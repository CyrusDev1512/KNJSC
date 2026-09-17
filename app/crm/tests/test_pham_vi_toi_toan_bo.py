"""ADR-033 — Nhân viên Vận đơn xem và sửa toàn bảng; nút Tôi / Toàn bộ lọc theo
cột phụ trách của bộ phận mình; bỏ Chế độ xem bảng (ADR-026) và Chế độ Xem/Chỉnh sửa.
"""
import uuid

import pytest
from django.http import QueryDict

from core.constants import Rank
from core.exceptions import OutOfScopeError
from crm.services import grid_service
from forms_builder.models import DataRecord, TableDef
from forms_builder.services import export_service, record_service
from orders.services import assignment_service

from .test_master_grid import BASE, write
from .test_waybill_feedback import assign_rows, cskh_staff, delivery_leader, feedback, visible  # noqa: F401

pytestmark = pytest.mark.django_db


@pytest.fixture
def ke_toan(make_user):
    from org.models import Department
    return make_user('ke_toan', Rank.STAFF, Department.objects.get_or_create(code='ke-toan', defaults={'name': 'Kế toán'})[0])


def test_delivery_staff_sees_and_edits_unassigned_rows(client, feedback, nguoi_dung, delivery_leader):
    """AC-33.1 — Nhân viên Vận đơn thấy mọi dòng, kể cả chưa phân công hay do
    người khác phụ trách, và sửa được các dòng đó (mặc định công ty 17.09.2026)."""
    table, _, rows = feedback
    staff = nguoi_dung['staff_vd']
    assign_rows(delivery_leader, [rows[1]], delivery=delivery_leader.pk)     # dòng của người khác
    client.force_login(staff)
    data = client.get(BASE + 'du-lieu/').json()
    assert data['total'] == 2 and all(r['editable'] for r in data['rows'])
    assert write(client, rows[1], old=rows[1].data.get('ghi_chu')).status_code == 200
    record_service.update_cell(rows[0], 'ghi_chu', 'Vận đơn sửa dòng chưa giao', actor=staff)
    assert client.get(f'/van-don/chi-tiet/{rows[1].pk}/').status_code == 200
    assert TableDef.objects.in_scope(staff).with_visible_record_count(staff).get(pk=table.pk).so_dong == 2


def test_care_and_sale_stay_view_only(client, feedback, nguoi_dung, delivery_leader, cskh_staff):
    """AC-33.2 — CSKH được giao chỉ xem; Sale không sửa đơn của Sale khác; cột
    phụ trách vẫn không gõ được từ ô (chỉ hộp Phân công)."""
    table, _, rows = feedback
    assign_rows(delivery_leader, [rows[0]], care=cskh_staff.pk)
    assert visible(cskh_staff, table) == {rows[0].pk}
    client.force_login(cskh_staff)
    assert write(client, rows[0], old=rows[0].data.get('ghi_chu')).status_code == 403
    client.force_login(nguoi_dung['staff_sale_1'])
    assert write(client, rows[1], old=rows[1].data.get('ghi_chu')).status_code in (403, 404)
    client.force_login(nguoi_dung['admin'])
    assert write(client, rows[0], column='phu_trach_vd', old=None, value='staff_vd').status_code == 400
    with pytest.raises(OutOfScopeError):
        record_service.update_cell(rows[1], 'ghi_chu', 'x', actor=cskh_staff)


def test_cua_toi_filters_by_department_field_and_ignored_for_admin(client, feedback, nguoi_dung, delivery_leader, cskh_staff, ke_toan, departments):
    """AC-33.3 — `cua_toi=1`: Vận đơn lọc theo Phụ trách Vận đơn, CSKH theo Phụ
    trách CSKH; Admin, Kế toán và bảng thường bỏ qua; khối dữ liệu đổi phiên bản."""
    table, _, rows = feedback
    staff = nguoi_dung['staff_vd']
    assign_rows(delivery_leader, [rows[0]], delivery=staff.pk, care=cskh_staff.pk)
    assign_rows(delivery_leader, [rows[1]], delivery=delivery_leader.pk, care=nguoi_dung['staff_sale_1'].pk)
    assert assignment_service.field_for(staff) == 'delivery'
    assert assignment_service.field_for(cskh_staff) == 'care'
    assert assignment_service.field_for(nguoi_dung['staff_sale_1']) == 'care'
    assert assignment_service.field_for(nguoi_dung['staff_mkt']) == 'marketing'
    assert assignment_service.field_for(nguoi_dung['admin']) is None
    assert assignment_service.field_for(ke_toan) is None

    def ids(user, qs=''):
        grid = grid_service.build_grid(user, QueryDict(qs), table=table)
        return set(grid.queryset.values_list('pk', flat=True)), grid.my_scope

    assert ids(staff) == ({r.pk for r in rows}, False)
    assert ids(staff, 'cua_toi=1') == ({rows[0].pk}, True)
    assert ids(delivery_leader, 'cua_toi=1') == ({rows[1].pk}, True)
    assert ids(cskh_staff, 'cua_toi=1') == ({rows[0].pk}, True)
    assert ids(nguoi_dung['staff_sale_1'], 'cua_toi=1') == ({rows[1].pk}, True)
    assert ids(nguoi_dung['admin'], 'cua_toi=1') == ({r.pk for r in rows}, False)
    assert ids(ke_toan, 'cua_toi=1') == ({r.pk for r in rows}, False)

    thuong = TableDef.objects.create(code='bang-thuong', name='Bảng thường', department=departments['vd'])
    DataRecord.objects.create(table=thuong, department=thuong.department, created_by=staff, data={})
    grid = grid_service.build_grid(staff, QueryDict('cua_toi=1'), table=thuong)
    assert grid.queryset.count() == 1 and grid.my_scope is False

    client.force_login(staff)
    full = client.get(BASE + 'du-lieu/').json()
    mine = client.get(BASE + 'du-lieu/?cua_toi=1').json()
    assert full['total'] == 2 and mine['total'] == 1 and mine['rows'][0]['id'] == rows[0].pk
    assert full['version'] != mine['version']


def test_cua_toi_reaches_excel_export_and_statistics(client, feedback, nguoi_dung, delivery_leader, settings, tmp_path):
    """AC-33.4 — `cua_toi=1` đi theo Tải Excel (trực tiếp và nền) và Thống kê."""
    from unittest.mock import patch
    from core.constants import JobStatus
    table, _, rows = feedback
    staff = nguoi_dung['staff_vd']
    assign_rows(delivery_leader, [rows[0]], delivery=staff.pk)
    kind, book = export_service.export(staff, table, QueryDict('cua_toi=1'), builder='grid')
    assert kind == 'file' and book.active.max_row == 2
    settings.STORAGE_DIR = tmp_path; settings.EXPORT_DIR = tmp_path / 'exports'
    with patch.object(export_service, 'EXPORT_SYNC_MAX_ROWS', 0), patch('forms_builder.services.import_service._day_vao_hang_doi'):
        _, job = export_service.export(staff, table, QueryDict('cua_toi=1'), builder='grid')
    export_service.run(job.pk); job.refresh_from_db()
    assert job.status == JobStatus.DONE and job.summary['exported_row_ids'] == [rows[0].pk]
    client.force_login(staff)
    assert client.get('/thong-ke/', {'nguon': 'van_don_moi'}).context['summary']['orders'] == 2
    assert client.get('/thong-ke/', {'nguon': 'van_don_moi', 'cua_toi': '1'}).context['summary']['orders'] == 1


def test_delivery_view_mode_removed(client, feedback, nguoi_dung):
    """AC-33.5 — Trang Chế độ xem bảng không còn; `TableDef` không còn
    `delivery_view_all`; màn Cột & cấp quyền không còn khối chế độ xem."""
    client.force_login(nguoi_dung['admin'])
    assert client.get(BASE + 'che-do-xem/').status_code == 404
    assert client.post(BASE + 'che-do-xem/', {'mode': 'all'}).status_code == 404
    assert 'delivery_view_all' not in {f.name for f in TableDef._meta.get_fields()}
    assert 'delivery_view_version' in {f.name for f in TableDef._meta.get_fields()}
    html = client.get(f'/bang/{feedback[0].code}/cot/').content.decode()
    assert 'Chế độ xem bảng' not in html


def test_shell_renders_scope_toggle_by_role(client, feedback, nguoi_dung, delivery_leader, ke_toan):
    """AC-33.6 — Nút Tôi / Toàn bộ chỉ hiện cho người có cột phụ trách; không còn
    nút Chế độ: Xem; `?cua_toi=1` đánh dấu nút Tôi."""
    for user, expected in ((nguoi_dung['staff_vd'], True), (delivery_leader, True),
                           (nguoi_dung['staff_sale_1'], True), (nguoi_dung['admin'], False), (ke_toan, False)):
        client.force_login(user)
        response = client.get(BASE)
        assert response.status_code == 200, user.username
        html = response.content.decode()
        assert ('id="mg-pham-vi"' in html) is expected, user.username
        assert 'id="mg-mode"' not in html and 'Chế độ: Xem' not in html
    client.force_login(nguoi_dung['staff_vd'])
    html = client.get(BASE).content.decode()
    assert '"myScope": "delivery"' in html
    assert 'data-pham-vi="toan_bo" aria-pressed="true"' in html
    html = client.get(BASE + '?cua_toi=1').content.decode()
    assert 'data-pham-vi="toi" aria-pressed="true"' in html


@pytest.mark.django_db(transaction=True)
def test_migration_0013_roundtrip(departments):
    """AC-33.7 — Migration 0013 bỏ `delivery_view_all` chạy xuôi và ngược, giữ
    `delivery_view_version` và dữ liệu."""
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor
    assert connection.settings_dict['NAME'].startswith('test_')
    table = TableDef.objects.create(code='migration-033', name='Migration 033', department=departments['vd'])
    row = DataRecord.objects.create(table=table, department=table.department, data={'ghi_chu': 'giữ'})

    def columns():
        with connection.cursor() as cursor:
            return {c.name for c in connection.introspection.get_table_description(cursor, 'forms_builder_tabledef')}

    try:
        MigrationExecutor(connection).migrate([('forms_builder', '0012_order_destination')])
        assert 'delivery_view_all' in columns() and 'delivery_view_version' in columns()
    finally:
        executor = MigrationExecutor(connection); executor.migrate(executor.loader.graph.leaf_nodes())
    assert 'delivery_view_all' not in columns() and 'delivery_view_version' in columns()
    assert DataRecord.objects.get(pk=row.pk).data == {'ghi_chu': 'giữ'}


def test_cua_toi_query_budget(client, feedback, nguoi_dung, delivery_leader, django_assert_max_num_queries):
    """AC-33.3 — Lọc Tôi không thêm truy vấn theo dòng: 100 dòng vẫn trong trần 22."""
    from orders.models import WaybillAssignment
    table, _, rows = feedback
    staff = nguoi_dung['staff_vd']
    more = DataRecord.objects.bulk_create([DataRecord(table=table, department=table.department,
        created_by=nguoi_dung['staff_sale_1'], data={**rows[0].data, 'ma_don': f'TOI-{i}'}) for i in range(98)])
    WaybillAssignment.objects.bulk_create([WaybillAssignment(record=r, delivery=staff) for r in rows + more])
    client.force_login(staff)
    client.get(BASE + 'moi-nhat/')
    with django_assert_max_num_queries(22):
        response = client.get(BASE + 'du-lieu/?cua_toi=1')
    assert response.status_code == 200 and len(response.json()['rows']) == 100
