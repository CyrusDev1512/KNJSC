"""AC-21 — Autosave: giao dịch, lịch sử, style và thứ tự không mất dữ liệu."""
import uuid
import pytest
from .test_waybill_feedback import feedback, delivery_leader, assign_rows
from .test_master_grid import BASE, write

pytestmark = pytest.mark.django_db


def post(client, cells, operation=None):
    return client.post(BASE+'luu-json/', {'operation': operation or str(uuid.uuid4()),
                       'cells': cells}, content_type='application/json')


def test_chronological_default(client, feedback, nguoi_dung):
    client.force_login(nguoi_dung['admin'])
    assert [r['id'] for r in client.get(BASE+'du-lieu/').json()['rows']] == sorted(r.pk for r in feedback[2])


def test_history_replay_and_scope(client, feedback, nguoi_dung, delivery_leader):
    row = feedback[2][0]
    client.force_login(nguoi_dung['admin'])
    op = str(uuid.uuid4())
    assert write(client, row, old=row.data.get('ghi_chu'), operation=op).status_code == 200
    assert write(client, row, old=row.data.get('ghi_chu'), operation=op).status_code == 200
    url = BASE+f'lich-su/?record={row.pk}'
    response = client.get(url)
    assert response.status_code == 200
    items = response.json()['items']
    assert len(items) == 1 and items[0]['after'] == 'Ghi chú mới'
    assign_rows(delivery_leader, [row], delivery=nguoi_dung['staff_vd'].pk)
    client.force_login(nguoi_dung['staff_vd'])
    assert client.get(url).status_code == 200
    assign_rows(delivery_leader, [row], delivery=None)
    assert client.get(url).status_code in (403, 404)


def test_history_does_not_load_full_receipt_result(client, feedback, nguoi_dung):
    """AC-21.10: lịch sử 50 ô không kéo 50 bản kết quả dán cả nghìn dòng."""
    from django.db import connection
    from django.test.utils import CaptureQueriesContext
    client.force_login(nguoi_dung['admin'])
    row = feedback[2][0]
    assert write(client, row, old=row.data.get('ghi_chu')).status_code == 200
    with CaptureQueriesContext(connection) as queries:
        response = client.get(BASE+f'lich-su/?record={row.pk}')
    assert response.status_code == 200
    assert response.json()['items'][0]['kind'] == 'edit'
    assert not any(', "crm_gridmutationreceipt"."result",' in q['sql'] for q in queries)


def test_table_specific_scope_matches_general_scope(feedback, nguoi_dung, delivery_leader):
    """AC-21.4/6: tối ưu truy vấn không đổi tập dòng được phép."""
    from forms_builder.models import DataRecord, TableDef
    table, _, rows = feedback
    assign_rows(delivery_leader, [rows[0]], delivery=nguoi_dung['staff_vd'].pk,
                care=nguoi_dung['staff_sale_1'].pk)
    for user in [*nguoi_dung.values(), delivery_leader]:
        for target in TableDef.objects.all():
            expected = set(DataRecord.objects.in_scope(user).filter(table=target).values_list('pk', flat=True))
            actual = set(DataRecord.objects.in_scope(user, table=target).values_list('pk', flat=True))
            assert actual == expected
    # Quyền mở bảng qua dòng được giao chỉ cần một dòng tồn tại, không lấy mọi ID.
    assert 'EXISTS' in str(TableDef.objects.in_scope(nguoi_dung['staff_sale_1']).query)


@pytest.mark.parametrize('code', ['ma_don', 'quoc_gia'])
def test_exact_json_filter_uses_existing_gin_and_keeps_results(feedback, nguoi_dung, code):
    """AC-21.6: thu hẹp ứng viên bằng GIN, vẫn kiểm đúng phép bằng cũ."""
    from django.http import QueryDict
    from forms_builder.models import DataRecord
    from crm.services.grid_service import build_grid
    table, _, rows=feedback
    value=rows[0].data[code]
    params=QueryDict('',mutable=True);params['f_'+code]=value
    qs=build_grid(nguoi_dung['admin'],params,table=table).queryset
    expected=DataRecord.objects.filter(table=table,**{'data__'+code:value})
    assert set(qs.values_list('pk',flat=True))==set(expected.values_list('pk',flat=True))
    assert '@>' in str(qs.query)


@pytest.mark.parametrize('failure,status', [('type',400),('conflict',409)])
def test_one_error_in_two_thousand_cells_rolls_back_everything(client, feedback, nguoi_dung, failure, status):
    """AC-21.3/9: kiểm đúng kích thước giới hạn, không thay bằng lô hai ô."""
    from forms_builder.models import DataRecord
    from crm.models import GridCellHistory, GridMutationReceipt
    user=nguoi_dung['admin'];client.force_login(user)
    rows=DataRecord.objects.bulk_create([DataRecord(table=feedback[0],created_by=user,
        data={'ghi_chu':'Ban đầu','ngay':'2026-01-01'}) for _ in range(1000)])
    cells=[]
    for row in rows:
        cells.extend([{'id':row.pk,'column':'ghi_chu','old':'Ban đầu','value':'Không được ghi'},
                      {'id':row.pk,'column':'ngay','old':'2026-01-01','value':'2026-01-02'}])
    cells[-1]['value' if failure=='type' else 'old']='không hợp lệ'
    operation=str(uuid.uuid4());response=post(client,cells,operation)
    assert response.status_code==status
    ids=[r.pk for r in rows]
    assert DataRecord.objects.filter(pk__in=ids,data__ghi_chu='Ban đầu',data__ngay='2026-01-01').count()==1000
    assert not GridCellHistory.objects.filter(record_id__in=ids).exists()
    assert not GridMutationReceipt.objects.filter(actor=user,operation=operation).exists()


def test_style_cas_merges_properties_and_preserves_value(client, feedback, nguoi_dung):
    client.force_login(nguoi_dung['admin'])
    row = feedback[2][0]
    def cell(prop, old, value):
        return {'id': row.pk, 'column': 'ghi_chu', 'property': prop, 'old': old, 'value': value}
    assert post(client, [cell('fs', None, 18)]).status_code == 200
    assert post(client, [cell('bg', None, 'm01')]).status_code == 200
    conflict = post(client, [cell('fs', None, 20)])
    assert conflict.status_code == 409
    assert conflict.json()['conflicts'][0]['current'] == 18
    row.refresh_from_db()
    assert row.style['ghi_chu'] == {'fs': 18, 'bg': 'm01'}
    assert post(client, [cell('fs', 18, None)]).status_code == 200
    row.refresh_from_db()
    assert row.style['ghi_chu'] == {'bg': 'm01'}


def test_conflict_rolls_back_whole_batch_and_no_history(client, feedback, nguoi_dung):
    client.force_login(nguoi_dung['admin'])
    row = feedback[2][0]
    response = post(client, [
        {'id': row.pk, 'column': 'ghi_chu', 'old': row.data.get('ghi_chu'), 'value': 'Không ghi'},
        {'id': row.pk, 'column': 'bang', 'old': 'stale', 'value': 'Không ghi'}])
    assert response.status_code == 409
    assert response.json()['conflicts'][0]['column'] == 'bang'
    row.refresh_from_db()
    assert row.data.get('ghi_chu') != 'Không ghi'
    assert client.get(BASE+f'lich-su/?record={row.pk}').json()['items'] == []


def test_admin_selects_seller_without_changing_profile(feedback, nguoi_dung):
    from orders.services.order_service import create_order, orders_of
    from forms_builder.models import DataRecord
    admin, seller = nguoi_dung['admin'], nguoi_dung['staff_sale_1']
    before = admin.profile.department_id
    order = create_order(actor=admin, seller=seller, phone='0900000001', customer_name='Kiểm thử Admin',
                         lines=[{'product': feedback[1][0], 'quantity': 1, 'unit_price': '1'}])
    assert order.created_by == admin and order.seller == seller
    assert order.department_id == seller.profile.department_id
    assert orders_of(seller).filter(pk=order.pk).exists()
    assert DataRecord.objects.in_scope(seller).filter(pk=order.record_id).exists()
    admin.profile.refresh_from_db()
    assert admin.profile.department_id == before


def test_admin_form_requires_seller_and_rejects_forgery(client, feedback, nguoi_dung):
    from orders.models import Order
    data={'customer_name':'Khách E2E','phone':'0911111111','market':'USA','currency':'USD',
          'payment_method':'card','product':[feedback[1][0].code],'quantity':['1'],'unit_price':['1'],'paid_amount':['0']}
    # Lấy các giá trị lựa chọn thực tế, không phụ thuộc nhãn hiển thị.
    from orders.constants import Market, PaymentMethod
    data.update(market=Market.US,payment_method=PaymentMethod.CARD)
    client.force_login(nguoi_dung['admin'])
    before=Order.objects.count()
    assert client.post('/van-don/len-don/',data).status_code==400
    data['seller']=nguoi_dung['staff_sale_1'].pk
    assert client.post('/van-don/len-don/',data).status_code==200
    assert Order.objects.count()==before+1
    client.force_login(nguoi_dung['staff_sale_2'])
    assert client.post('/van-don/len-don/',data).status_code==400
    assert Order.objects.count()==before+1


@pytest.mark.parametrize('field,value',[('is_active',False),('department','mkt'),('locked_until','future'),('department_active',False),('department_deleted',True)])
def test_rejects_unavailable_seller(feedback, nguoi_dung, departments, field, value):
    from orders.services.order_service import create_order
    from core.exceptions import BusinessError
    from django.utils import timezone
    from datetime import timedelta
    seller=nguoi_dung['staff_sale_1']
    if field=='is_active':seller.is_active=False;seller.save()
    elif field=='department':seller.profile.department=departments[value];seller.profile.save()
    elif field=='department_active':seller.profile.department.is_active=False;seller.profile.department.save()
    elif field=='department_deleted':seller.profile.department.deleted_at=timezone.now();seller.profile.department.save()
    else:seller.profile.locked_until=timezone.now()+timedelta(hours=1);seller.profile.save()
    from crm.waybill_forms import WaybillOrderForm
    assert not WaybillOrderForm(actor=nguoi_dung['admin']).fields['seller'].queryset.filter(pk=seller.pk).exists()
    with pytest.raises(BusinessError):
        create_order(actor=nguoi_dung['admin'],seller=seller,phone='0912222222',customer_name='Không tạo',lines=[{'product':feedback[1][0],'quantity':1,'unit_price':'1'}])


def test_bad_style_rolls_back_values_and_history(client, feedback, nguoi_dung):
    from crm.models import GridCellHistory, GridMutationReceipt
    client.force_login(nguoi_dung['admin']);row=feedback[2][0]
    r=post(client,[{'id':row.pk,'column':'ghi_chu','old':row.data.get('ghi_chu'),'value':'Không ghi'},
                   {'id':row.pk,'column':'bang','property':'fs','old':None,'value':999}])
    assert r.status_code==400
    row.refresh_from_db();assert row.data.get('ghi_chu')!='Không ghi'
    assert not GridCellHistory.objects.exists() and not GridMutationReceipt.objects.exists()


def test_history_cursor_is_bounded_and_append_only(client, feedback, nguoi_dung):
    from crm.models import GridCellHistory
    client.force_login(nguoi_dung['admin']);row=feedback[2][0];old=row.data.get('ghi_chu')
    for i in range(53):
        assert write(client,row,old=old,value=str(i)).status_code==200
        old=str(i)
    url=BASE+f'lich-su/?record={row.pk}'
    page1=client.get(url).json();page2=client.get(url+'&before='+str(page1['next'])).json()
    assert len(page1['items'])==50 and len(page2['items'])==3 and page2['next'] is None
    assert not {h['id'] for h in page1['items']} & {h['id'] for h in page2['items']}
    with pytest.raises(RuntimeError):GridCellHistory.objects.all().update(after='X')
    with pytest.raises(RuntimeError):GridCellHistory.objects.all().delete()


def test_scope_probe_and_legacy_style_denied(client, feedback, nguoi_dung, delivery_leader):
    row,other=feedback[2]
    assign_rows(delivery_leader,[row],delivery=nguoi_dung['staff_vd'].pk)
    client.force_login(nguoi_dung['staff_vd'])
    r=client.post(BASE+'quyen-dong/',{'ids':[row.pk,other.pk]},content_type='application/json')
    assert r.status_code==200 and r.json()['visible']==[row.pk]
    assert client.post(BASE+'dinh-dang/',{'o':[f'{row.pk}:ghi_chu'],'fs':'18'}).status_code==409


def test_batch_query_count_is_bounded(client, feedback, nguoi_dung):
    from forms_builder.models import DataRecord
    from django.db import connection
    from django.test.utils import CaptureQueriesContext
    rows=DataRecord.objects.bulk_create([DataRecord(table=feedback[0],created_by=nguoi_dung['admin'],data={'ghi_chu':'A'}) for _ in range(25)])
    client.force_login(nguoi_dung['admin'])
    with CaptureQueriesContext(connection) as queries:
        response=post(client,[{'id':r.pk,'column':'ghi_chu','old':'A','value':'B'} for r in rows])
    assert response.status_code==200
    assert len(queries)<60, f'Lưu 25 dòng dùng {len(queries)} truy vấn'


@pytest.mark.django_db(transaction=True)
def test_history_migration_roundtrip_keeps_rows(feedback):
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor
    from forms_builder.models import DataRecord
    ids=set(DataRecord.objects.values_list('pk',flat=True))
    executor=MigrationExecutor(connection)
    try:
        executor.migrate([('crm','0001_initial')])
        assert set(DataRecord.objects.values_list('pk',flat=True))==ids
    finally:
        executor=MigrationExecutor(connection);executor.migrate(executor.loader.graph.leaf_nodes())
    assert set(DataRecord.objects.values_list('pk',flat=True))==ids


@pytest.mark.django_db(transaction=True)
def test_cover_index_migration_roundtrip_keeps_rows(feedback):
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor
    from forms_builder.models import DataRecord
    ids=set(DataRecord.objects.values_list('pk',flat=True))
    def present():
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_indexes WHERE indexname='record_master_cover_idx'")
            return cursor.fetchone() is not None
    assert present()
    try:
        MigrationExecutor(connection).migrate([('forms_builder','0009_record_updated_phone_idx')])
        assert not present()
        assert set(DataRecord.objects.values_list('pk',flat=True))==ids
    finally:
        executor=MigrationExecutor(connection);executor.migrate(executor.loader.graph.leaf_nodes())
    assert present()
    assert set(DataRecord.objects.values_list('pk',flat=True))==ids
