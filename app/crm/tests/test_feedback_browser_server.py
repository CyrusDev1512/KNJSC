"""AC-20.6 — Lệnh kiểm feedback cũ chuyển sang bộ kiểm lưới master ADR-021."""
import os
import pytest
from .test_waybill_feedback import feedback, delivery_leader
from .test_master_browser_server import test_master_browser as run_master_browser


@pytest.mark.trinh_duyet
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(os.environ.get('KN_FEEDBACK_BROWSER') != '1', reason='Cần Chrome host / DB test riêng')
def test_feedback_browser(live_server, feedback, delivery_leader, nguoi_dung, settings):
    run_master_browser(live_server, feedback, delivery_leader, nguoi_dung, settings)
