"""Dữ liệu mẫu dùng chung cho mọi bài kiểm thử.

Dựng đủ chín vai trò của ma trận phân quyền: ba bộ phận nhân ba cấp bậc,
cộng một quản trị viên.
"""
import pytest
from django.contrib.auth import get_user_model

from core.constants import Rank


@pytest.fixture
def User():
    return get_user_model()


@pytest.fixture
def departments(db):
    from org.models import Department

    return {
        "sale": Department.objects.create(name="Sale", code="sale"),
        "mkt": Department.objects.create(name="Marketing", code="marketing"),
        "vd": Department.objects.create(name="Vận đơn", code="van-don"),
    }


@pytest.fixture
def make_user(db, User):
    """Tạo một tài khoản kèm hồ sơ nhân sự."""
    from org.models import UserProfile

    def _tao(username, rank=Rank.STAFF, department=None, team=None,
             password="matkhau-kiem-thu-1", must_change_password=False):
        user = User.objects.create_user(
            username=username, email=f"{username}@kimngan.vn", password=password,
        )
        UserProfile.objects.create(
            user=user, full_name=username.replace("_", " ").title(), rank=rank,
            department=department, team=team,
            must_change_password=must_change_password,
        )
        return user

    return _tao


@pytest.fixture
def teams(db, departments, make_user):
    """Hai team trong bộ phận Sale, mỗi team một Leader."""
    from org.models import Team

    leader1 = make_user("leader_sale_1", Rank.LEADER, departments["sale"])
    leader2 = make_user("leader_sale_2", Rank.LEADER, departments["sale"])
    t1 = Team.objects.create(name="Sale 1", department=departments["sale"], leader=leader1)
    t2 = Team.objects.create(name="Sale 2", department=departments["sale"], leader=leader2)
    leader1.profile.team = t1
    leader1.profile.save(update_fields=["team"])
    leader2.profile.team = t2
    leader2.profile.save(update_fields=["team"])
    return {"sale1": t1, "sale2": t2, "leader1": leader1, "leader2": leader2}


@pytest.fixture
def nguoi_dung(db, departments, teams, make_user):
    """Chín vai trò cộng quản trị viên."""
    return {
        "staff_sale_1": make_user("staff_sale_1", Rank.STAFF, departments["sale"], teams["sale1"]),
        "staff_sale_1b": make_user("staff_sale_1b", Rank.STAFF, departments["sale"], teams["sale1"]),
        "staff_sale_2": make_user("staff_sale_2", Rank.STAFF, departments["sale"], teams["sale2"]),
        "leader_sale_1": teams["leader1"],
        "leader_sale_2": teams["leader2"],
        "manager_sale": make_user("manager_sale", Rank.MANAGER, departments["sale"]),
        "staff_mkt": make_user("staff_mkt", Rank.STAFF, departments["mkt"]),
        "manager_mkt": make_user("manager_mkt", Rank.MANAGER, departments["mkt"]),
        "staff_vd": make_user("staff_vd", Rank.STAFF, departments["vd"]),
        "admin": make_user("quan_tri", Rank.ADMIN),
    }


@pytest.fixture
def probes(db, departments, teams, nguoi_dung):
    """Mỗi người một bản ghi, để kiểm ai thấy được của ai."""
    from core.tests.models import ScopeProbe

    def _tao(ten, nguoi, bo_phan, team=None):
        return ScopeProbe.objects.create(
            title=ten, created_by=nguoi, department=bo_phan, team=team,
        )

    return {
        "cua_staff_1": _tao("Của staff sale 1", nguoi_dung["staff_sale_1"],
                            departments["sale"], teams["sale1"]),
        "cua_staff_1b": _tao("Của staff sale 1b", nguoi_dung["staff_sale_1b"],
                             departments["sale"], teams["sale1"]),
        "cua_staff_2": _tao("Của staff sale 2", nguoi_dung["staff_sale_2"],
                            departments["sale"], teams["sale2"]),
        "cua_mkt": _tao("Của marketing", nguoi_dung["staff_mkt"], departments["mkt"]),
        "cua_vd": _tao("Của vận đơn", nguoi_dung["staff_vd"], departments["vd"]),
    }
