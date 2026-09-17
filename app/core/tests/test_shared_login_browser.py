"""Chrome HTTPS hai hostname; chỉ khởi tạo dữ liệu trong PostgreSQL test."""
import json
import os
import time
from pathlib import Path
import pytest
from crm.tests.test_waybill_feedback import feedback


class HostRouter:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.urlconf = 'knjsc.urls_bangtinh' if request.get_host().startswith('crm.') else 'knjsc.urls'
        return self.get_response(request)


@pytest.mark.trinh_duyet
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(os.environ.get('SHARED_LOGIN_BROWSER') != '1', reason='Cần Chrome và proxy HTTPS riêng')
def test_shared_login_browser(request, feedback, nguoi_dung, settings):
    from django.db import connection
    from orders.models import Order
    assert connection.settings_dict['NAME'].startswith('test_')
    settings.DEBUG = True
    settings.ALLOWED_HOSTS = ['*']
    settings.SESSION_COOKIE_DOMAIN = 'shared.test'
    settings.CSRF_COOKIE_DOMAIN = 'shared.test'
    settings.SESSION_COOKIE_NAME = 'knjsc_session_v2'
    settings.CSRF_COOKIE_NAME = 'knjsc_csrf_v2'
    settings.SESSION_COOKIE_SECURE = True
    settings.CSRF_COOKIE_SECURE = True
    settings.SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    settings.CSRF_TRUSTED_ORIGINS = ['https://erp.shared.test:8445', 'https://crm.shared.test:8445']
    settings.BANGTINH_URL = 'https://crm.shared.test:8445/'
    settings.MAIN_APP_URL = 'https://erp.shared.test:8445/'
    settings.MIDDLEWARE = ['core.tests.test_shared_login_browser.HostRouter', *settings.MIDDLEWARE]
    request.getfixturevalue('live_server')
    folder = Path('/evidence')
    result = folder / 'browser-result.json'
    result.unlink(missing_ok=True)
    ready = folder / 'browser-ready.json'
    ready.write_text(json.dumps({'product': feedback[1][0].code,
        'otherOrder': Order.objects.get(record=feedback[2][1]).code}))
    try:
        deadline = time.monotonic() + 600
        while not result.exists() and time.monotonic() < deadline:
            time.sleep(.2)
        assert result.exists(), 'Thiếu kết quả Chrome'
        evidence = json.loads(result.read_text())
        assert evidence['ok'], evidence.get('errors')
        orders = list(Order.objects.filter(customer__name__startswith='Shared Login QA ').select_related('seller'))
        assert len(orders) == 16
        for order in orders:
            assert order.total == 25
            assert order.customer.name.endswith(order.seller.username)
    finally:
        ready.unlink(missing_ok=True)
