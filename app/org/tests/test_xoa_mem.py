"""Kiểm thử xoá mềm trên module org.

Bài kiểm này sinh ra từ một lỗi thật: khi gắn manager có phạm vi quyền cho
Team, manager mới kế thừa nhầm `models.QuerySet` thay vì `SoftDeleteQuerySet`,
làm Team mất tính năng xoá mềm mà không ai biết.

Từ đợt rà soát sau đó, manager mặc định của Bộ phận và Team **tự loại** bản
ghi đã xoá. Muốn thấy cả bản ghi đã xoá thì dùng `all_objects`.
"""
import pytest

from org.models import Department, Team

pytestmark = pytest.mark.django_db


def test_xoa_team_la_danh_dau_khong_xoa_cung(departments):
    """AC-9.1 — Xoá team thì bản ghi vẫn còn trong cơ sở dữ liệu, chỉ đánh dấu"""
    team = Team.objects.create(name="Team thử", department=departments["sale"])
    team.delete()

    assert not Team.objects.filter(pk=team.pk).exists()        # khuất khỏi danh sách
    assert Team.all_objects.filter(pk=team.pk).exists()        # vẫn còn trong bảng
    team.refresh_from_db()
    assert team.deleted_at is not None


def test_xoa_bo_phan_la_danh_dau_khong_xoa_cung(departments):
    """AC-9.1 — Xoá bộ phận cũng là đánh dấu"""
    bo_phan = departments["mkt"]
    bo_phan.delete()

    assert not Department.objects.filter(pk=bo_phan.pk).exists()
    assert Department.all_objects.filter(pk=bo_phan.pk).exists()
    bo_phan.refresh_from_db()
    assert bo_phan.deleted_at is not None


def test_manager_cua_team_van_con_ham_xoa_cung(departments):
    """AC-9.1 — Manager của Team phải giữ đủ hàm của SoftDeleteQuerySet"""
    for ten_ham in ("delete", "hard_delete", "alive", "dead", "in_scope"):
        assert hasattr(Team.objects.all(), ten_ham), ten_ham
    for ten_ham in ("delete", "hard_delete", "alive", "dead", "in_scope"):
        assert hasattr(Department.objects.all(), ten_ham), ten_ham


def test_xoa_theo_lo_van_ghi_nguoi_xoa(departments, nguoi_dung):
    """AC-9.1 — Xoá cả lô cũng ghi lại ai xoá, không chỉ ghi lúc nào"""
    Team.objects.create(name="Team lô 1", department=departments["sale"])
    Team.objects.create(name="Team lô 2", department=departments["sale"])

    Team.objects.filter(name__startswith="Team lô").delete(by=nguoi_dung["admin"])

    for team in Team.all_objects.filter(name__startswith="Team lô"):
        assert team.deleted_at is not None
        assert team.deleted_by_id == nguoi_dung["admin"].pk


def test_bo_phan_da_xoa_khong_con_o_bat_ky_dau(departments, nguoi_dung):
    """AC-9.1 — Bộ phận đã xoá biến mất khỏi mọi danh sách và mọi ô chọn

    Trước đây manager không tự loại bản ghi đã xoá, nên bảy chỗ trong mã phải
    tự nhớ `.filter(deleted_at__isnull=True)`. Quên một chỗ là bản ghi đã xoá
    hiện trở lại.
    """
    from org.forms import SuaHoSoForm, TaoTaiKhoanForm, TeamForm

    bo_phan = departments["vd"]
    bo_phan.delete()

    assert bo_phan not in list(Department.objects.all())
    assert bo_phan not in list(Department.objects.in_scope(nguoi_dung["admin"]))
    assert bo_phan not in list(TaoTaiKhoanForm().fields["department"].queryset)
    assert bo_phan not in list(TeamForm().fields["department"].queryset)
    assert bo_phan not in list(SuaHoSoForm().fields["department"].queryset)


def test_team_da_xoa_khong_con_trong_pham_vi(nguoi_dung, teams):
    """AC-3.2 — Team đã đánh dấu xoá không còn trong danh sách theo phạm vi"""
    teams["sale1"].delete()
    con_lai = list(Team.objects.in_scope(nguoi_dung["admin"]))
    assert teams["sale1"] not in con_lai
    assert teams["sale2"] in con_lai


def test_leader_cua_team_da_xoa_mat_pham_vi_team(nguoi_dung, teams):
    """AC-3.2 — Team bị xoá thì Leader không còn phạm vi trên team đó"""
    leader = nguoi_dung["leader_sale_1"]
    assert leader.profile.scope_team_ids()

    teams["sale1"].delete()
    assert leader.profile.scope_team_ids() == ()
