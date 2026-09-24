"""Ma trận phân quyền đầy đủ cho luồng báo cáo ngày — bổ sung ADR-041 (24.09.2026).

Mỗi hàm `can_amend` / `can_withdraw` / `can_restore` đã có bài kiểm riêng, nhưng
chưa có MỘT chỗ nhìn thấy cả bốn hành động (xem × sửa × bỏ × khôi phục) cạnh nhau
cho từng vai — sửa một hàm mà quên hàm kia là ma trận lệch không ai thấy. Tệp này
khoá ma trận đó, kèm bốn persona chưa có trong fixture chung: tài khoản khoá,
tài khoản không hồ sơ nhân sự, nhân sự CSKH, Leader không dẫn team nào.

Không lặp lại các tổ hợp `test_bao_cao_xoa_khoi_phuc.py` và
`test_report_amendments.py` đã phủ — chỉ thêm ô còn trống.
"""
import pytest

from core.constants import AuditAction, Rank
from core.exceptions import NoProfileError
from core.models import AuditLog
from reports.models import DailyReport
from reports.services import daily_service

from .test_bao_cao_ngay import bm_mkt, bm_sale, _nop  # noqa: F401

pytestmark = pytest.mark.django_db


@pytest.fixture
def bo_phan_cskh(db):
    """CSKH chưa có trong conftest chung — với luồng báo cáo nó là 'bộ phận khác'."""
    from org.models import Department

    return Department.objects.get_or_create(code="cskh", defaults={"name": "CSKH"})[0]


@pytest.fixture
def nguoi_dung_mo_rong(nguoi_dung, departments, make_user, bo_phan_cskh):
    """Fixture chung cộng ba persona còn thiếu của ma trận."""
    them = dict(nguoi_dung)
    them["staff_cskh"] = make_user("staff_cskh", Rank.STAFF, bo_phan_cskh)
    them["manager_cskh"] = make_user("manager_cskh", Rank.MANAGER, bo_phan_cskh)
    # Leader theo hồ sơ nhưng không là Team.leader của team nào → scope_team_ids rỗng
    them["leader_khong_team"] = make_user(
        "leader_khong_team", Rank.LEADER, departments["sale"])
    return them


# Ma trận trên báo cáo của staff_sale_1 (bộ phận Sale, team Sale 1):
# (vai, sửa được, bỏ được, khôi phục được)
MA_TRAN = [
    ("staff_sale_1", False, True, False),       # người nộp: chỉ bỏ, không sửa/khôi phục
    ("staff_sale_1b", False, False, False),     # cùng team, không nộp
    ("staff_sale_2", False, False, False),      # khác team
    ("leader_sale_1", True, True, False),       # Leader đúng team; khôi phục nhờ Manager
    ("leader_sale_2", False, False, False),     # Leader team khác
    ("leader_khong_team", False, False, False), # Leader không dẫn team nào
    ("manager_sale", True, True, True),         # Manager đúng bộ phận: đủ cả ba
    ("manager_mkt", False, False, False),       # Manager bộ phận khác
    ("manager_cskh", False, False, False),      # Manager CSKH — bộ phận khác
    ("staff_cskh", False, False, False),
    ("staff_vd", False, False, False),
    ("staff_kt", True, False, False),           # Kế toán: sửa mọi báo cáo, không bỏ/khôi phục
    ("admin", True, True, True),
]


@pytest.mark.parametrize("vai,sua,bo,khoi_phuc", MA_TRAN)
def test_ma_tran_bon_hanh_dong_theo_vai(bm_sale, nguoi_dung_mo_rong, vai, sua, bo, khoi_phuc):  # noqa: F811
    """AC-4.4, AC-4.9, AC-4.10 — Ma trận sửa × bỏ × khôi phục cho 13 vai trên cùng
    một báo cáo: ba hàm quyền phải khớp nhau từng ô, kể cả Leader không dẫn team
    và Manager/Staff CSKH (bộ phận ngoài cuộc)"""
    bc = _nop(bm_sale, nguoi_dung_mo_rong["staff_sale_1"])
    nguoi = nguoi_dung_mo_rong[vai]
    assert daily_service.can_amend(nguoi, bc) is sua
    assert daily_service.can_withdraw(nguoi, bc) is bo
    assert daily_service.can_restore(nguoi, bc) is khoi_phuc


def test_tai_khoan_khoa_mat_het_quyen(bm_sale, nguoi_dung):  # noqa: F811
    """AC-4.4, AC-4.9, AC-4.10 — Tài khoản khoá (`is_active=False`) mất cả ba quyền
    dù cấp bậc là gì, kể cả Admin và Kế toán; người nộp bị khoá cũng không tự bỏ
    được báo cáo của mình (chặn đứng trước nhánh người-nộp)"""
    bc = _nop(bm_sale, nguoi_dung["staff_sale_1"])
    for vai in ("leader_sale_1", "manager_sale", "staff_kt", "admin", "staff_sale_1"):
        nguoi = nguoi_dung[vai]
        nguoi.is_active = False
        nguoi.save(update_fields=["is_active"])
        assert daily_service.can_amend(nguoi, bc) is False, vai
        assert daily_service.can_withdraw(nguoi, bc) is False, vai
        assert daily_service.can_restore(nguoi, bc) is False, vai


def test_tai_khoan_khoa_bi_day_ve_dang_nhap(client, bm_sale, nguoi_dung):  # noqa: F811
    """AC-4.9 — Tài khoản khoá bị chặn ngay từ tầng phiên: khoá giữa chừng thì
    phiên đang đăng nhập mất hiệu lực (ModelBackend không trả user khoá), POST bỏ
    bị đẩy về trang đăng nhập, báo cáo còn nguyên — service phía sau còn thêm lớp
    `is_active` phòng khi backend khác cho qua (bài service ở trên)"""
    bc = _nop(bm_sale, nguoi_dung["staff_sale_1"])
    ld = nguoi_dung["leader_sale_1"]
    client.force_login(ld)
    ld.is_active = False
    ld.save(update_fields=["is_active"])
    kq = client.post(f"/bao-cao/{bc.pk}/bo/")
    assert kq.status_code == 302 and kq.url.startswith("/dang-nhap/")
    assert DailyReport.objects.filter(pk=bc.pk).exists()


def test_ke_toan_het_hieu_luc_khi_bo_phan_xoa_mem(client, bm_sale, departments, nguoi_dung, User):  # noqa: F811
    """AC-4.8 — Ngoại lệ Kế toán bám theo bộ phận còn sống: xoá mềm bộ phận Kế toán
    thì `is_accountant` tắt — hết quyền sửa và hết thấy báo cáo bộ phận khác (404),
    người đó rơi về Staff thường"""
    bc = _nop(bm_sale, nguoi_dung["staff_sale_1"])
    assert daily_service.can_amend(nguoi_dung["staff_kt"], bc) is True
    departments["kt"].delete(by=nguoi_dung["admin"])
    # Lấy lại user mới để bỏ đệm scope và hồ sơ đã nạp trên đối tượng cũ
    kt = User.objects.get(pk=nguoi_dung["staff_kt"].pk)
    assert daily_service.can_amend(kt, bc) is False
    client.force_login(kt)
    assert client.get(f"/bao-cao/{bc.pk}/").status_code == 404
    assert client.get(f"/bao-cao/{bc.pk}/sua/").status_code == 404


def test_khong_ho_so_bi_permission_denied_khong_500(client, bm_sale, nguoi_dung, User):  # noqa: F811
    """AC-3.6 — Tài khoản không có hồ sơ nhân sự: ba hàm quyền ném `NoProfileError`
    (một dạng PermissionDenied) với báo cáo người khác, và mọi đường dẫn báo cáo
    trả 403 chứ không 500"""
    bc = _nop(bm_sale, nguoi_dung["staff_sale_1"])
    mo_coi = User.objects.create_user("khong_ho_so", password="matkhau-kiem-thu-1")
    for ham in (daily_service.can_amend, daily_service.can_withdraw, daily_service.can_restore):
        with pytest.raises(NoProfileError):
            ham(mo_coi, bc)
    client.force_login(mo_coi)
    for url in ("/bao-cao/lich-su/", f"/bao-cao/{bc.pk}/",
                f"/bao-cao/{bc.pk}/sua/", "/bao-cao/da-bo/"):
        assert client.get(url).status_code == 403, url
    assert client.post(f"/bao-cao/{bc.pk}/bo/").status_code == 403
    assert client.post(f"/bao-cao/{bc.pk}/khoi-phuc/").status_code == 403
    assert DailyReport.objects.filter(pk=bc.pk).exists()


def test_nguoi_nop_mat_ho_so_van_giu_nhanh_nguoi_nop(bm_sale, nguoi_dung, User):  # noqa: F811
    """AC-4.9 — Ghi nhận hành vi hiện có: hồ sơ bị gỡ SAU khi nộp thì nhánh
    người-nộp của `can_withdraw` vẫn trả True (đứng trước kiểm scope), còn
    `can_restore` ném NoProfileError; qua HTTP người này vẫn bị 403 từ tầng xem
    nên không có đường bỏ thật — chốt lại để đổi hành vi là đổi có chủ đích"""
    bc = _nop(bm_sale, nguoi_dung["staff_sale_1"])
    nguoi_dung["staff_sale_1"].profile.delete()
    chu = User.objects.get(pk=nguoi_dung["staff_sale_1"].pk)
    assert daily_service.can_withdraw(chu, bc) is True
    with pytest.raises(NoProfileError):
        daily_service.can_restore(chu, bc)


@pytest.mark.parametrize("vai", ["staff_cskh", "leader_khong_team"])
def test_ngoai_pham_vi_xem_404_moi_duong_dan(client, bm_sale, nguoi_dung_mo_rong, vai):  # noqa: F811
    """AC-4.4, AC-4.9, AC-4.10 — Người ngoài phạm vi xem (Staff CSKH, Leader không
    dẫn team) bị 404 ở xem/sửa/bỏ — không lộ báo cáo tồn tại (quy tắc 8); trang
    "Đã bỏ" trả 403 có nhật ký vì không phải Manager/Admin"""
    bc = _nop(bm_sale, nguoi_dung_mo_rong["staff_sale_1"])
    client.force_login(nguoi_dung_mo_rong[vai])
    assert client.get(f"/bao-cao/{bc.pk}/").status_code == 404
    assert client.get(f"/bao-cao/{bc.pk}/sua/").status_code == 404
    assert client.post(f"/bao-cao/{bc.pk}/bo/").status_code == 404
    assert DailyReport.objects.filter(pk=bc.pk).exists()
    truoc = AuditLog.objects.filter(action=AuditAction.DENIED).count()
    assert client.get("/bao-cao/da-bo/").status_code == 403
    assert AuditLog.objects.filter(action=AuditAction.DENIED).count() == truoc + 1


def test_manager_bo_phan_khac_trang_da_bo_rong_va_khong_khoi_phuc_cheo(client, bm_sale, nguoi_dung_mo_rong):  # noqa: F811
    """AC-4.10 — Manager bộ phận khác vẫn vào được trang "Đã bỏ" (cổng theo cấp
    bậc) nhưng danh sách tự thu hẹp theo phạm vi nên rỗng; khôi phục chéo bộ phận
    bị 404 và báo cáo vẫn ở trạng thái đã bỏ"""
    bc = _nop(bm_sale, nguoi_dung_mo_rong["staff_sale_1"])
    daily_service.withdraw(bc, actor=nguoi_dung_mo_rong["manager_sale"])
    client.force_login(nguoi_dung_mo_rong["manager_cskh"])
    kq = client.get("/bao-cao/da-bo/")
    assert kq.status_code == 200
    assert list(kq.context["trang"]) == []
    assert client.post(f"/bao-cao/{bc.pk}/khoi-phuc/").status_code == 404
    assert not DailyReport.objects.filter(pk=bc.pk).exists()
