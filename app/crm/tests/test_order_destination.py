"""Bảng nhận đơn cấu hình bởi Admin, giữ liên kết và phạm vi đơn cũ."""
import pytest
from .test_waybill_feedback import feedback

pytestmark = pytest.mark.django_db
URL = '/cau-hinh/nhan-don/'

def test_admin_can_open_destination_configuration(client, feedback, nguoi_dung):
    client.force_login(nguoi_dung['admin'])
    response = client.get(URL)
    assert response.status_code == 200
    assert 'Bảng nhận đơn' in response.content.decode()

@pytest.mark.parametrize('role', ['staff_vd', 'staff_sale_1', 'manager_sale'])
def test_non_admin_cannot_configure(client, feedback, nguoi_dung, role):
    client.force_login(nguoi_dung[role])
    assert client.get(URL).status_code == 403
    assert client.post(URL, {'table': feedback[0].pk}).status_code == 403


@pytest.fixture
def destination(feedback, nguoi_dung):
    from orders.services import waybill_db_service
    return waybill_db_service.ensure_table(actor=nguoi_dung['admin'])


def create(user, products, phone):
    from orders.services import order_service
    return order_service.create_order(phone=phone, customer_name='Khách kiểm thử', actor=user,
        lines=[{'product': p.code, 'quantity': 2, 'unit_price': '12.50'} for p in products])


def test_switch_new_orders_keeps_old_rows_and_workflow(client, feedback, destination, nguoi_dung):
    from decimal import Decimal
    from orders.services import destination_service, assignment_service
    from orders.models import WaybillItem
    from forms_builder.models import DataRecord
    from django.http import QueryDict
    from crm.services import grid_service, statistics_profiles
    old, products, old_rows = feedback
    actor = nguoi_dung['admin']
    client.force_login(actor)
    assert client.post(URL, {'table': destination.pk}).status_code == 302
    order = create(nguoi_dung['staff_sale_1'], products, '0909000011')
    destination.refresh_from_db()
    assert order.record.table_id == destination.pk
    assert order.total == Decimal('50.00')
    assert WaybillItem.objects.filter(record=order.record).count() == 2
    assert old_rows[0].__class__.objects.get(pk=old_rows[0].pk).table_id == old.pk
    assert statistics_profiles.profile_of(destination) == 'waybill'
    assert [c.code for c in grid_service.display_columns(destination)] == list(destination.columns.order_by('order','id').values_list('code', flat=True))
    assert DataRecord.objects.in_scope(nguoi_dung['staff_vd'], table=destination).filter(pk=order.record_id).exists()
    assignment_service.assign(actor, {order.record_id: 0}, {'delivery': nguoi_dung['staff_vd'].pk})
    assert DataRecord.objects.in_scope(nguoi_dung['staff_vd'], table=destination).filter(pk=order.record_id).exists()
    client.force_login(nguoi_dung['staff_vd'])
    base=f'/bang-tinh/{destination.code}/'
    response=client.get(base+'du-lieu/')
    assert response.status_code == 200 and response.json()['total'] == 1
    assert client.get(f'/van-don/chi-tiet/{order.record_id}/').status_code == 200
    destination_service.configure(actor, old.pk)
    next_order=create(nguoi_dung['staff_sale_2'], products, '0909000012')
    assert next_order.record.table_id == old.pk
    order.refresh_from_db()
    assert order.record.table_id == destination.pk
    assert DataRecord.objects.in_scope(nguoi_dung['staff_vd'], table=destination).filter(pk=order.record_id).exists()
    grid=grid_service.build_grid(actor, QueryDict('sp='+products[1].code),table=destination)
    assert list(grid.queryset.values_list('pk',flat=True)) == [order.record_id]


def test_reject_bad_schema_or_populated_generic_table(client, feedback, destination, nguoi_dung):
    from forms_builder.models import DataRecord
    from orders.services import destination_service
    client.force_login(nguoi_dung['admin'])
    DataRecord.objects.create(table=destination, department=destination.department, data={'ghi_chu':'giữ lại'})
    assert client.post(URL, {'table': destination.pk}).status_code == 400
    assert destination_service.current().pk == feedback[0].pk
    destination.columns.filter(code='ma_don').delete()
    assert client.post(URL, {'table': destination.pk}).status_code == 400
    assert client.post(URL, {'table': '-1'}).status_code == 400


def test_selected_destination_failure_rolls_back_without_fallback(feedback, destination, nguoi_dung):
    from orders.services import destination_service
    from orders.models import Order
    from core.exceptions import BusinessError
    from forms_builder.models import TableDef
    destination_service.configure(nguoi_dung['admin'], destination.pk)
    before = Order.objects.count()
    TableDef.objects.filter(pk=destination.pk).update(is_active=False)
    with pytest.raises(BusinessError):
        create(nguoi_dung['staff_sale_1'], feedback[1], '0909000013')
    assert Order.objects.count() == before


def test_destination_cannot_be_deleted(feedback, destination, nguoi_dung):
    from orders.services import destination_service
    from forms_builder.services import lifecycle_service
    destination_service.configure(nguoi_dung['admin'], destination.pk)
    destination.refresh_from_db()
    assert not lifecycle_service.can_delete(nguoi_dung['admin'], destination)



def test_destination_payment_edit_permissions_and_export(client, feedback, destination, nguoi_dung, settings, tmp_path):
    import uuid
    from .test_payment_documents import create_document
    from orders.services import destination_service, assignment_service
    from forms_builder.services import export_service
    from django.http import QueryDict
    settings.PAYMENT_DOCUMENTS_ENABLED = True
    settings.STORAGE_DIR = tmp_path
    admin, staff = nguoi_dung['admin'], nguoi_dung['staff_vd']
    destination_service.configure(admin, destination.pk)
    a=create(nguoi_dung['staff_sale_1'],feedback[1],'0909000014')
    b=create(nguoi_dung['staff_sale_2'],feedback[1],'0909000015')
    assignment_service.assign(admin,{a.record_id:0},{'delivery':staff.pk})
    destination.refresh_from_db()
    client.force_login(staff)
    response=create_document(client,a.record)
    assert response.status_code == 200
    assert create_document(client,b.record,reference='not-mine').status_code == 200   # ADR-033: toàn bảng
    base=f'/bang-tinh/{destination.code}/'
    cells=lambda row:[{'id':row.pk,'column':'ghi_chu','old':row.data.get('ghi_chu'),'value':'đã kiểm tra'}]
    assert client.post(base+'luu-json/',{'operation':str(uuid.uuid4()),'cells':cells(a.record)},content_type='application/json').status_code == 200
    assert client.post(base+'luu-json/',{'operation':str(uuid.uuid4()),'cells':cells(b.record)},content_type='application/json').status_code == 200
    kind, book=export_service.export(staff,destination,QueryDict(),builder='grid')
    assert book.active.max_row == 3
