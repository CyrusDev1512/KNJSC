"""Chrome: loại tiền cố định, xác nhận đổi quốc gia, hai phương thức thanh toán."""
import json
import os
import time
from pathlib import Path
import pytest
from .test_waybill_feedback import feedback


@pytest.mark.trinh_duyet
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(os.environ.get('MARKET_CURRENCY_BROWSER') != '1', reason='Cần Chrome host')
def test_market_currency_chrome(request, settings, feedback, nguoi_dung):
    from django.db import connection
    from orders.models import Order
    assert connection.settings_dict['NAME'].startswith('test_')
    settings.DEBUG = True
    settings.ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']
    for row in feedback[2]:
        row.data['pttt_thuc_te'] = 'Thẻ'
        row.save(update_fields=['data'])
    request.getfixturevalue('live_server')
    folder = Path('/evidence'); result = folder/'browser-result.json'; ready = folder/'browser-ready.json'
    result.unlink(missing_ok=True)
    ready.write_text(json.dumps({'table':feedback[0].code, 'product':feedback[1][0].code,
                                'codes':[r.data['ma_don'] for r in feedback[2]]}))
    try:
        deadline = time.monotonic() + 420
        while not result.exists() and time.monotonic() < deadline:
            time.sleep(.2)
        assert result.exists(), 'Thiếu bằng chứng Chrome'
        evidence = json.loads(result.read_text()); assert evidence['ok'], evidence
        orders = list(Order.objects.filter(customer__name__startswith='Currency QA ').select_related('record'))
        assert len(orders) == 2
        assert all(o.currency == 'PHP' and o.payment_method == 'paypal' and o.total == 25 for o in orders)
        for row in feedback[2]:
            row.refresh_from_db()
            assert row.data['quoc_gia'] == 'Canada' and row.data['loai_tien'] == 'CAD'
            assert row.data['gia_tien'] == '10.00' and row.data['pttt_thuc_te'] == 'PayPal'
            assert row.order.currency == 'USD'
    finally:
        ready.unlink(missing_ok=True)
