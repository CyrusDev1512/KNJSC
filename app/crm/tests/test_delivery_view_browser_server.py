"""Máy chủ E2E riêng cho Chrome host; không dùng database đang vận hành."""
import json
import os
import time
from pathlib import Path
import pytest
from core.constants import Rank
from .test_waybill_feedback import feedback, delivery_leader, assign_rows


@pytest.mark.trinh_duyet
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(os.environ.get('KN_VIEW_BROWSER') != '1', reason='Cần Chrome host và DB test riêng')
def test_delivery_view_browser(live_server, feedback, delivery_leader, nguoi_dung, make_user, departments, settings):
    from django.db import connection
    assert connection.settings_dict['NAME'].startswith('test_')
    settings.DEBUG = True
    settings.ALLOWED_HOSTS = ['*']
    make_user('view_manager', Rank.MANAGER, departments['vd'])
    assign_rows(delivery_leader, [feedback[2][0]], delivery=nguoi_dung['staff_vd'].pk)
    folder = Path('/evidence')
    result = folder/'browser-result.json'
    result.unlink(missing_ok=True)
    (folder/'browser-ready.json').write_text(json.dumps({'rows':[r.pk for r in feedback[2]]}))
    try:
        deadline = time.monotonic()+240
        while not result.exists() and time.monotonic()<deadline:
            time.sleep(.2)
        assert result.exists(), 'Chưa có kết quả Chrome'
        outcome = json.loads(result.read_text())
        assert outcome['ok'], outcome
    finally:
        (folder/'browser-ready.json').unlink(missing_ok=True)
