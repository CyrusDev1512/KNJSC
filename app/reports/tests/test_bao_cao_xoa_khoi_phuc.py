"""Xoá và khôi phục báo cáo của cấp dưới — ADR-041, chủ dự án chốt 24.09.2026.

Bỏ báo cáo: người nộp (như cũ), Leader trong team, Manager trong bộ phận, Admin;
Kế toán KHÔNG (giữ đúng ADR-038 — Kế toán sửa số, không quyết bỏ). Bỏ là xoá mềm
cả `DailyReport` lẫn dòng số liệu (BR-4) nên số rời khỏi Báo cáo tổng hợp.
Khôi phục: Manager bộ phận mình và Admin, từ trang "Đã bỏ".
"""
import pytest

from core.constants import AuditAction
from core.exceptions import OutOfScopeError
from core.models import AuditLog
from forms_builder.models import DataRecord
from reports.models import DailyReport
from reports.services import daily_service

from .test_bao_cao_ngay import bm_mkt, bm_sale, _nop  # noqa: F401

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("ai,duoc", [
    ("staff_sale_1", True),      # người nộp — hành vi cũ giữ nguyên
    ("staff_sale_1b", False),    # cùng team nhưng không nộp, không quản lý
    ("staff_sale_2", False),     # khác team
    ("leader_sale_1", True),     # Leader đúng team
    ("leader_sale_2", False),    # Leader team khác
    ("manager_sale", True),      # Manager đúng bộ phận
    ("manager_mkt", False),      # Manager bộ phận khác
    ("staff_kt", False),         # Kế toán: sửa được nhưng KHÔNG bỏ (ADR-038)
    ("admin", True),
])
def test_quyen_bo_bao_cao_hai_chieu(client, bm_sale, nguoi_dung, ai, duoc):  # noqa: F811
    """AC-4.9 — Bỏ báo cáo cấp dưới: người nộp, Leader trong team, Manager trong bộ
    phận, Admin được; nhân viên khác, Leader team khác, Manager bộ phận khác và Kế
    toán bị 403 có nhật ký, báo cáo còn nguyên"""
    bc = _nop(bm_sale, nguoi_dung["staff_sale_1"])
    nguoi = nguoi_dung[ai]
    assert daily_service.can_withdraw(nguoi, bc) is duoc
    client.force_login(nguoi)
    truoc = AuditLog.objects.filter(action=AuditAction.DENIED).count()
    kq = client.post(f"/bao-cao/{bc.pk}/bo/")
    if duoc:
        assert kq.status_code == 302
        assert not DailyReport.objects.filter(pk=bc.pk).exists()
        assert AuditLog.objects.filter(action=AuditAction.DELETE,
                                       detail__startswith="Bỏ báo cáo").exists()
    else:
        # Kế toán và quản lý sai phạm vi vẫn THẤY báo cáo (403 + nhật ký);
        # người ngoài phạm vi xem thì 404 như cũ
        assert kq.status_code in (403, 404)
        if kq.status_code == 403:
            assert AuditLog.objects.filter(action=AuditAction.DENIED).count() == truoc + 1
        assert DailyReport.objects.filter(pk=bc.pk).exists()


def test_bo_la_xoa_mem_ca_dong_so_lieu_va_roi_khoi_tong_hop(client, bm_sale, nguoi_dung):  # noqa: F811
    """AC-4.9 — Manager bỏ báo cáo của Staff: báo cáo biến khỏi Lịch sử, dòng số
    liệu xoá mềm (BR-4, còn nguyên nội dung trong DB) nên Báo cáo tổng hợp — vốn
    chỉ đọc dòng sống — không còn đếm; service gọi thẳng bởi người không quyền bị
    `OutOfScopeError` (kiểm trong giao dịch, không tin view)"""
    bc = _nop(bm_sale, nguoi_dung["staff_sale_1"])
    dong = bc.record
    with pytest.raises(OutOfScopeError):
        daily_service.withdraw(bc, actor=nguoi_dung["staff_kt"])
    daily_service.withdraw(bc, actor=nguoi_dung["manager_sale"])

    assert not daily_service.history(nguoi_dung["manager_sale"]).filter(pk=bc.pk).exists()
    assert not DataRecord.objects.filter(pk=dong.pk).exists()          # tổng hợp hết đếm
    con = DataRecord.all_objects.get(pk=dong.pk)
    assert con.deleted_at is not None and con.data["so_mess"] == 1000  # không mất nội dung
    # Bấm đúp / hai tab: lần hai không nổ, không ghi thêm nhật ký DELETE
    so_nk = AuditLog.objects.filter(action=AuditAction.DELETE).count()
    daily_service.withdraw(bc, actor=nguoi_dung["manager_sale"])
    assert AuditLog.objects.filter(action=AuditAction.DELETE).count() == so_nk


@pytest.mark.parametrize("ai,duoc", [
    ("staff_sale_1", False),     # người nộp cũng không tự khôi phục
    ("leader_sale_1", False),    # Leader bỏ được nhưng khôi phục là việc của Manager
    ("manager_sale", True),
    ("manager_mkt", False),      # Manager bộ phận khác
    ("staff_kt", False),         # Kế toán
    ("admin", True),
])
def test_quyen_khoi_phuc_hai_chieu(client, bm_sale, nguoi_dung, ai, duoc):  # noqa: F811
    """AC-4.10 — Khôi phục báo cáo đã bỏ: Manager bộ phận mình và Admin được;
    Staff, Leader, Kế toán và Manager bộ phận khác bị từ chối có nhật ký"""
    bc = _nop(bm_sale, nguoi_dung["staff_sale_1"])
    daily_service.withdraw(bc, actor=nguoi_dung["manager_sale"])
    nguoi = nguoi_dung[ai]
    client.force_login(nguoi)
    kq = client.post(f"/bao-cao/{bc.pk}/khoi-phuc/")
    if duoc:
        assert kq.status_code == 302
        assert DailyReport.objects.filter(pk=bc.pk).exists()
    else:
        assert kq.status_code in (403, 404)
        assert not DailyReport.objects.filter(pk=bc.pk).exists()


def test_khoi_phuc_tra_bao_cao_va_so_lieu_ve_nguyen(client, bm_sale, nguoi_dung):  # noqa: F811
    """AC-4.10 — Khôi phục trả cả báo cáo lẫn dòng số liệu về trạng thái sống:
    Lịch sử thấy lại, dòng sống lại với nội dung nguyên vẹn, có nhật ký UPDATE;
    khôi phục lần hai không nổ"""
    bc = _nop(bm_sale, nguoi_dung["staff_sale_1"])
    dong = bc.record
    daily_service.withdraw(bc, actor=nguoi_dung["manager_sale"])
    daily_service.restore(bc, actor=nguoi_dung["manager_sale"])

    assert daily_service.history(nguoi_dung["staff_sale_1"]).filter(pk=bc.pk).exists()
    dong.refresh_from_db()
    assert dong.deleted_at is None and dong.data["so_mess"] == 1000
    assert AuditLog.objects.filter(action=AuditAction.UPDATE,
                                   detail__startswith="Khôi phục báo cáo").exists()
    daily_service.restore(bc, actor=nguoi_dung["manager_sale"])       # lần hai: bỏ qua êm


def test_trang_da_bo_theo_pham_vi_va_nut_hien_dung(client, bm_sale, bm_mkt, nguoi_dung):  # noqa: F811
    """AC-4.10 — Trang "Đã bỏ": Manager chỉ thấy báo cáo đã bỏ của bộ phận mình,
    Admin thấy hết; Staff/Leader/Kế toán gọi thẳng bị 403 có nhật ký; liên kết
    "Đã bỏ" trên Lịch sử chỉ hiện với người có quyền"""
    bc_sale = _nop(bm_sale, nguoi_dung["staff_sale_1"])
    bc_mkt = _nop(bm_mkt, nguoi_dung["staff_mkt"])
    daily_service.withdraw(bc_sale, actor=nguoi_dung["manager_sale"])
    daily_service.withdraw(bc_mkt, actor=nguoi_dung["manager_mkt"])

    client.force_login(nguoi_dung["manager_sale"])
    kq = client.get("/bao-cao/da-bo/")
    thay = [b.pk for b in kq.context["trang"]]
    assert bc_sale.pk in thay and bc_mkt.pk not in thay
    assert "Đã bỏ" in client.get("/bao-cao/lich-su/").content.decode()

    client.force_login(nguoi_dung["admin"])
    thay = [b.pk for b in client.get("/bao-cao/da-bo/").context["trang"]]
    assert bc_sale.pk in thay and bc_mkt.pk in thay

    for ai in ("staff_sale_1", "leader_sale_1", "staff_kt"):
        client.force_login(nguoi_dung[ai])
        truoc = AuditLog.objects.filter(action=AuditAction.DENIED).count()
        assert client.get("/bao-cao/da-bo/").status_code == 403, ai
        assert AuditLog.objects.filter(action=AuditAction.DENIED).count() == truoc + 1
        assert "Đã bỏ" not in client.get("/bao-cao/lich-su/").content.decode().split("sp-history-title")[1][:300]
