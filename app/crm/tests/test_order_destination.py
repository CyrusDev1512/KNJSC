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

def test_candidates_list_every_waybill_table(client, feedback, destination, departments, nguoi_dung):
    """AC-11.39 — Bảng nhận đơn liệt kê mọi bảng vận đơn đang có (ADR-034): bảng cũ `van_don`, bảng đang nhận,
    bảng của bộ phận Vận đơn có cột Mã đơn đúng cấu trúc; bảng báo cáo cùng bộ phận và bảng bộ phận khác không hiện;
    bảng chưa đủ điều kiện hiện kèm lý do, không chọn được"""
    from forms_builder.meaning import FieldType, Meaning
    from forms_builder.models import ColumnDef, TableDef
    from orders.constants import WAYBILL_TABLE_CODE
    from orders.services import destination_service
    old = TableDef.objects.filter(code=WAYBILL_TABLE_CODE).first() or TableDef.objects.create(
        name='Vận đơn mới', code=WAYBILL_TABLE_CODE, department=departments['vd'], created_by=nguoi_dung['admin'])
    bao_cao = TableDef.objects.create(name='Báo cáo ngày VD', code='bao_cao_vd_ngay', department=departments['vd'], created_by=nguoi_dung['admin'])
    ColumnDef.objects.create(table=bao_cao, name='Ngày', code='ngay', field_type=FieldType.DATE, meaning=Meaning.DATE, order=0)
    khac = TableDef.objects.create(name='Bảng Sale', code='bang_sale_khac', department=departments['sale'], created_by=nguoi_dung['admin'])
    ColumnDef.objects.create(table=khac, name='Mã đơn', code='ma_don', field_type=FieldType.TEXT, meaning='', order=0)
    rows = {table.code: reason for table, reason in destination_service.candidates()}
    assert set(rows) == {feedback[0].code, destination.code, WAYBILL_TABLE_CODE}
    assert rows[feedback[0].code] == '' and rows[destination.code] == ''
    assert rows[WAYBILL_TABLE_CODE] != ''            # bảng cũ hiện ra nhưng chưa đủ cấu trúc để chọn
    client.force_login(nguoi_dung['admin'])
    assert client.post(URL, {'table': old.pk}).status_code == 400
    page = client.get(URL)
    assert page.status_code == 200
    html = page.content.decode()
    assert 'Vận đơn mới' in html and 'Báo cáo ngày VD' not in html and 'Bảng Sale' not in html


def test_prepare_upgrades_legacy_schema_then_selectable(feedback, departments, nguoi_dung):
    """AC-11.39 — Bảng cũ thiếu cấu trúc chuẩn (cột chữ tự do thay vì danh sách, thiếu cột) được
    `prepare_existing` bổ sung: thêm cột thiếu, đổi chữ → danh sách kèm lựa chọn chuẩn, giữ nguyên dòng và
    giá trị cũ; sau đó đủ điều kiện và chọn được làm bảng nhận đơn; Staff/Leader/Manager bị từ chối"""
    from core.exceptions import OutOfScopeError
    from forms_builder.meaning import FieldType
    from forms_builder.models import ColumnDef, DataRecord, TableDef
    from orders.constants import WAYBILL_TABLE_CODE
    from orders.services import destination_service, waybill_service
    old = TableDef.all_objects.filter(code=WAYBILL_TABLE_CODE).first() or TableDef.objects.create(
        name='Vận đơn mới', code=WAYBILL_TABLE_CODE, department=departments['vd'], created_by=nguoi_dung['admin'])
    old.columns.all().delete()          # mô phỏng bảng cũ thiếu cấu trúc chuẩn
    TableDef.all_objects.filter(pk=old.pk).update(workflow='', receives_orders=False)
    old.refresh_from_db()
    skip = {'pttt_thuc_te', 'phu_trach_vd', 'phu_trach_mkt'}
    for i, (label, code, kind, meaning) in enumerate(waybill_service.COLUMNS):
        if code in skip:
            continue
        loose = code in ('loai_tien', 'pttt')
        ColumnDef.objects.create(table=old, name=label, code=code, order=i, meaning=meaning,
                                 field_type=FieldType.TEXT if loose else kind,
                                 options=[] if loose else list(waybill_service.OPTIONS.get(code) or []))
    row = DataRecord.objects.create(table=old, department=old.department, created_by=nguoi_dung['admin'],
                                    data={'ma_don': 'CU-1', 'ten_khach': 'Khách cũ', 'loai_tien': 'usd', 'pttt': 'Tiền mặt'})
    assert destination_service.eligibility(old) != ''
    for role in ('staff_vd', 'leader_sale_1', 'manager_sale'):
        with pytest.raises(OutOfScopeError):
            destination_service.prepare_existing(nguoi_dung[role], old.pk, expected_rows=1)
    destination_service.prepare_existing(nguoi_dung['admin'], old.pk, expected_rows=1)
    old.refresh_from_db()
    assert destination_service.eligibility(old) == '' and old.workflow == 'waybill'
    assert set(old.columns.values_list('code', flat=True)) >= {c[1] for c in waybill_service.COLUMNS}
    loai_tien = old.columns.get(code='loai_tien')
    assert loai_tien.field_type == FieldType.CHOICE and set(waybill_service.OPTIONS['loai_tien']) <= set(loai_tien.options)
    row.refresh_from_db()
    assert row.data['loai_tien'] == 'usd' and row.data['pttt'] == 'Tiền mặt', 'giá trị cũ không bị sửa'
    assert DataRecord.all_objects.filter(table=old).count() == 1
    destination_service.configure(nguoi_dung['admin'], old.pk)
    assert destination_service.current().pk == old.pk
