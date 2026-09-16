"""Audit hợp đồng đọc giữa các cờ trên database kiểm thử riêng, không sửa dữ liệu."""
import json
from pathlib import Path
import django

django.setup()
from django.db import connection
from django.test import Client, override_settings

assert connection.settings_dict["NAME"] == "test_knjsc_gridflags_load"
assert connection.settings_dict["HOST"] == "knjsc-gridflags-db"
root = Path("/runtime")
ready = json.loads((root / "ready.json").read_text())
actors = [u for u in ready["users"] if u["role"] == "admin" or u["role"] == "delivery" and u["index"] == 0]
result = []
for actor in actors:
    client = Client()
    client.cookies["sessionid"] = actor["session"]
    base = "/bang-tinh/van_don_moi/"
    with override_settings(CRM_OPT_READ=False, CRM_OPT_SYNC=False, CRM_OPT_RECEIPTS=False):
        reference = client.get(base + "du-lieu/").json()
    for name, read, sync in [("off", False, False), ("render", False, False), ("read", True, False), ("sync", True, True)]:
        with override_settings(CRM_OPT_READ=read, CRM_OPT_SYNC=sync, CRM_OPT_RENDER=name == "render", CRM_OPT_RECEIPTS=False):
            response = client.get(base + "du-lieu/", {"protocol": "2" if read else "1"})
            data = response.json()
            errors = []
            for key in ["capabilities", "schema_version", "total", "columns"]:
                if data.get(key) != reference.get(key):
                    errors.append("different_or_missing:" + key)
            if [r["id"] for r in data["rows"]] != [r["id"] for r in reference["rows"]]:
                errors.append("different_row_scope_or_order")
            if sync:
                own = [r["id"] for r in data["rows"]]
                response_sync = client.post(base + "dong-bo/", {"query_token": data["query_token"], "revision": data["revision"], "ids": own, "visible": own}, content_type="application/json")
                if response_sync.status_code != 200 or response_sync.json().get("reset"):
                    errors.append("unexpected_sync_reset")
            result.append({"actor_role": actor["role"], "variant": name, "status": response.status_code,
                           "capabilities": data.get("capabilities"), "schema_present": "schema_version" in data,
                           "total": data["total"], "errors": errors})
(root / "results/flag-contract.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result))
