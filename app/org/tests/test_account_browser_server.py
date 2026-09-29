"""Chrome host kiểm giao diện thật; pytest giữ database riêng và kiểm hậu điều kiện."""
import json
import os
import time
from pathlib import Path

import pytest
from django.db import connection

from core.constants import Rank
from org.models import UserProfile


class AccountTestRouter:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.urlconf = "knjsc.urls_bangtinh" if request.get_host().startswith("crm.") else "knjsc.urls"
        return self.get_response(request)


@pytest.mark.trinh_duyet
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(os.environ.get("ACCOUNT_BROWSER") != "1", reason="Cần Chrome host và server test riêng")
def test_account_browser(request, settings, nguoi_dung, make_user, departments):
    assert connection.settings_dict["NAME"].startswith("test_")
    settings.DEBUG = True
    settings.ALLOWED_HOSTS = ["erp.accounts.test", "crm.accounts.test"]
    settings.SESSION_COOKIE_DOMAIN = "accounts.test"
    settings.CSRF_COOKIE_DOMAIN = "accounts.test"
    settings.SESSION_COOKIE_SECURE = False
    settings.CSRF_COOKIE_SECURE = False
    settings.MIDDLEWARE = ["org.tests.test_account_browser_server.AccountTestRouter", *settings.MIDDLEWARE]
    settings.BANGTINH_URL = "http://crm.accounts.test:18047/"
    settings.MAIN_APP_URL = "http://erp.accounts.test:18047/"
    actors = {"leader": nguoi_dung["leader_sale_1"], "manager": nguoi_dung["manager_sale"],
              "ceo": make_user("browser_ceo", Rank.CEO), "admin": nguoi_dung["admin"],
              "staff": nguoi_dung["staff_sale_1"]}
    cases = []
    for width in (1440, 390):
        for role, rank in (("leader", Rank.STAFF), ("manager", Rank.LEADER), ("ceo", Rank.MANAGER), ("admin", Rank.CEO)):
            target = make_user(f"browser_{role}_{width}", rank, departments["sale"],
                               nguoi_dung["staff_sale_1"].profile.team)
            cases.append({"width": width, "role": role, "actor": actors[role].username,
                          "target": target.username, "pk": target.profile.pk})
    request.getfixturevalue("live_server")
    folder = Path("/evidence")
    ready, result = folder / "account-browser-ready.json", folder / "account-browser-result.json"
    result.unlink(missing_ok=True)
    ready.write_text(json.dumps({"cases": cases, "staff": actors["staff"].username,
                                "admin_pk": actors["admin"].profile.pk}))
    try:
        deadline = time.monotonic() + 900
        while not result.exists() and time.monotonic() < deadline:
            time.sleep(.2)
        assert result.exists(), "Chưa có kết quả Chrome"
        outcome = json.loads(result.read_text())
        assert outcome["ok"], outcome
        assert len(outcome["cases"]) == 8
        assert UserProfile.objects.filter(pk__in=[case["pk"] for case in cases], deleted_at__isnull=False).count() == 8
    finally:
        ready.unlink(missing_ok=True)
