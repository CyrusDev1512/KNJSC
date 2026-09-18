"""Tái hiện đổi token bởi đơn mới ngoài phạm vi Vận đơn; chỉ DB test riêng."""
import json
import uuid
from pathlib import Path
import django

django.setup()
from django.db import connection
from django.contrib.auth import get_user_model
from django.test import Client, override_settings
from orders.services import order_service
from forms_builder.models import DataRecord

assert connection.settings_dict["NAME"] == "test_knjsc_gridflags_load"
assert connection.settings_dict["HOST"] == "knjsc-gridflags-db"
root = Path("/runtime")
ready = json.loads((root / "ready.json").read_text())
actor = next(u for u in ready["users"] if u["role"] == "delivery" and u["index"] == 9)
sale = next(u for u in ready["users"] if u["role"] == "sale" and u["index"] == 0)
client = Client()
client.cookies["sessionid"] = actor["session"]
url = "/bang-tinh/van_don/du-lieu/"
with override_settings(CRM_OPT_READ=True):
    before_v1 = client.get(url, {"protocol": "1"}).json()
    before_v2 = client.get(url, {"protocol": "2"}).json()
    order = order_service.create_order(
        actor=get_user_model().objects.get(pk=sale["id"]), phone="08" + uuid.uuid4().hex[:14],
        customer_name="Khach TEST token", market="us", payment_method="zelle",
        lines=[{"product": ready["products"][0], "quantity": 1, "unit_price": "10.10"}],
    )
    staff = get_user_model().objects.get(pk=actor["id"])
    assert not DataRecord.objects.in_scope(staff).filter(pk=order.record_id).exists()
    v1 = client.get(url, {"protocol": "1", "version": before_v1["version"]})
    v2 = client.get(url, {"protocol": "2", "query_token": before_v2["query_token"]})
    fresh = client.get(url, {"protocol": "2"}).json()
    result = {
        "new_order_outside_delivery_scope": True, "v1_status": v1.status_code,
        "v2_old_token_status": v2.status_code, "total_unchanged": fresh["total"] == before_v2["total"],
        "first_block_ids_unchanged": [r["id"] for r in fresh["rows"]] == [r["id"] for r in before_v2["rows"]],
    }
(root / "results/invalidation-audit.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result))
