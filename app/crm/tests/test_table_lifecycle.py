"""Xóa bảng giữ dữ liệu, quyền và khóa vòng đời."""
import pytest
from core.constants import Rank, JobKind, JobStatus
from core.exceptions import BusinessError, OutOfScopeError
from forms_builder.models import DataRecord, FormDef
from forms_builder.services import record_service
from .test_shared_grid import generic

pytestmark = pytest.mark.django_db


def test_delete_and_restore_preserve_identity(client, generic, nguoi_dung):
    table, row = generic
    client.force_login(nguoi_dung['manager_mkt'])
    url=f'/bang-tinh/{table.code}/xoa-bang/'
    assert client.post(url, {'name':'Sai tên'}).status_code == 400
    assert client.post(url, {'name':table.name}).status_code == 302
    row.refresh_from_db();table.refresh_from_db()
    assert table.deleted_at and row.deleted_at is None
    assert not DataRecord.objects.in_scope(nguoi_dung['admin']).filter(pk=row.pk).exists()
    assert client.get(f'/bang-tinh/{table.code}/du-lieu/').status_code in (403,404)
    assert client.post(f'/bang-tinh/{table.code}/khoi-phuc-bang/').status_code == 302
    table.refresh_from_db();row.refresh_from_db()
    assert table.deleted_at is None and row.table_id==table.pk


@pytest.mark.parametrize('role',['staff_mkt','leader_sale_1','manager_sale'])
def test_no_cross_department_delete(client, generic, nguoi_dung, role):
    client.force_login(nguoi_dung[role])
    assert client.post(f'/bang-tinh/{generic[0].code}/xoa-bang/',{'name':generic[0].name}).status_code in (403,404)


def test_active_form_blocks_delete(client, generic, nguoi_dung):
    table, row=generic
    FormDef.objects.create(name='Biểu mẫu đang dùng',code='active-form',table=table,department=table.department)
    client.force_login(nguoi_dung['admin'])
    response=client.post(f'/bang-tinh/{table.code}/xoa-bang/',{'name':table.name})
    assert response.status_code==400 and 'Biểu mẫu đang dùng' in response.content.decode()


def test_new_waybill_is_protected_even_for_admin(client, departments, nguoi_dung):
    from forms_builder.models import TableDef
    from orders.constants import ACTIVE_WAYBILL_TABLE_CODE
    from crm.services import row_mutations
    from forms_builder.services import lifecycle_service
    table=TableDef.objects.create(code=ACTIVE_WAYBILL_TABLE_CODE,name='Vận đơn mới',department=departments['vd'])
    admin=nguoi_dung['admin'];client.force_login(admin)
    assert not row_mutations.can_create(admin,table)
    assert not lifecycle_service.can_delete(admin,table)
    assert client.post(f'/bang-tinh/{table.code}/xoa-bang/',{'name':table.name}).status_code==403
    assert table.deleted_at is None
