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

def test_thanh_dieu_huong_an_muc_ngoai_quyen(nguoi_dung, departments):
    """AC-3.6 — Thanh điều hướng chỉ hiện mục người dùng có quyền vào"""
    from core.navigation import visible_navigation
    from forms_builder.models import FormDef, TableDef

    # "Nộp báo cáo ngày" chỉ hiện khi bộ phận có biểu mẫu báo cáo ngày (chủ dự án 13–14.10, P0-2)
    bang = TableDef.objects.create(name="Bảng Sale", code="bang_menu_sale", department=departments["sale"])
    FormDef.objects.create(name="Báo cáo Sale", code="bc_menu_sale", table=bang, department=departments["sale"])

    def cac_ma(user):
        return {m["code"] for nhom in visible_navigation(user) for m in nhom["items"]}

    # Staff thấy đúng những mục không đòi cấp bậc — suy ra từ chính NAVIGATION
    # thay vì chép tay, để thêm màn hình mới không phải sửa bài kiểm thử này.
    # Vẫn bắt được rò rỉ: mục nào đòi cấp bậc mà Staff thấy được là đỏ ngay.
    from core.constants import Rank
    from core.navigation import NAVIGATION

    # Mục giới hạn bộ phận (Lên đơn của Sale, Bảng tính của Vận đơn) chỉ tính
    # khi bộ phận khớp — Staff Sale không được thấy Bảng tính
    khong_doi_cap_bac = {
        m.code for nhom in NAVIGATION for m in nhom.items
        if m.min_rank == Rank.STAFF and (m.departments is None or "sale" in m.departments)
    }
    assert cac_ma(nguoi_dung["staff_sale_1"]) == khong_doi_cap_bac
    assert "nhan_su" not in cac_ma(nguoi_dung["staff_sale_1"])
    assert "nhan_su" in cac_ma(nguoi_dung["leader_sale_1"])
    assert "nhat_ky" not in cac_ma(nguoi_dung["manager_sale"])
    assert "ma_tran_quyen" not in cac_ma(nguoi_dung["manager_sale"])
    assert {"nhat_ky", "ma_tran_quyen"} <= cac_ma(nguoi_dung["admin"])
    assert "ma_tran_quyen" not in cac_ma(nguoi_dung["leader_sale_1"])
    assert "bo_phan" not in cac_ma(nguoi_dung["manager_sale"])
    assert "bo_phan" in cac_ma(nguoi_dung["admin"])


# ══ Tổng quan chịu lỗi ═════════════════════════════════════════

def test_tong_quan_van_chay_khi_mot_khoi_loi(nguoi_dung):
    """kien-truc.md, mục chịu lỗi — Một khối lỗi thì các khối còn lại vẫn hiện

    Giả lập khối bảng động hỏng. Trước đây khối này **cố tình** hỏng thật vì
    module forms_builder chưa có; nay nó chạy được, nên phải giả lập — không
    thì tính chất chịu lỗi mất người canh.
    """
    from unittest import mock

    from dashboard.services import dashboard_service

    with mock.patch.object(
        dashboard_service, "_bang_dong", side_effect=RuntimeError("hỏng giả lập")
    ):
        kq = dashboard_service.tong_quan(nguoi_dung["manager_sale"])

    assert kq["bang_dong"]["ok"] is False      # khối hỏng
    assert kq["nhan_su"]["ok"] is True         # các khối khác vẫn chạy
    assert kq["co_cau"]["ok"] is True
    assert kq["hoat_dong"]["ok"] is True


def test_tong_quan_hien_bang_dong_khi_binh_thuong(nguoi_dung, departments):
    """kien-truc.md — Khối bảng động chạy thật, không còn báo chưa khả dụng"""
    from dashboard.services import dashboard_service
    from forms_builder.models import TableDef

    TableDef.objects.create(
        name="Bảng thử", code="bang_thu_tq",
        department=departments["sale"], created_by=nguoi_dung["manager_sale"],
    )
    kq = dashboard_service.tong_quan(nguoi_dung["manager_sale"])

    assert kq["bang_dong"]["ok"] is True
    assert kq["bang_dong"]["data"]["so_bang"] == 1


def test_tong_quan_vao_duoc_voi_moi_cap_bac(client, nguoi_dung):
    """AC-3.6 — Mọi cấp bậc đều vào được Tổng quan"""
    for khoa in ("staff_sale_1", "leader_sale_1", "manager_sale", "admin"):
        client.force_login(nguoi_dung[khoa])
        assert client.get("/").status_code == 200, khoa


# ══ Trưởng nhóm cùng bộ phận, hồ sơ phải có bộ phận — TL-95, TL-96 · P0-9 ═══

def test_tao_team_tu_choi_truong_nhom_khac_bo_phan(client, nguoi_dung, departments, make_user):
    """AC-2.2 — Tạo team: trưởng nhóm phải cùng bộ phận với team, chọn Leader bộ phận khác thì báo lỗi dưới ô Trưởng
    nhóm và không tạo; chọn Leader đúng bộ phận thì tạo được (TL-95)"""
    from org.forms import TeamForm
    from org.models import Team

    leader_mkt = make_user("leader_mkt_x", Rank.LEADER, departments["mkt"])
    client.force_login(nguoi_dung["admin"])
    goi = {"tm-name": "Sale 9", "tm-department": departments["sale"].pk, "tm-leader": leader_mkt.pk,
           "tm-is_active": "on", "tao_team": "1"}
    r = client.post("/bo-phan/", goi)
    assert r.status_code == 200 and "không thuộc" in r.content.decode()
    assert not Team.objects.filter(name="Sale 9").exists()
    form = TeamForm({k.removeprefix("tm-"): v for k, v in goi.items() if k.startswith("tm-")})
    assert not form.is_valid() and "leader" in form.errors

    r = client.post("/bo-phan/", {**goi, "tm-leader": nguoi_dung["leader_sale_1"].pk})
    assert r.status_code == 302
    assert Team.objects.get(name="Sale 9").leader == nguoi_dung["leader_sale_1"]


def test_leader_khac_bo_phan_lam_truong_team_khong_quan_ly_duoc_staff(client, nguoi_dung, teams, departments, make_user):
    """AC-3.3 — Leader bộ phận khác lỡ là trưởng một team (dữ liệu cũ, trang quản trị) không có phạm vi trên team đó:
    không thấy, không mở hồ sơ, không đặt lại mật khẩu, không xoá người của team; Leader đúng bộ phận vẫn làm được
    (TL-95 — trước đây đặt lại được mật khẩu, xoá được)"""
    from django.contrib.auth import get_user_model

    from org.models import Team
    from org.services.account_management import AccountPolicy

    leader_mkt = make_user("leader_mkt_x", Rank.LEADER, departments["mkt"])
    Team.objects.filter(pk=teams["sale2"].pk).update(leader=leader_mkt)
    nan_nhan = nguoi_dung["staff_sale_2"]
    doc_lai = get_user_model().objects.get(pk=leader_mkt.pk)
    assert "staff_sale_2" not in ten(UserProfile.objects.in_scope(doc_lai))
    assert not AccountPolicy(doc_lai).can_manage(nan_nhan.profile)

    hash_cu = nan_nhan.password
    mat_khau = {"new_password1": "MatKhauMoi-2026!", "new_password2": "MatKhauMoi-2026!"}
    client.force_login(leader_mkt)
    assert client.get(f"/nhan-su/{nan_nhan.profile.pk}/sua/").status_code == 403
    assert client.post(f"/nhan-su/{nan_nhan.profile.pk}/dat-lai-mat-khau/", mat_khau).status_code == 403
    assert client.post(f"/nhan-su/{nan_nhan.profile.pk}/xoa/", {"confirm": "yes"}).status_code == 403
    nan_nhan.refresh_from_db()
    nan_nhan.profile.refresh_from_db()
    assert nan_nhan.password == hash_cu and nan_nhan.profile.deleted_at is None

    client.force_login(nguoi_dung["leader_sale_1"])
    assert client.post(f"/nhan-su/{nguoi_dung['staff_sale_1'].profile.pk}/dat-lai-mat-khau/", mat_khau).status_code == 302


def test_sua_ho_so_bat_buoc_bo_phan_tru_admin_va_ceo(client, nguoi_dung, departments):
    """AC-2.3 — Sửa hồ sơ bắt buộc chọn bộ phận như Tạo tài khoản: Staff, Leader, Manager để trống bộ phận thì không
    lưu; Giám đốc và Quản trị viên không bắt buộc (ADR-044, TL-96)"""
    from org.forms import SuaHoSoForm

    ql = nguoi_dung["manager_sale"].profile
    for cap in (Rank.STAFF, Rank.LEADER, Rank.MANAGER):
        assert not SuaHoSoForm({"full_name": "X", "rank": cap, "department": ""}, instance=ql).is_valid(), cap
    for cap in (Rank.CEO, Rank.ADMIN):
        assert SuaHoSoForm({"full_name": "X", "rank": cap, "department": ""}, instance=ql).is_valid(), cap
    client.force_login(nguoi_dung["admin"])
    r = client.post(f"/nhan-su/{ql.pk}/sua/", {"full_name": ql.full_name, "rank": Rank.MANAGER, "department": ""})
    assert r.status_code == 200
    ql.refresh_from_db()
    assert ql.department == departments["sale"]
