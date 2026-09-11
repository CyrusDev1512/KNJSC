"""Lên đơn: chọn rõ quốc gia, tiền tệ và phương thức thanh toán."""
import pytest
import re
from orders.models import Order, WaybillItem
from .test_waybill_new import setup, form_data, ENTRY

pytestmark = pytest.mark.django_db
FIELDS = ("market", "currency", "payment_method")


def assert_empty_choices(response):
    for name in FIELDS:
        markup = str(response.context["form"][name])
        options = re.findall(r"<option\b([^>]*)>", markup)
        selected = next((option for option in options if "selected" in option), options[0])
        assert 'value=""' in selected, name
        assert " required" in markup, name



@pytest.mark.parametrize("role", ["staff_sale_1", "admin"])
def test_initial_and_next_order_require_explicit_choices(client, setup, nguoi_dung, role):
    client.force_login(nguoi_dung[role])
    assert_empty_choices(client.get(ENTRY))
    response = client.post(ENTRY, form_data(setup[2]))
    assert response.status_code == 200 and Order.objects.count() == 1
    assert_empty_choices(response)


@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize("value", [None, "", "INVALID"])
def test_missing_or_invalid_choice_cannot_create_order(client, setup, nguoi_dung, field, value):
    client.force_login(nguoi_dung["staff_sale_1"])
    data = form_data(setup[2])
    if value is None:
        del data[field]
    else:
        data[field] = value
    response = client.post(ENTRY, data)
    assert response.status_code == 400
    assert field in response.context["form"].errors
    assert not Order.objects.exists() and not WaybillItem.objects.exists()
    for other in FIELDS:
        if other != field:
            assert response.context["form"][other].value() == data[other]
