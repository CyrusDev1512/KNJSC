"""Admin chọn bảng có placeholder, Sale lưu đơn bằng Chrome trên DB riêng."""
import json
import os
import time
from pathlib import Path
import pytest
from .test_waybill_feedback import feedback
from .test_order_destination import destination
from .test_prepare_destination import populated


@pytest.mark.trinh_duyet
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(os.environ.get('DESTINATION_PREPARE_BROWSER') != '1', reason='Cần Chrome host')
def test_prepare_destination_chrome(request, settings, feedback, destination, populated, nguoi_dung):
    from django.db import connection
    from orders.models import Order
    from orders.services import destination_service
    assert connection.settings_dict['NAME'].startswith('test_')
    destination_service.prepare_existing(nguoi_dung['admin'], destination.pk, expected_rows=1)
    settings.DEBUG = True
    settings.ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']
    request.getfixturevalue('live_server')
    folder = Path('/evidence')
    result = folder / 'browser-result.json'
    result.unlink(missing_ok=True)
    ready = folder / 'browser-ready.json'
    ready.write_text(json.dumps({'destination': destination.pk, 'original': feedback[0].pk,
                                'product': feedback[1][0].code}))
    try:
        deadline = time.monotonic() + 300
        while not result.exists() and time.monotonic() < deadline:
            time.sleep(.2)
        assert result.exists(), 'Thiếu kết quả Chrome'
        evidence = json.loads(result.read_text())
        assert evidence['ok'], evidence
        orders = list(Order.objects.filter(customer__name__startswith='Prepare QA ').select_related('record', 'seller'))
        assert len(orders) == 2
        assert all(o.record.table_id == destination.pk and o.total == 25 and
                   o.seller.username == 'staff_sale_1' for o in orders)
        populated.refresh_from_db()
        assert populated.data == {'ma_don': 'PLACEHOLDER-1', 'ghi_chu': 'giữ nguyên'}
        assert destination_service.current().pk == feedback[0].pk
    finally:
        ready.unlink(missing_ok=True)
