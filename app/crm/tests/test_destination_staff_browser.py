"""Phiên Chrome Admin/Sale độc lập; DB xác nhận sau thao tác UI."""
import json
import os
import time
from decimal import Decimal
from pathlib import Path
import pytest
from .test_waybill_feedback import feedback
from .test_order_destination import destination

@pytest.mark.trinh_duyet
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(os.environ.get("ORDER_DESTINATION_BROWSER") != "1", reason="Cần Chrome host riêng")
def test_admin_switch_staff_submit(live_server, feedback, destination, nguoi_dung, settings):
    from django.db import connection
    from orders.models import Order
    assert connection.settings_dict["NAME"].startswith("test_")
    settings.DEBUG = True
    settings.ALLOWED_HOSTS = ["*"]
    out = Path("/evidence")
    result = out / "staff-result.json"
    ready = out / "staff-ready.json"
    result.unlink(missing_ok=True)
    ready.write_text(json.dumps({"old": feedback[0].pk, "oldCode": feedback[0].code,
        "destination": destination.pk, "code": destination.code, "product": feedback[1][0].code}))
    try:
        until = time.monotonic() + 240
        while not result.exists() and time.monotonic() < until:
            time.sleep(.2)
        assert result.exists(), "Chrome chưa trả kết quả"
        evidence = json.loads(result.read_text())
        assert evidence["ok"], evidence
        assert len(evidence["orders"]) == 8
        for case in evidence["orders"]:
            order = Order.objects.select_related("record", "seller").get(customer__name=case["name"])
            assert order.record.table_id == case["table"]
            assert order.seller.username == case["seller"]
            assert order.created_by_id == order.seller_id
            assert order.total == Decimal("25.00")
            assert order.lines.count() == 1
        assert Order.objects.filter(customer__name__startswith="Staff Flow ").count() == 8
        assert all(row.__class__.objects.get(pk=row.pk).table_id == feedback[0].pk for row in feedback[2])
    finally:
        ready.unlink(missing_ok=True)
