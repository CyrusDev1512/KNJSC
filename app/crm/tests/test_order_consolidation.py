"""Một cửa lên đơn tại CRM; ERP không giữ đường ghi cũ."""
import pytest
from core.navigation import visible_navigation
from orders.models import Order
from .test_waybill_new import setup, order, form_data

pytestmark = pytest.mark.django_db


def test_erp_navigation_and_legacy_posts(client, nguoi_dung, settings):
    settings.ROOT_URLCONF = 'knjsc.urls'
    settings.BANGTINH_URL = 'http://localhost:8021/'
    user = nguoi_dung['admin']
    client.force_login(user)
    codes = {m['code'] for g in visible_navigation(user) for m in g['items']}
    assert not codes.intersection({'len_don', 'don_hang'})
    for path in ['/len-don/', '/don-hang/']:
        response = client.get(path)
        assert response.status_code == 302
        assert response.url.startswith('http://localhost:8021/')
        assert client.post(path, {}).status_code == 405
    assert "bang" in codes
    assert client.get("/bang/").status_code == 200
    assert not Order.objects.exists()


def test_crm_order_entry_keeps_customer_fields(client, setup, nguoi_dung):
    client.force_login(nguoi_dung['staff_sale_1'])
    data = {**form_data(setup[2]), 'facebook': 'khach-thu',
            'email': 'khach@example.test', 'sub_unit': 'Đơn vị thử'}
    response = client.post('/van-don/len-don/', data)
    assert response.status_code == 200
    saved = Order.objects.get()
    assert saved.customer.facebook == data['facebook']
    assert saved.customer.email == data['email']
    assert saved.sub_unit == data['sub_unit']
    assert saved.record_id


@pytest.mark.parametrize('role,expected', [
    ('staff_sale_1', 200), ('staff_sale_1b', 404), ('staff_sale_2', 404),
    ('leader_sale_1', 200), ('leader_sale_2', 404), ('manager_sale', 200),
    ('admin', 200), ('staff_vd', 404),
])
def test_original_order_scope(client, setup, nguoi_dung, role, expected):
    saved = order(setup, nguoi_dung['staff_sale_1'])
    client.force_login(nguoi_dung[role])
    response = client.get(f'/van-don/don-goc/{saved.code}/')
    assert response.status_code == expected
    if expected == 200:
        assert saved.code in response.content.decode()
        assert 'KN CRM' in response.content.decode()
        assert client.post(f'/van-don/don-goc/{saved.code}/', {}).status_code == 405


def test_original_order_link_respects_scope(client, setup, nguoi_dung):
    saved = order(setup, nguoi_dung['staff_sale_1'])
    client.force_login(nguoi_dung['admin'])
    page = client.get(f'/van-don/chi-tiet/{saved.record_id}/')
    assert f'/van-don/don-goc/{saved.code}/' in page.content.decode()
    client.force_login(nguoi_dung['staff_vd'])
    page = client.get(f'/van-don/chi-tiet/{saved.record_id}/')
    assert page.status_code == 200
    assert '/van-don/don-goc/' not in page.content.decode()


def test_preview_uses_decimal_without_creating_order(client, setup, nguoi_dung):
    client.force_login(nguoi_dung['staff_sale_1'])
    response = client.post('/van-don/len-don/tom-tat/', form_data(setup[2]))
    assert response.status_code == 200
    assert response.json() == {'lines': 2, 'quantity': 4, 'total': '40.40', 'currency': 'USD'}
    assert not Order.objects.exists()
    invalid = {**form_data(setup[2]), 'quantity': ['0', '1']}
    assert client.post('/van-don/len-don/tom-tat/', invalid).status_code == 400
    client.force_login(nguoi_dung['staff_vd'])
    assert client.post('/van-don/len-don/tom-tat/', form_data(setup[2])).status_code == 403


def test_creator_can_cancel_original_order(client, setup, nguoi_dung):
    saved = order(setup, nguoi_dung['staff_sale_1'])
    client.force_login(nguoi_dung['staff_sale_1'])
    response = client.post(f'/van-don/don-goc/{saved.code}/bo/')
    assert response.status_code == 302 and response.url == '/thu-muc/'
    assert not Order.objects.filter(pk=saved.pk).exists()
    saved.record.refresh_from_db()
    assert saved.record.deleted_at is not None
