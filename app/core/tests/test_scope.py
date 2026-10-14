"""Kiểm thử phạm vi quyền.

Mỗi tiêu chí kiểm cả hai chiều: trường hợp được phép và trường hợp bị từ
chối. Chỉ kiểm chiều được phép thì không phát hiện được rò rỉ dữ liệu.
"""
import pytest

from core.constants import Rank
from core.exceptions import NoProfileError
from core.scope import get_user_scope
from core.tests.models import ScopeProbe

pytestmark = pytest.mark.django_db


def tieu_de(qs):
    return set(qs.values_list("title", flat=True))


def test_staff_chi_xem_duoc_du_lieu_cua_minh(nguoi_dung, probes):
    """AC-3.1 — Staff chỉ xem được bản ghi do chính mình tạo"""
    thay = tieu_de(ScopeProbe.objects.in_scope(nguoi_dung["staff_sale_1"]))
    assert thay == {"Của staff sale 1"}


def test_staff_khong_xem_duoc_du_lieu_nguoi_cung_team(nguoi_dung, probes):
    """AC-3.1 — Staff không thấy bản ghi của người cùng team"""
    thay = tieu_de(ScopeProbe.objects.in_scope(nguoi_dung["staff_sale_1"]))
    assert "Của staff sale 1b" not in thay


def test_leader_xem_duoc_toan_bo_team_minh(nguoi_dung, probes):
    """AC-3.2 — Leader xem được toàn bộ bản ghi của team mình"""
    thay = tieu_de(ScopeProbe.objects.in_scope(nguoi_dung["leader_sale_1"]))
    assert {"Của staff sale 1", "Của staff sale 1b"} <= thay


def test_leader_khong_xem_duoc_team_khac_cung_bo_phan(nguoi_dung, probes):
    """AC-3.3 — Leader không xem được bản ghi của team khác cùng bộ phận"""
    thay = tieu_de(ScopeProbe.objects.in_scope(nguoi_dung["leader_sale_1"]))
    assert "Của staff sale 2" not in thay


def test_manager_xem_duoc_toan_bo_bo_phan(nguoi_dung, probes):
    """AC-3.4 — Manager xem được toàn bộ bản ghi của bộ phận mình"""
    thay = tieu_de(ScopeProbe.objects.in_scope(nguoi_dung["manager_sale"]))
    assert {"Của staff sale 1", "Của staff sale 1b", "Của staff sale 2"} <= thay


def test_manager_khong_xem_duoc_bo_phan_khac(nguoi_dung, probes):
    """AC-3.5 — Manager không xem được bản ghi của bộ phận khác"""
    thay = tieu_de(ScopeProbe.objects.in_scope(nguoi_dung["manager_sale"]))
    assert "Của marketing" not in thay
    assert "Của vận đơn" not in thay


def test_admin_xem_duoc_moi_bo_phan(nguoi_dung, probes):
    """AC-3.8 — Admin có tất cả các quyền, xem được mọi bộ phận"""
    thay = tieu_de(ScopeProbe.objects.in_scope(nguoi_dung["admin"]))
    assert len(thay) == len(probes)


def test_pham_vi_leader_gom_ca_ban_ghi_cua_chinh_minh(nguoi_dung, departments, teams):
    """AC-3.2 — Leader vẫn thấy bản ghi của chính mình dù không gắn team"""
    rieng = ScopeProbe.objects.create(
        title="Ghi chú riêng của leader",
        created_by=nguoi_dung["leader_sale_1"],
        department=departments["sale"],
    )
    thay = tieu_de(ScopeProbe.objects.in_scope(nguoi_dung["leader_sale_1"]))
    assert rieng.title in thay


def test_chua_dang_nhap_thi_khong_co_pham_vi(db):
    """AC-3.6 — Chưa đăng nhập thì không suy ra được phạm vi nào"""
    from django.contrib.auth.models import AnonymousUser

    with pytest.raises(NoProfileError):
        get_user_scope(AnonymousUser())


def test_tai_khoan_khong_co_ho_so_bi_tu_choi(db, User):
    """AC-3.6 — Tài khoản chưa gán bộ phận và cấp bậc thì bị từ chối"""
    user = User.objects.create_user(username="chua_gan", password="matkhau-kiem-thu-1")
    with pytest.raises(NoProfileError):
        get_user_scope(user)


def test_cap_bac_quyet_dinh_do_rong_pham_vi(nguoi_dung):
    """AC-3.1 tới AC-3.4 — Cấp bậc quyết định phạm vi rộng bao nhiêu"""
    assert get_user_scope(nguoi_dung["staff_sale_1"]).rank == Rank.STAFF
    assert get_user_scope(nguoi_dung["leader_sale_1"]).team_ids
    assert get_user_scope(nguoi_dung["manager_sale"]).department_ids
    assert get_user_scope(nguoi_dung["admin"]).all_departments is True


def test_fixture_chung_du_vai_co_luat_rieng(nguoi_dung, departments):
    """AC-3.1 tới AC-3.8, AC-33.6 — Fixture chung có đủ các vai mang luật riêng: CEO (ADR-044), CSKH (ADR-033),
    Leader và Manager Vận đơn (phân công), Kế toán (ADR-038); mỗi vai rơi đúng nhánh luật của nó, cả chiều được
    lẫn chiều không. Thiếu vai thì bài nào cần nó lại tự dựng riêng và các bài lặp mọi vai bỏ sót nó (TL-90)."""
    from orders.services import assignment_service
    from org.services.org_service import is_accountant

    assert departments["cskh"].code == "cskh"
    ceo, cskh = nguoi_dung["ceo"], nguoi_dung["cskh"]
    leader_vd, manager_vd = nguoi_dung["leader_vd"], nguoi_dung["manager_vd"]
    assert (ceo.profile.rank, ceo.profile.department_id) == (Rank.CEO, None)
    assert (cskh.profile.rank, cskh.profile.department) == (Rank.STAFF, departments["cskh"])
    assert (leader_vd.profile.rank, leader_vd.profile.department) == (Rank.LEADER, departments["vd"])
    assert (manager_vd.profile.rank, manager_vd.profile.department) == (Rank.MANAGER, departments["vd"])
    ten = [u.username for u in nguoi_dung.values()]
    assert len(ten) == len(set(ten))

    pham_vi_ceo = get_user_scope(ceo)
    assert pham_vi_ceo.all_departments is True and pham_vi_ceo.is_admin is False
    assert assignment_service.only_own_rows(cskh) is True
    assert assignment_service.only_own_rows(leader_vd) is False
    assert assignment_service.can_assign(leader_vd) and assignment_service.can_assign(manager_vd)
    for vai in ("cskh", "ceo", "staff_vd"):
        assert not assignment_service.can_assign(nguoi_dung[vai]), vai
    assert is_accountant(nguoi_dung["staff_kt"]) and not is_accountant(ceo)


def test_ban_ghi_da_xoa_khong_con_trong_pham_vi(nguoi_dung, probes):
    """AC-9.1 — Bản ghi bị đánh dấu xoá không xuất hiện trong danh sách"""
    probes["cua_staff_1"].delete(by=nguoi_dung["manager_sale"])
    thay = tieu_de(ScopeProbe.objects.in_scope(nguoi_dung["staff_sale_1"]))
    assert "Của staff sale 1" not in thay
    # Nhưng vẫn còn trong cơ sở dữ liệu, không xoá cứng
    assert ScopeProbe.all_objects.filter(pk=probes["cua_staff_1"].pk).exists()
