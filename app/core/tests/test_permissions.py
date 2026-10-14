"""Kiểm thử kiểm quyền ở tầng máy chủ."""
import pytest

from core.constants import Rank
from core.exceptions import OutOfScopeError
from core.models import AuditLog
from core.permissions import assert_can_view, assert_rank, has_rank, is_admin
from core.tests.models import ScopeProbe

pytestmark = pytest.mark.django_db


def test_thu_tu_cap_bac_dung(nguoi_dung):
    """AC-3.6 — Cấp bậc so sánh theo thứ bậc, không theo thứ tự chữ cái"""
    assert has_rank(nguoi_dung["manager_sale"], Rank.LEADER)
    assert has_rank(nguoi_dung["leader_sale_1"], Rank.STAFF)
    assert not has_rank(nguoi_dung["staff_sale_1"], Rank.LEADER)
    assert not has_rank(nguoi_dung["leader_sale_1"], Rank.MANAGER)


def test_admin_co_tat_ca_cac_quyen(nguoi_dung):
    """AC-3.6 — Admin có tất cả các quyền, ở mọi cấp bậc"""
    admin = nguoi_dung["admin"]
    assert is_admin(admin)
    for muc in (Rank.STAFF, Rank.LEADER, Rank.MANAGER, Rank.ADMIN):
        assert has_rank(admin, muc)


def test_cap_bac_thap_hon_bi_tu_choi(nguoi_dung):
    """AC-3.6 — Cấp bậc thấp hơn mức yêu cầu thì bị từ chối, không trả rỗng"""
    with pytest.raises(OutOfScopeError):
        assert_rank(nguoi_dung["staff_sale_1"], Rank.MANAGER)


def test_xem_ban_ghi_ngoai_pham_vi_bi_tu_choi(nguoi_dung, probes):
    """AC-3.6 — Xem bản ghi ngoài phạm vi trả lỗi từ chối, không trả danh sách rỗng"""
    with pytest.raises(OutOfScopeError):
        assert_can_view(nguoi_dung["staff_sale_1"], probes["cua_mkt"])


def test_xem_ban_ghi_trong_pham_vi_thi_duoc(nguoi_dung, probes):
    """AC-3.6 — Bản ghi trong phạm vi thì vào được bình thường"""
    assert assert_can_view(nguoi_dung["staff_sale_1"], probes["cua_staff_1"]) is True


def test_moi_lan_tu_choi_deu_ghi_nhat_ky(nguoi_dung, probes):
    """AC-3.7 — Mỗi lần truy cập bị từ chối đều được ghi vào nhật ký"""
    truoc = AuditLog.objects.filter(action="denied").count()
    with pytest.raises(OutOfScopeError):
        assert_can_view(nguoi_dung["staff_sale_1"], probes["cua_vd"])
    assert AuditLog.objects.filter(action="denied").count() == truoc + 1


def test_goi_thang_duong_dan_van_bi_kiem_quyen(client, nguoi_dung):
    """AC-3.7 — Gọi thẳng đường dẫn không qua giao diện vẫn bị kiểm quyền"""
    tra_loi = client.get("/")
    assert tra_loi.status_code == 302
    assert "/dang-nhap/" in tra_loi.headers["Location"]


def test_dang_nhap_roi_thi_vao_duoc_tong_quan(client, nguoi_dung):
    """AC-3.7 — Người đã đăng nhập vào được màn hình trong phạm vi"""
    client.force_login(nguoi_dung["staff_sale_1"])
    assert client.get("/").status_code == 200


def test_khong_duoc_dung_objects_filter_de_vuot_pham_vi(nguoi_dung, probes):
    """AC-3.6 — Manager gọi in_scope vẫn không thấy bộ phận khác

    Kiểm chính cái manager, để nếu ai đó đổi cách lọc thì bài này gãy ngay.
    """
    qs = ScopeProbe.objects.in_scope(nguoi_dung["manager_sale"])
    assert probes["cua_mkt"] not in list(qs)
    assert probes["cua_staff_2"] in list(qs)


def test_assert_business_write_chan_giam_doc_va_ghi_nhat_ky(nguoi_dung, rf):
    """AC-3.7 — Giám đốc gọi thẳng đường ghi nghiệp vụ thì bị từ chối và có đúng một dòng Từ chối mang đường dẫn
    (FR-3.5, AC-44.6); tầng dịch vụ gọi không kèm request thì vẫn chặn nhưng không ghi, để view gọi lại tự ghi một lần
    (don_bo, xoá dòng lưới) — không ghi đôi; Manager và Kế toán đi qua không ghi gì (P0-2, TL-91)"""
    from core.constants import AuditAction
    from core.permissions import assert_business_write

    ceo = nguoi_dung["ceo"]
    tu_choi = AuditLog.objects.filter(action=AuditAction.DENIED, actor=ceo)
    with pytest.raises(OutOfScopeError):
        assert_business_write(ceo, rf.post("/bang/moi/"))
    assert tu_choi.count() == 1 and tu_choi.get().target_id == "/bang/moi/"
    with pytest.raises(OutOfScopeError):
        assert_business_write(ceo)
    assert tu_choi.count() == 1
    truoc = AuditLog.objects.count()
    for ai in ("manager_sale", "staff_kt"):
        assert_business_write(nguoi_dung[ai], rf.post("/bang/moi/"))
    assert AuditLog.objects.count() == truoc
