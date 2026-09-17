"""Loại tiền theo quốc gia; xác nhận đổi đơn vị tiền và danh mục thanh toán mới."""
import uuid
from decimal import Decimal
import pytest
from core.exceptions import BusinessError
from crm.services import master_grid_service
from forms_builder.services import record_service
from orders.services import order_service
from orders.models import WaybillItem
from .test_waybill_feedback import feedback

pytestmark = pytest.mark.django_db


def payload(row, column, value, **extra):
    return {'operation': str(uuid.uuid4()), 'cells': [
        {'id': row.pk, 'column': column, 'old': row.data.get(column), 'value': value}], **extra}


@pytest.mark.parametrize('market,currency', [('us','USD'),('ca','CAD'),('ph','PHP')])
def test_order_derives_currency_and_new_payment(feedback, nguoi_dung, market, currency):
    order = order_service.create_order(phone='0987000001', customer_name='Tiền theo quốc gia',
        actor=nguoi_dung['staff_sale_1'], market=market, payment_method='paypal',
        lines=[{'product': feedback[1][0].code, 'quantity': 2, 'unit_price': '12.50'}])
    assert order.currency == currency and order.record.data['loai_tien'] == currency
    assert order.record.data['pttt'] == 'PayPal' and order.total == Decimal('25')


def test_forged_currency_and_retired_payment_rejected(feedback, nguoi_dung):
    args = dict(phone='0987000002', customer_name='Không hợp lệ', actor=nguoi_dung['staff_sale_1'],
                market='ca', lines=[{'product': feedback[1][0].code, 'quantity': 1, 'unit_price': '5'}])
    for extra in [{'currency':'USD','payment_method':'zelle'}, {'payment_method':'card'}]:
        with pytest.raises(BusinessError):
            order_service.create_order(**args, **extra)


def test_grid_confirmation_preserves_amount_and_order_and_history(client, feedback, nguoi_dung):
    table, _, rows = feedback
    row = rows[0]
    client.force_login(nguoi_dung['admin'])
    url = f'/bang-tinh/{table.code}/luu-json/'
    changes = payload(row, 'quoc_gia', 'Canada')
    response = client.post(url, changes, content_type='application/json')
    assert response.status_code == 400
    assert response.json()['code'] == 'currency_confirmation'
    row.refresh_from_db()
    assert row.data['quoc_gia'] == 'Hoa Kỳ'
    changes['currency_confirmations'] = response.json()['currency_confirmations']
    response = client.post(url, changes, content_type='application/json')
    assert response.status_code == 200, response.content
    row.refresh_from_db()
    assert row.data['quoc_gia'] == 'Canada' and row.data['loai_tien'] == 'CAD'
    assert row.data['gia_tien'] == '10.00' and row.order.currency == 'USD'
    assert WaybillItem.objects.get(record=row).unit_price == Decimal('10')
    from crm.models import GridCellHistory
    assert GridCellHistory.objects.filter(record=row, column='loai_tien', before='USD', after='CAD').exists()
    assert client.post(url, changes, content_type='application/json').json()['replayed']


def test_confirmation_expires_after_row_changes(client, feedback, nguoi_dung):
    table, _, rows = feedback
    row = rows[0]; client.force_login(nguoi_dung['admin'])
    url = f'/bang-tinh/{table.code}/luu-json/'
    change = payload(row, 'quoc_gia', 'Canada')
    change['currency_confirmations'] = client.post(url, change, content_type='application/json').json()['currency_confirmations']
    record_service.update_cell(row, 'ghi_chu', 'thay đổi sau xác nhận', actor=nguoi_dung['admin'])
    response = client.post(url, change, content_type='application/json')
    assert response.status_code == 400 and response.json()['code'] == 'currency_confirmation'


def test_currency_locked_and_payment_choices_shared(client, feedback, nguoi_dung):
    table, _, rows = feedback
    meta = {c['code']: c for c in master_grid_service.metadata(table.columns.all())}
    assert meta['loai_tien']['protected']
    assert meta['pttt']['options'] == meta['pttt_thuc_te']['options'] == ['Zelle', 'PayPal']
    client.force_login(nguoi_dung['admin'])
    url = f'/bang-tinh/{table.code}/luu-json/'
    assert client.post(url, payload(rows[0], 'loai_tien', 'CAD'), content_type='application/json').status_code == 400
    assert client.post(url, payload(rows[0], 'pttt', 'PayPal'), content_type='application/json').status_code == 200
    with pytest.raises(BusinessError):
        record_service.update_cell(rows[0], 'quoc_gia', 'Philippines', actor=nguoi_dung['admin'])


def test_confirmation_does_not_bypass_scope(client, feedback, nguoi_dung):
    table, _, rows = feedback
    client.force_login(nguoi_dung['admin'])
    url = f'/bang-tinh/{table.code}/luu-json/'
    change = payload(rows[1], 'quoc_gia', 'Canada')
    change['currency_confirmations'] = client.post(url, change, content_type='application/json').json()['currency_confirmations']
    client.force_login(nguoi_dung['staff_sale_1'])
    assert client.post(url, change, content_type='application/json').status_code == 403


@pytest.mark.parametrize('custom_table', [False, True])
def test_assigned_delivery_can_confirm_on_any_waybill_profile(client, feedback, nguoi_dung, custom_table):
    from orders.models import WaybillAssignment
    table, _, rows = feedback
    if custom_table:
        table.code = 'delivery-custom'
        table.workflow = 'waybill'
        table.save(update_fields=['code', 'workflow'])
    actor = nguoi_dung['staff_vd']
    WaybillAssignment.objects.create(record=rows[0], delivery=actor)
    client.force_login(actor)
    url = f'/bang-tinh/{table.code}/luu-json/'
    change = payload(rows[0], 'quoc_gia', 'Philippines')
    response = client.post(url, change, content_type='application/json')
    assert response.status_code == 400 and response.json()['code'] == 'currency_confirmation'
    change['currency_confirmations'] = response.json()['currency_confirmations']
    assert client.post(url, change, content_type='application/json').status_code == 200
    rows[0].refresh_from_db()
    assert rows[0].data['loai_tien'] == 'PHP'
    # ADR-033: dòng chưa giao cũng sửa được với nhân viên Vận đơn, nên cũng bị hỏi xác nhận đổi tiền.
    other = client.post(url, payload(rows[1], 'quoc_gia', 'Philippines'), content_type='application/json')
    assert other.status_code == 400 and other.json()['code'] == 'currency_confirmation'


@pytest.mark.parametrize('compact', [False, True])
def test_batch_confirmation_and_undo_currency(client, feedback, nguoi_dung, settings, compact):
    from crm.models import GridCellHistory
    table, _, rows = feedback
    client.force_login(nguoi_dung['admin'])
    url = f'/bang-tinh/{table.code}/luu-json/'
    change = {'operation':str(uuid.uuid4()), 'kind':'paste', 'cells':[
        {'id':r.pk, 'column':'quoc_gia', 'old':'Hoa Kỳ', 'value':'Canada'} for r in rows]}
    if compact:
        settings.CRM_OPT_RECEIPTS = True
        change['protocol'] = 2
    response = client.post(url, change, content_type='application/json')
    assert response.status_code == 400
    assert len(response.json()['currency_confirmations']) == 2
    change['currency_confirmations'] = response.json()['currency_confirmations']
    response = client.post(url, change, content_type='application/json')
    assert response.status_code == 200, response.content
    for row in rows:
        row.refresh_from_db(); assert row.data['loai_tien'] == 'CAD'
    assert GridCellHistory.objects.filter(column='loai_tien', after='CAD').count() == 2
    undo = payload(rows[0], 'quoc_gia', 'Hoa Kỳ', kind='undo')
    response = client.post(url, undo, content_type='application/json')
    undo['currency_confirmations'] = response.json()['currency_confirmations']
    assert client.post(url, undo, content_type='application/json').status_code == 200
    rows[0].refresh_from_db(); assert rows[0].data['loai_tien'] == 'USD'


def test_import_derives_currency_and_rejects_mismatch(feedback):
    from orders.services import waybill_service
    values = {'quoc_gia':'canada', 'pttt':'PayPal', 'chi_tiet_sp':[
        {'product':feedback[1][0].code, 'quantity':1, 'unit_price':'10'}]}
    assert waybill_service.prepare_values(values)['loai_tien'] == 'CAD'
    with pytest.raises(BusinessError, match='Loại tiền'):
        waybill_service.prepare_values({**values, 'loai_tien':'USD'})


def test_form_ignores_forged_currency_but_requires_active_payment(feedback, nguoi_dung):
    from crm.waybill_forms import WaybillOrderForm
    data = {'customer_name':'Form QA', 'phone':'0909988776', 'market':'ph',
            'currency':'VND', 'payment_method':'zelle'}
    form = WaybillOrderForm(data, actor=nguoi_dung['staff_sale_1'])
    assert form.is_valid(), form.errors
    assert form.cleaned_data['currency'] == 'PHP'
    assert form.fields['currency'].widget.attrs['readonly']
    assert not WaybillOrderForm({**data,'payment_method':'card'}).is_valid()


def test_zero_money_changes_without_confirmation_and_old_payment_stays(feedback, nguoi_dung):
    row = feedback[2][0]
    row.data.update(gia_tien='0', so_tien_tt='0', pttt='Thẻ')
    row.save()
    row.waybill_items.update(unit_price=0, paid_amount=0)
    record_service.update_cell(row, 'quoc_gia', 'Canada', actor=nguoi_dung['admin'])
    row.refresh_from_db()
    assert row.data['loai_tien'] == 'CAD' and row.data['pttt'] == 'Thẻ'
