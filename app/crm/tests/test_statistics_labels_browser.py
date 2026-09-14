"""Fixture Chrome riêng cho lỗi CSS/nhãn Thống kê; không dùng DB vận hành."""
import json
import os
import subprocess
import time
from pathlib import Path

import pytest
from django.db import connection
from .test_waybill_feedback import feedback
from .test_executive_statistics import executive_tables


@pytest.mark.trinh_duyet
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(os.environ.get("STAT_LABEL_BROWSER") != "1", reason="Cần Chrome host và DB test riêng")
def test_statistics_labels_browser(feedback, executive_tables, nguoi_dung):
    database = connection.settings_dict["NAME"]
    assert database.startswith("test_")
    ready = Path("/storage/statistics-label-ready.json")
    result = Path("/storage/statistics-label-result.json")
    result.unlink(missing_ok=True)
    code = """
import os
os.environ['DJANGO_SETTINGS_MODULE']='knjsc.settings.test'
import django
django.setup()
from django.conf import settings
settings.ROOT_URLCONF='knjsc.urls_bangtinh'
settings.BANGTINH_URL=''
settings.DEBUG=True
settings.ALLOWED_HOSTS=['*']
from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.servers.basehttp import ThreadedWSGIServer, WSGIRequestHandler
server=ThreadedWSGIServer(('0.0.0.0',8812),WSGIRequestHandler)
server.set_app(StaticFilesHandler(get_wsgi_application()))
server.serve_forever()
"""
    process = subprocess.Popen(["python", "-c", code], env={**os.environ, "POSTGRES_DB": database},
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ready.write_text(json.dumps({"database": database}), encoding="utf-8")
        deadline = time.monotonic() + 300
        while not result.exists() and time.monotonic() < deadline:
            assert process.poll() is None
            time.sleep(.2)
        assert result.exists(), "Chưa có kết quả Chrome"
        assert json.loads(result.read_text())["ok"]
    finally:
        process.terminate()
        process.wait(timeout=15)
        ready.unlink(missing_ok=True)
        result.unlink(missing_ok=True)
