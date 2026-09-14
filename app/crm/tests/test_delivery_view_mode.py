"""Chế độ xem toàn bảng không mở rộng quyền ghi — quyết định 12.09.2026."""
import pytest
from core.constants import Rank
from forms_builder.models import DataRecord
from .test_waybill_feedback import feedback, delivery_leader, assign_rows
from .test_master_grid import write
from .test_optimization import enabled

pytestmark = pytest.mark.django_db
BASE = '/bang-tinh/van_don_moi/'
MODE = BASE + 'che-do-xem/'


def test_manager_changes_visibility_but_not_editing(client, feedback, nguoi_dung, make_user, departments, delivery_leader):
    manager = make_user('mode_manager', Rank.MANAGER, departments['vd'])
    staff = nguoi_dung['staff_vd']
    own, other = feedback[2]
    assign_rows(delivery_leader, [own], delivery=staff.pk)
    client.force_login(manager)
    assert client.post(MODE, {'mode': 'all'}).status_code == 302
    client.force_login(staff)
    data = client.get(BASE + 'du-lieu/').json()
    assert data['total'] == 2
    assert {r['id']: r['editable'] for r in data['rows']} == {own.pk: True, other.pk: False}
    assert write(client, other, old=other.data.get('ghi_chu')).status_code == 403
    assert write(client, own, old=own.data.get('ghi_chu')).status_code == 200
    client.force_login(manager)
    assert client.post(MODE, {'mode': 'assigned'}).status_code == 302
    client.force_login(staff)
    assert client.get(BASE + 'du-lieu/').json()['total'] == 1
    assert client.get(f'/van-don/chi-tiet/{other.pk}/').status_code in (403, 404)


@pytest.mark.parametrize('actor', ['staff_vd', 'manager_mkt', 'staff_sale_1'])
def test_unauthorized_mode_change(client, feedback, nguoi_dung, actor):
    client.force_login(nguoi_dung[actor])
    assert client.post(MODE, {'mode': 'all'}).status_code == 403


def test_leader_cannot_change_mode(client, feedback, delivery_leader):
    client.force_login(delivery_leader)
    assert client.post(MODE, {'mode': 'all'}).status_code == 403


def test_default_invalid_values_and_other_departments(client, feedback, nguoi_dung):
    staff = nguoi_dung['staff_vd']
    assert not DataRecord.objects.in_scope(staff).filter(table=feedback[0]).exists()
    sale = nguoi_dung['staff_sale_1']
    before = set(DataRecord.objects.in_scope(sale).values_list('pk', flat=True))
    client.force_login(nguoi_dung['admin'])
    assert client.post(MODE, {'mode': 'anything'}).status_code == 400
    assert client.post(MODE, {'mode': 'all'}).status_code == 302
    assert set(DataRecord.objects.in_scope(sale).values_list('pk', flat=True)) == before
    assert client.post('/bang-tinh/van_don/che-do-xem/', {'mode': 'all'}).status_code == 404


def test_tokens_poll_export_and_replay_follow_current_rights(client, feedback, nguoi_dung, delivery_leader, enabled):
    import uuid
    from django.http import QueryDict
    from forms_builder.services import export_service
    from orders.services.delivery_view_service import change
    from crm.services import grid_service
    table, _, rows = feedback
    staff, admin = nguoi_dung['staff_vd'], nguoi_dung['admin']
    assign_rows(delivery_leader, [rows[0]], delivery=staff.pk)
    client.force_login(staff)
    first = client.get(BASE+'du-lieu/', {'protocol': 2}).json()
    operation = str(uuid.uuid4())
    assert write(client, rows[0], old=rows[0].data.get('ghi_chu'), operation=operation).status_code == 200
    change(admin, table, 'all')
    assign_rows(delivery_leader, [rows[0]], delivery=None)
    # Quyền đọc còn, nhưng không được nhận lại biên nhận thành công sau mất quyền sửa.
    assert write(client, rows[0], old=rows[0].data.get('ghi_chu'), operation=operation).status_code == 403
    assert client.get(BASE+'du-lieu/', {'protocol': 2, 'query_token': first['query_token']}).status_code == 409
    wide = client.get(BASE+'du-lieu/', {'protocol': 2}).json()
    assert wide['total'] == 2
    poll = client.get(BASE+'moi-nhat/').json()
    assert poll['delivery_view_version'] == 1
    table.refresh_from_db()
    grid = grid_service.build_grid(staff, QueryDict(), table=table)
    assert grid.queryset.count() == 2
    kind, workbook = export_service.export(staff, table, QueryDict(), builder='grid')
    assert workbook.active.max_row == 3
    change(admin, table, 'assigned')
    sync = client.post(BASE+'dong-bo/', {'ids':[r.pk for r in rows], 'visible':[],
        'query':'', 'query_token':wide['query_token'], 'revision':wide['revision']}, content_type='application/json').json()
    assert sync['delivery_view_version'] == 2 and set(sync['removed']) == {r.pk for r in rows}
    assert client.get(BASE+'du-lieu/', {'protocol': 2}).json()['total'] == 0


def test_links_and_csrf(client, feedback, nguoi_dung):
    from django.test import Client
    from django.urls import reverse
    client.force_login(nguoi_dung['admin'])
    assert 'Chế độ xem bảng' in client.get(BASE).content.decode()
    assert 'Chế độ xem bảng' in client.get(reverse('bang_cot', args=[feedback[0].code])).content.decode()
    strict = Client(enforce_csrf_checks=True)
    strict.force_login(nguoi_dung['admin'])
    assert strict.post(MODE, {'mode':'all'}).status_code == 403


def test_full_view_does_not_query_per_row(client, feedback, nguoi_dung, django_assert_max_num_queries):
    from orders.services.delivery_view_service import change
    table, _, rows = feedback
    DataRecord.objects.bulk_create([DataRecord(table=table, department=table.department,
        created_by=nguoi_dung['admin'], data=rows[0].data) for _ in range(100)])
    change(nguoi_dung['admin'], table, 'all')
    client.force_login(nguoi_dung['staff_vd'])
    # Giữ đúng trần của endpoint lưới hiện có, không tạo N+1 khi kiểm quyền ghi.
    with django_assert_max_num_queries(22):
        response = client.get(BASE+'du-lieu/')
    assert response.status_code == 200 and len(response.json()['rows']) == 100


def test_mode_audited_idempotent_and_legacy_unchanged(feedback, nguoi_dung):
    from forms_builder.models import TableDef
    from core.models import AuditLog
    from orders.services.delivery_view_service import change
    table = feedback[0]
    old = TableDef.objects.get(code='van_don')
    before = (old.is_shared, old.delivery_view_all, old.delivery_view_version)
    count = AuditLog.objects.count()
    first = change(nguoi_dung['admin'], table, 'all')
    second = change(nguoi_dung['admin'], table, 'all')
    assert first.delivery_view_version == second.delivery_view_version == 1
    assert AuditLog.objects.count() == count+1
    old.refresh_from_db()
    assert (old.is_shared, old.delivery_view_all, old.delivery_view_version) == before
