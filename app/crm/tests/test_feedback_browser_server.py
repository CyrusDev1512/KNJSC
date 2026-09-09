"""AC-20.6 — Chrome trên Windows → live_server và database pytest riêng.

Chỉ bật khi chạy scripts/kiem-thu-feedback-ui.cjs song song; không ghi DB dev.
"""
import json
import os
import time
from pathlib import Path

import pytest

from .test_waybill_feedback import feedback, delivery_leader  # noqa: F401 — fixtures


@pytest.mark.trinh_duyet
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(os.environ.get('KN_FEEDBACK_BROWSER') != '1', reason='Cần Chrome host và cầu live_server chuyên dụng')
def test_feedback_browser(live_server, feedback, delivery_leader, nguoi_dung, settings):
    settings.DEBUG = True
    settings.ALLOWED_HOSTS = ['*']
    profile = nguoi_dung['staff_mkt'].profile
    profile.full_name = ('Nhân viên Marketing có tên dài ' * 5)[:150]
    profile.save(update_fields=['full_name'])
    from django.db import connection
    assert connection.settings_dict['NAME'].startswith('test_')
    marker = Path('/app/.feedback-browser-ready.json')
    result = Path('/app/.feedback-browser-result.json')
    result.unlink(missing_ok=True)
    try:
        marker.write_text(json.dumps({'rows': [r.pk for r in feedback[2]],
            'delivery': nguoi_dung['staff_vd'].pk, 'care': nguoi_dung['staff_sale_1'].pk,
            'marketing': nguoi_dung['staff_mkt'].pk}), encoding='utf-8')
        deadline = time.monotonic() + 300
        while not result.exists() and time.monotonic() < deadline:
            time.sleep(0.2)
        assert result.exists(), 'Chrome host chưa trả kết quả trong 300 giây'
        outcome = json.loads(result.read_text(encoding='utf-8'))
        assert outcome.get('ok'), outcome
    finally:
        marker.unlink(missing_ok=True)
        result.unlink(missing_ok=True)
