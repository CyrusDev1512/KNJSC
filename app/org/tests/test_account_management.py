"""Ma trận quản lý tài khoản: kiểm qua endpoint thật, không chỉ nút UI."""
import pytest
from django.contrib.auth import authenticate
from django.urls import reverse
from django.test import Client, override_settings

from core.constants import Rank
from core.scope import get_user_scope

pytestmark = pytest.mark.django_db
PASSWORD = "New-Account-Test-2026!"


@pytest.fixture
def actors(nguoi_dung, make_user):
    return {**nguoi_dung, "ceo": make_user("director", "ceo"),
            "other_ceo": make_user("director_two", "ceo"),
            "other_admin": make_user("admin_two", Rank.ADMIN)}


def test_leader_can_open_password_screen(client, actors):
    client.force_login(actors["leader_sale_1"])
    response = client.get(reverse("nhan_su_sua", args=[actors["staff_sale_1"].profile.pk]))
    assert response.status_code == 200
    assert 'name="new_password1"' in response.content.decode()
    assert 'name="rank"' not in response.content.decode()


def test_ceo_is_company_wide_but_not_admin(actors):
    scope = get_user_scope(actors["ceo"])
    assert scope.all_departments
    assert not scope.is_admin


@pytest.mark.parametrize("actor,target,allowed", [
    ("staff_sale_1", "staff_sale_1b", False),
    ("leader_sale_1", "staff_sale_1", True),
    ("leader_sale_1", "staff_sale_2", False),
    ("leader_sale_1", "leader_sale_2", False),
    ("manager_sale", "staff_sale_2", True),
    ("manager_sale", "leader_sale_2", True),
    ("manager_sale", "manager_mkt", False),
    ("manager_sale", "staff_mkt", False),
    ("ceo", "manager_mkt", True),
    ("ceo", "other_ceo", False),
    ("ceo", "admin", False),
    ("admin", "ceo", True),
    ("admin", "other_admin", True),
    ("admin", "admin", False),
])
@pytest.mark.parametrize("action", ["dat-lai-mat-khau", "xoa"])
def test_management_matrix(client, actors, actor, target, allowed, action):
    user = actors[target]
    old_hash = user.password
    client.force_login(actors[actor])
    response = client.post(f"/nhan-su/{user.profile.pk}/{action}/", {
        "new_password1": PASSWORD, "new_password2": PASSWORD, "confirm": "yes",
    })
    assert response.status_code == (302 if allowed else 403)
    user.refresh_from_db()
    if action == "dat-lai-mat-khau":
        assert user.check_password(PASSWORD) == allowed
        if not allowed:
            assert user.password == old_hash
    else:
        assert user.is_active != allowed
        assert (user.profile.deleted_at is not None) == allowed


def test_deleted_account_cannot_authenticate_even_reactivated(client, actors):
    user = actors["staff_sale_1"]
    client.force_login(actors["admin"])
    response = client.post(f"/nhan-su/{user.profile.pk}/xoa/", {"confirm": "yes"})
    assert response.status_code == 302
    user.refresh_from_db()
    user.is_active = True
    user.save(update_fields=["is_active"])
    assert authenticate(username=user.username, password="matkhau-kiem-thu-1") is None


def test_ceo_cannot_inherit_business_write_even_in_own_department(actors, departments):
    from types import SimpleNamespace
    from forms_builder.services import grant_service
    from documents.services import document_service
    from resources.services import resource_service
    from culture.services import recognition_service
    from orders.services import payment_service, assignment_service
    from reports.services import daily_service
    ceo = actors["ceo"]
    ceo.profile.department = departments["sale"]
    ceo.profile.save()
    table = SimpleNamespace(pk=1, code="sale", department_id=departments["sale"].pk)
    assert not grant_service.can_fill(ceo, table)
    assert not grant_service.can_create_record(ceo, table)
    assert not resource_service.can_manage(ceo)
    assert not document_service.can_manage_category(ceo, departments["sale"])
    assert not recognition_service.can_recognize(ceo)
    assert not payment_service.can_manage(ceo)
    assert not assignment_service.can_assign(ceo)
    report = SimpleNamespace(created_by_id=ceo.pk, department_id=table.department_id, team_id=None)
    assert not daily_service.can_amend(ceo, report)
    assert not daily_service.can_withdraw(ceo, report)


@pytest.mark.parametrize("first,second", [(PASSWORD, "different"), ("123", "123")])
def test_password_errors_do_not_change_hash_or_echo_input(client, actors, first, second):
    user = actors["staff_sale_1"]
    before = user.password
    client.force_login(actors["leader_sale_1"])
    response = client.post(reverse("nhan_su_dat_lai_mat_khau", args=[user.profile.pk]),
                           {"new_password1": first, "new_password2": second})
    assert response.status_code == 200
    assert f'value="{first}"' not in response.content.decode()
    assert "no-store" in response.headers["Cache-Control"]
    user.refresh_from_db()
    assert user.password == before


def test_reset_invalidates_erp_crm_sessions_and_forces_change(client, actors):
    from core.models import AuditLog
    target = actors["staff_sale_1"]
    erp, crm = Client(), Client()
    erp.force_login(target)
    crm.force_login(target)
    client.force_login(actors["leader_sale_1"])
    assert client.post(reverse("nhan_su_dat_lai_mat_khau", args=[target.profile.pk]),
                       {"new_password1": PASSWORD, "new_password2": PASSWORD}).status_code == 302
    assert "/dang-nhap/" in erp.get("/").url
    with override_settings(ROOT_URLCONF="knjsc.urls_bangtinh"):
        assert "/dang-nhap/" in crm.get("/thu-muc/").url
    assert not erp.login(username=target.username, password="matkhau-kiem-thu-1")
    assert erp.login(username=target.username, password=PASSWORD)
    assert erp.get("/").url == reverse("doi_mat_khau")
    target.refresh_from_db()
    assert target.password != PASSWORD and target.check_password(PASSWORD)
    assert target.profile.must_change_password
    assert not AuditLog.objects.filter(detail__contains=PASSWORD).exists()
    assert PASSWORD not in repr(dict(client.session))


def test_reset_keeps_locked_account_locked(client, actors):
    target = actors["staff_sale_1"]
    target.is_active = False
    target.save(update_fields=["is_active"])
    client.force_login(actors["leader_sale_1"])
    assert client.post(reverse("nhan_su_dat_lai_mat_khau", args=[target.profile.pk]),
                       {"new_password1": PASSWORD, "new_password2": PASSWORD}).status_code == 302
    target.refresh_from_db()
    assert not target.is_active and target.check_password(PASSWORD)
    assert authenticate(username=target.username, password=PASSWORD) is None


def test_delete_requires_confirmation_and_csrf(client, actors):
    user = actors["staff_sale_1"]
    url = reverse("nhan_su_xoa", args=[user.profile.pk])
    client.force_login(actors["leader_sale_1"])
    page = client.get(url)
    assert page.status_code == 200 and user.profile.staff_code.encode() in page.content
    assert client.post(url).status_code == 200
    assert user.profile.deleted_at is None
    strict = Client(enforce_csrf_checks=True)
    strict.force_login(actors["leader_sale_1"])
    assert strict.post(url, {"confirm": "yes"}).status_code == 403
    assert client.get(reverse("nhan_su_dat_lai_mat_khau", args=[user.profile.pk])).status_code == 405


def test_delete_preserves_history_and_hides_new_assignments(client, actors, departments):
    from forms_builder.models import TableDef, DataRecord, FormDef
    from reports.models import DailyReport
    from taskboard.models import Task
    from taskboard.services.task_service import assignable_users
    from core.models import AuditLog
    from org.models import UserProfile
    from orders.models import Customer, Order, WaybillAssignment
    from org.services.account_service import unlock_account, reset_password, update_profile
    from core.exceptions import BusinessError
    from django.utils import timezone
    target = actors["staff_sale_1"]
    table = TableDef.objects.create(code="kept_history", name="History", department=departments["sale"])
    row = DataRecord.objects.create(table=table, created_by=target, department=table.department, data={"old": 1})
    form = FormDef.objects.create(code="kept_form", name="History", department=table.department, table=table)
    report = DailyReport.objects.create(form=form, record=row, created_by=target, department=table.department,
                                       report_date=timezone.localdate())
    task = Task.objects.create(title="Giữ phân công", created_by=target, assignee=target, department=table.department)
    customer = Customer.objects.create(phone="+15550000001", name="Khách kiểm thử")
    order = Order.objects.create(code="HISTORY-KEEP", customer=customer, seller=target,
                                 created_by=target, department=table.department)
    assignment = WaybillAssignment.objects.create(record=row, care=target)
    stale_profile = target.profile
    old_code = stale_profile.staff_code
    old_team = stale_profile.team_id
    client.force_login(actors["admin"])
    assert client.post(reverse("nhan_su_xoa", args=[stale_profile.pk]), {"confirm": "yes"}).status_code == 302
    for obj in (row, report, task, order):
        obj.refresh_from_db()
        assert obj.created_by_id == target.pk
    assert task.assignee_id == target.pk
    assert order.seller_id == target.pk
    assignment.refresh_from_db()
    assert assignment.care_id == target.pk
    assert row.data == {"old": 1}
    saved = UserProfile.objects.get(pk=stale_profile.pk)
    assert saved.staff_code == old_code and saved.team_id == old_team
    assert not assignable_users(actors["admin"]).filter(pk=target.pk).exists()
    listing = client.get(reverse("nhan_su"))
    assert saved.pk not in [profile.pk for profile in listing.context["trang"]]
    assert AuditLog.objects.filter(target_id=str(saved.pk), action="delete").exists()
    for call in (lambda: unlock_account(stale_profile), lambda: reset_password(stale_profile, PASSWORD),
                 lambda: update_profile(stale_profile, {"full_name": "Changed"})):
        with pytest.raises(BusinessError):
            call()
    for name in ("nhan_su_sua", "nhan_su_doi_trang_thai", "nhan_su_dat_lai_mat_khau", "nhan_su_xoa"):
        assert client.post(reverse(name, args=[saved.pk]), {"confirm": "yes"}).status_code == 404


@pytest.mark.parametrize("role", ["staff_sale_1", "leader_sale_1", "manager_sale", "ceo"])
def test_profile_privileges_remain_admin_only(client, actors, role):
    target = actors["staff_sale_1b"]
    client.force_login(actors[role])
    assert client.post(reverse("nhan_su_sua", args=[target.profile.pk]), {"rank": "admin"}).status_code == 403
    assert client.post(reverse("nhan_su_doi_trang_thai", args=[target.profile.pk])).status_code == 403
    assert client.post(reverse("nhan_su_moi"), {"username": "injected"}).status_code == 403
    target.profile.refresh_from_db()
    assert target.profile.rank == Rank.STAFF


def test_deleted_user_never_authenticates_with_valid_hash(actors):
    from django.utils import timezone
    from org.models import UserProfile
    target = actors["staff_sale_1"]
    UserProfile.objects.filter(pk=target.profile.pk).update(deleted_at=timezone.now())
    # is_active và mật khẩu đều còn hợp lệ: backend vẫn từ chối.
    assert target.is_active and target.check_password("matkhau-kiem-thu-1")
    assert authenticate(username=target.username, password="matkhau-kiem-thu-1") is None


def test_admin_interfaces_block_hard_delete(actors):
    from django.contrib import admin
    from django.contrib.auth import get_user_model
    from django.test import RequestFactory
    from org.models import UserProfile
    request = RequestFactory().get("/admin/")
    request.user = actors["admin"]
    for model in (get_user_model(), UserProfile):
        assert not admin.site._registry[model].has_delete_permission(request)


def test_account_list_stays_within_ten_queries(client, actors, make_user, departments, django_assert_max_num_queries):
    for n in range(25):
        make_user(f"query_person_{n}", Rank.STAFF, departments["sale"])
    client.force_login(actors["admin"])
    client.get("/nhan-su/")  # khởi tạo session, không tính lần ghi dấu truy cập đầu tiên
    with django_assert_max_num_queries(10):
        response = client.get("/nhan-su/")
        assert response.status_code == 200


def test_permission_is_rechecked_with_fresh_actor_and_target(actors):
    from org.models import UserProfile
    from org.services.account_management import reset_account_password
    from core.exceptions import OutOfScopeError
    stale_leader = actors["leader_sale_1"]
    target = actors["staff_sale_1"]
    UserProfile.objects.filter(pk=stale_leader.profile.pk).update(rank=Rank.STAFF)
    with pytest.raises(OutOfScopeError):
        reset_account_password(target.profile.pk, PASSWORD, actor=stale_leader)
    UserProfile.objects.filter(pk=stale_leader.profile.pk).update(rank=Rank.LEADER)
    UserProfile.objects.filter(pk=target.profile.pk).update(rank=Rank.MANAGER)
    with pytest.raises(OutOfScopeError):
        reset_account_password(target.profile.pk, PASSWORD, actor=stale_leader)


def test_ceo_reads_company_records_but_cannot_mutate_or_configure(client, actors, departments, settings):
    from forms_builder.models import TableDef, DataRecord, ColumnDef
    from forms_builder.services import record_service, table_service, grant_service
    from core.exceptions import OutOfScopeError
    ceo = actors["ceo"]
    tables = []
    for department in (departments["sale"], departments["mkt"]):
        table = TableDef.objects.create(code=f"ceo_read_{department.code}", name="CEO read", department=department)
        column = ColumnDef.objects.create(table=table, code="note", name="Note", field_type="text")
        row = DataRecord.objects.create(table=table, department=department, data={"note": "unchanged"})
        assert DataRecord.objects.in_scope(ceo).filter(pk=row.pk).exists()
        tables.append((table, column, row))
    table, column, row = tables[0]
    client.force_login(ceo)
    assert client.get("/admin/").status_code in (302, 404)
    assert client.get(reverse("nhan_su")).status_code == 200
    for name, args in (("bang_cot", [table.code]), ("bang_moi", []), ("bieu_mau_moi", [])):
        assert client.post(reverse(name, args=args), {}).status_code == 403
    for call in (
        lambda: record_service.update_cell(row, "note", "forbidden", actor=ceo),
        lambda: table_service.create_table(name="No", code="no", department=table.department, actor=ceo),
        lambda: grant_service.grant(table=table, user=actors["staff_sale_1"], action="edit", actor=ceo),
    ):
        with pytest.raises(OutOfScopeError):
            call()
    row.refresh_from_db()
    assert row.data["note"] == "unchanged"


def test_admin_can_create_ceo_without_department(client, actors):
    from org.services.account_service import create_with_temporary_password
    from org.forms import TaoTaiKhoanForm
    form = TaoTaiKhoanForm({"full_name": "Giám đốc mới", "username": "new_director", "rank": "ceo", "password": PASSWORD})
    assert form.is_valid(), form.errors
    profile, _ = create_with_temporary_password(username="new_director", full_name="Giám đốc mới", rank=Rank.CEO,
                                               actor=actors["admin"], password=PASSWORD)
    assert not profile.user.is_staff and not profile.user.is_superuser


def test_cannot_delete_last_admin_or_reuse_deleted_identifiers(make_user):
    from org.services.account_management import delete_account
    from org.services.account_service import create_with_temporary_password
    from org.services import staff_code_service
    from core.exceptions import OutOfScopeError
    from django.core.exceptions import ValidationError
    admin = make_user("only_admin", Rank.ADMIN)
    with pytest.raises(OutOfScopeError):
        delete_account(admin.profile.pk, actor=admin)
    assert admin.is_active
    target = make_user("keep_identifier", Rank.STAFF)
    code = target.profile.staff_code
    delete_account(target.profile.pk, actor=admin)
    assert staff_code_service._taken(code)
    with pytest.raises(ValidationError):
        create_with_temporary_password(username=target.username.upper(), full_name="Reuse", actor=admin, password=PASSWORD)


@pytest.mark.parametrize("role", ["leader_sale_1", "manager_sale", "ceo", "admin"])
def test_management_detail_query_budget(client, actors, role, django_assert_max_num_queries):
    client.force_login(actors[role])
    url = reverse("nhan_su_sua", args=[actors["staff_sale_1"].profile.pk])
    client.get(url)
    with django_assert_max_num_queries(10):
        assert client.get(url).status_code == 200


def test_promoting_admin_to_ceo_removes_technical_privileges(actors):
    from org.services.account_service import update_profile
    target = actors["other_admin"]
    target.is_staff = target.is_superuser = True
    target.save(update_fields=["is_staff", "is_superuser"])
    epoch = target.profile.session_epoch
    update_profile(target.profile, {"rank": Rank.CEO}, actor=actors["admin"])
    target.refresh_from_db()
    assert target.profile.rank == Rank.CEO
    assert target.profile.session_epoch > epoch
    assert not target.is_staff and not target.is_superuser


def test_django_admin_cannot_reintroduce_ceo_flags_or_restore_deleted_profile(actors):
    from django.contrib import admin
    from django.contrib.auth import get_user_model
    from django.test import RequestFactory
    from django.http import Http404
    from org.models import UserProfile
    from org.services.account_management import delete_account
    request = RequestFactory().post("/admin/")
    request.user = actors["admin"]
    target = actors["other_admin"]
    target.profile.rank = Rank.CEO
    admin.site._registry[UserProfile].save_model(request, target.profile, None, True)
    target.refresh_from_db()
    assert not target.is_staff and not target.is_superuser
    target.is_staff = target.is_superuser = True
    admin.site._registry[get_user_model()].save_model(request, target, None, True)
    target.refresh_from_db()
    assert not target.is_staff and not target.is_superuser
    stale_profile = target.profile
    delete_account(stale_profile.pk, actor=actors["admin"])
    with pytest.raises(Http404):
        admin.site._registry[UserProfile].save_model(request, stale_profile, None, True)
