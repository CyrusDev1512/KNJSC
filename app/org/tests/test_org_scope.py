"""Kiểm thử phạm vi quyền trên module org.

Kiểm cả hai chiều: ai xem được ai, và ai không xem được ai.
"""
import pytest

from core.constants import Rank
from core.models import AuditLog
from org.models import UserProfile

pytestmark = pytest.mark.django_db


def ten(qs):
    return set(qs.values_list("user__username", flat=True))


# ══ Phạm vi trên danh sách nhân sự ═════════════════════════════

def test_staff_chi_thay_ho_so_cua_chinh_minh(nguoi_dung):
    """AC-3.1 — Staff chỉ thấy hồ sơ của chính mình trong danh sách nhân sự"""
    thay = ten(UserProfile.objects.in_scope(nguoi_dung["staff_sale_1"]))
    assert thay == {"staff_sale_1"}


def test_leader_thay_thanh_vien_team_minh(nguoi_dung, teams):
    """AC-3.2 — Leader thấy hồ sơ của người trong team mình phụ trách"""
    thay = ten(UserProfile.objects.in_scope(nguoi_dung["leader_sale_1"]))
    assert "staff_sale_1" in thay
    assert "staff_sale_1b" in thay


def test_leader_khong_thay_team_khac(nguoi_dung):
    """AC-3.3 — Leader không thấy hồ sơ của team khác cùng bộ phận"""
    thay = ten(UserProfile.objects.in_scope(nguoi_dung["leader_sale_1"]))
    assert "staff_sale_2" not in thay


def test_manager_thay_toan_bo_bo_phan(nguoi_dung):
    """AC-3.4 — Manager thấy hồ sơ của toàn bộ bộ phận mình"""
    thay = ten(UserProfile.objects.in_scope(nguoi_dung["manager_sale"]))
    assert {"staff_sale_1", "staff_sale_2", "leader_sale_1"} <= thay


def test_manager_khong_thay_bo_phan_khac(nguoi_dung):
    """AC-3.5 — Manager không thấy hồ sơ của bộ phận khác"""
    thay = ten(UserProfile.objects.in_scope(nguoi_dung["manager_sale"]))
    assert "staff_mkt" not in thay
    assert "staff_vd" not in thay


def test_admin_thay_tat_ca(nguoi_dung):
    """AC-3.8 — Admin thấy toàn bộ hồ sơ ở mọi bộ phận"""
    thay = ten(UserProfile.objects.in_scope(nguoi_dung["admin"]))
    assert len(thay) == UserProfile.objects.count()


# ══ Chặn ở tầng màn hình ═══════════════════════════════════════

def test_staff_khong_vao_duoc_man_hinh_nhan_su(client, nguoi_dung):
    """AC-3.6 — Staff mở màn hình nhân sự thì bị từ chối, không thấy danh sách rỗng"""
    client.force_login(nguoi_dung["staff_sale_1"])
    tra_loi = client.get("/nhan-su/")
    assert tra_loi.status_code == 403


def test_leader_vao_duoc_man_hinh_nhan_su(client, nguoi_dung):
    """AC-3.6 — Leader trở lên vào được màn hình nhân sự"""
    client.force_login(nguoi_dung["leader_sale_1"])
    assert client.get("/nhan-su/").status_code == 200


def test_chi_admin_tao_duoc_tai_khoan(client, nguoi_dung):
    """AC-3.6 — Chỉ quản trị viên mới tạo được tài khoản"""
    client.force_login(nguoi_dung["manager_sale"])
    assert client.get("/nhan-su/moi/").status_code == 403
    client.force_login(nguoi_dung["admin"])
    assert client.get("/nhan-su/moi/").status_code == 200


def test_chi_admin_vao_duoc_bo_phan(client, nguoi_dung):
    """AC-3.6 — Màn hình bộ phận và team chỉ dành cho quản trị viên"""
    client.force_login(nguoi_dung["manager_sale"])
    assert client.get("/bo-phan/").status_code == 403
    client.force_login(nguoi_dung["admin"])
    assert client.get("/bo-phan/").status_code == 200


def test_manager_chi_thay_nhat_ky_trong_pham_vi(client, nguoi_dung):
    """AC-3.5 — Manager chỉ thấy nhật ký của người trong bộ phận mình"""
    from core import audit
    from core.constants import AuditAction

    audit.record(AuditAction.LOGIN, actor=nguoi_dung["staff_sale_1"])
    audit.record(AuditAction.LOGIN, actor=nguoi_dung["staff_mkt"])

    thay = AuditLog.objects.in_scope(nguoi_dung["manager_sale"])
    nhan = set(thay.values_list("actor__username", flat=True))
    assert "staff_sale_1" in nhan
    assert "staff_mkt" not in nhan


def test_staff_khong_vao_duoc_nhat_ky(client, nguoi_dung):
    """AC-3.6 — Nhật ký chỉ dành cho Manager trở lên"""
    client.force_login(nguoi_dung["staff_sale_1"])
    assert client.get("/nhat-ky/").status_code == 403


# ══ Gán người vào bộ phận và team ══════════════════════════════

def test_khong_gan_duoc_team_sai_bo_phan(nguoi_dung, teams, departments):
    """AC-2.3 — Không gán được người vào team thuộc bộ phận khác"""
    from core.exceptions import BusinessError
    from org.services import org_service

    with pytest.raises(BusinessError):
        org_service.assign_member(
            nguoi_dung["staff_mkt"].profile,
            department=departments["mkt"], team=teams["sale1"],
        )


def test_gan_nguoi_vao_team_lam_mat_phien(client, nguoi_dung, teams, departments):
    """AC-2.3 — Chuyển team làm phiên đang mở mất hiệu lực ngay"""
    from org.services import org_service

    client.post("/dang-nhap/", {
        "username": "staff_sale_1", "password": "matkhau-kiem-thu-1",
    })
    assert client.get("/").status_code == 200

    org_service.assign_member(
        nguoi_dung["staff_sale_1"].profile,
        department=departments["sale"], team=teams["sale2"],
    )
    assert client.get("/").status_code == 302


# ══ Thanh điều hướng ═══════════════════════════════════════════

def test_thanh_dieu_huong_an_muc_ngoai_quyen(nguoi_dung):
    """AC-3.6 — Thanh điều hướng chỉ hiện mục người dùng có quyền vào"""
    from core.navigation import visible_navigation

    def cac_ma(user):
        return {m.code for nhom in visible_navigation(user) for m in nhom["items"]}

    # Staff chỉ vào được hai mục không đòi cấp bậc
    assert cac_ma(nguoi_dung["staff_sale_1"]) == {"tong_quan", "bang"}
    assert "nhan_su" not in cac_ma(nguoi_dung["staff_sale_1"])
    assert "nhan_su" in cac_ma(nguoi_dung["leader_sale_1"])
    assert "nhat_ky" in cac_ma(nguoi_dung["manager_sale"])
    assert "ma_tran_quyen" in cac_ma(nguoi_dung["manager_sale"])
    assert "ma_tran_quyen" not in cac_ma(nguoi_dung["leader_sale_1"])
    assert "bo_phan" not in cac_ma(nguoi_dung["manager_sale"])
    assert "bo_phan" in cac_ma(nguoi_dung["admin"])


# ══ Tổng quan chịu lỗi ═════════════════════════════════════════

def test_tong_quan_van_chay_khi_mot_khoi_loi(nguoi_dung):
    """kien-truc.md, mục chịu lỗi — Một khối lỗi thì các khối còn lại vẫn hiện"""
    from dashboard.services import dashboard_service

    kq = dashboard_service.tong_quan(nguoi_dung["manager_sale"])
    assert kq["bang_dong"]["ok"] is False      # khối này cố tình lỗi
    assert kq["nhan_su"]["ok"] is True         # các khối khác vẫn chạy
    assert kq["co_cau"]["ok"] is True
    assert kq["hoat_dong"]["ok"] is True


def test_tong_quan_vao_duoc_voi_moi_cap_bac(client, nguoi_dung):
    """AC-3.6 — Mọi cấp bậc đều vào được Tổng quan"""
    for khoa in ("staff_sale_1", "leader_sale_1", "manager_sale", "admin"):
        client.force_login(nguoi_dung[khoa])
        assert client.get("/").status_code == 200, khoa
