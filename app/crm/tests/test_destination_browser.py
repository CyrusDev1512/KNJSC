"""Chrome host dùng database do pytest tạo; không seed môi trường vận hành."""
import json
import os
import time
from pathlib import Path
import pytest
from .test_waybill_feedback import feedback
from .test_order_destination import destination

@pytest.mark.trinh_duyet
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(os.environ.get('ORDER_DESTINATION_BROWSER') != '1', reason='Cần Chrome host riêng')
def test_destination_browser(live_server, feedback, destination, nguoi_dung, settings):
    from django.db import connection
    from orders.models import Order
    assert connection.settings_dict['NAME'].startswith('test_')
    settings.DEBUG=True
    settings.ALLOWED_HOSTS=['*']
    out=Path('/evidence')
    result=out/'browser-result.json'
    result.unlink(missing_ok=True)
    ready=out/'browser-ready.json'
    ready.write_text(json.dumps({'old':feedback[0].pk,'destination':destination.pk,'code':destination.code,'product':feedback[1][0].code}))
    try:
        until=time.monotonic()+240
        while not result.exists() and time.monotonic()<until:
            time.sleep(.2)
        assert result.exists(), 'Chrome chưa trả kết quả'
        assert json.loads(result.read_text())['ok']
        assert Order.objects.filter(customer__name__startswith='Destination Chrome',record__table=destination).count()==2
    finally:
        ready.unlink(missing_ok=True)
