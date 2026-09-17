"""Server ERP/CRM cùng database pytest, chỉ bật cho E2E và kiểm tải có giới hạn."""
import json
import os
import subprocess
import time
from pathlib import Path
import pytest
from django.db import connection
from forms_builder.models import FormDef, TableDef
from documents.models import Document, DocumentCategory
from .test_waybill_new import setup, order


@pytest.mark.trinh_duyet
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(os.environ.get('KN_ORDER_HUB_BROWSER') != '1', reason='Cần Chrome host và server DB test')
def test_order_hub_browser(live_server, setup, nguoi_dung, settings):
    database = connection.settings_dict['NAME']
    assert database.startswith('test_')
    settings.ROOT_URLCONF = 'knjsc.urls'
    settings.DEBUG = True
    settings.ALLOWED_HOSTS = ['*']
    settings.BANGTINH_URL = 'http://127.0.0.1:8812/'
    settings.GRID_ONLY_TABLES = set()
    table = TableDef.objects.create(name='Bảng E2E', code='hub_e2e', department=nguoi_dung['staff_sale_1'].profile.department)
    FormDef.objects.bulk_create([FormDef(name=f'Biểu mẫu thử {i:04}', code=f'hub_{i}',
        table=table, department=table.department) for i in range(1000)])
    category = DocumentCategory.objects.create(name='Tài liệu dùng chung')
    Document.objects.bulk_create([Document(title=f'Tài liệu thử {i:04}', category=category,
        created_by=nguoi_dung['admin'], link='https://example.com/') for i in range(1000)])
    saved = order(setup, nguoi_dung['staff_sale_1'])
    child_code = '''
import os
os.environ['DJANGO_SETTINGS_MODULE']='knjsc.settings.test'
import django
django.setup()
from django.conf import settings
settings.ROOT_URLCONF='knjsc.urls_bangtinh'
settings.BANGTINH_URL=''
settings.GRID_ONLY_TABLES=set()
settings.DEBUG=True
settings.ALLOWED_HOSTS=['*']
from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.servers.basehttp import ThreadedWSGIServer, WSGIRequestHandler
server=ThreadedWSGIServer(('0.0.0.0',8812),WSGIRequestHandler)
server.set_app(StaticFilesHandler(get_wsgi_application()))
server.serve_forever()
'''
    env = {**os.environ, 'POSTGRES_DB': database}
    process = subprocess.Popen(['python', '-c', child_code], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    signal = Path('/app/.order-hub-ready.json')
    result = Path('/app/.order-hub-result.json')
    result.unlink(missing_ok=True)
    try:
        signal.write_text(json.dumps({'database': database, 'order': saved.code,
            'row': saved.record_id, 'products': [p.code for p in setup[2]]}), encoding='utf-8')
        end = time.monotonic() + 900
        while not result.exists() and time.monotonic() < end:
            assert process.poll() is None, 'Server CRM dừng ngoài dự kiến'
            time.sleep(.25)
        assert result.exists(), 'Chưa có kết quả Chrome/Locust'
        outcome = json.loads(result.read_text(encoding='utf-8'))
        assert outcome.get('ok'), outcome
    finally:
        process.terminate()
        process.wait(timeout=15)
        signal.unlink(missing_ok=True)
        result.unlink(missing_ok=True)
