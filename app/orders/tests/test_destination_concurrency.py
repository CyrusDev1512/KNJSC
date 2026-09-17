"""Tái sử dụng oracle 30 Sale cho bảng nhận đơn cấu hình."""
import pytest
from .test_len_don import bang_van_don, san_pham
from .test_order_code_concurrency import test_thirty_sales_keep_orders_and_snapshots_complete as check_thirty

@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('same_customer', [False, True])
def test_thirty_orders_reach_selected_destination(bang_van_don, san_pham, departments, make_user, nguoi_dung, same_customer):
    from orders.services import destination_service, waybill_db_service
    from orders.models import Order
    target=waybill_db_service.ensure_table(actor=nguoi_dung['admin'])
    destination_service.configure(nguoi_dung['admin'],target.pk)
    check_thirty(target,san_pham,departments,make_user,same_customer)
    assert Order.objects.filter(record__table=target).count()==30
