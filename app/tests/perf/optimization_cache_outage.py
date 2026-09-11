"""Kiểm mất kết nối Redis thật trong process riêng, không ngắt cache của bài tải."""
import json
import os
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'optimization_settings')
import django
django.setup()
from django.conf import settings
from django.core.cache import caches
from django.db import connection
from django.http import QueryDict
from django.contrib.auth import get_user_model
from crm.services import master_grid_service

assert connection.settings_dict['NAME'].startswith('test_knjsc_opt_')
assert settings.CACHES['crm']['LOCATION'] == 'redis://127.0.0.1:1/0'
assert settings.CRM_OPT_READ
try:
    caches['crm'].get('outage-probe')
except Exception as exc:
    error = type(exc).__name__
else:
    raise AssertionError('Redis phải thực sự từ chối kết nối trong phép thử này')
manifest = json.loads(Path(os.environ['OPT_MANIFEST']).read_text())
actor = manifest['actors'][0]
user = get_user_model().objects.get(pk=actor['user'])
table = master_grid_service.table_for(user, 'van_don_moi')
params = QueryDict('', mutable=True)
params.update({'protocol': '2', 'f_ma_don': actor['code']})
data = master_grid_service.block(user, table, params)
assert data['total'] == 1 and [r['id'] for r in data['rows']] == [actor['row']]
result = {'passed': True, 'redis_error': error, 'fallback': 'PostgreSQL', 'oracle': 'ID/order/total'}
Path(os.environ['OPT_RESULT']).write_text(json.dumps(result))
print(json.dumps(result))
