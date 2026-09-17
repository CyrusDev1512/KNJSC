"""Đọc một khối theo vai trò, chỉ trên DB kiểm tải đang được pytest sở hữu."""
import json
import time
from pathlib import Path
from django.contrib.auth import get_user_model
from django.db import connection
from django.http import QueryDict
from django.urls import set_urlconf
from crm.services.master_grid_service import table_for, block

assert connection.settings_dict['NAME'].startswith('test_knjsc_master_capacity_nine')
set_urlconf('knjsc.urls_bangtinh')
with connection.cursor() as cursor:
    cursor.execute('SET max_parallel_workers_per_gather=0')
result = []
for index in (0, 1, 2, 4):
    user = get_user_model().objects.select_related('profile__department').get(username=f'nine_capacity_{index}')
    queries = []
    def capture(execute, sql, params, many, context):
        start = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            queries.append({'ms': (time.perf_counter()-start)*1000, 'sql': sql})
    with connection.execute_wrapper(capture):
        table = table_for(user, 'van_don_moi')
        data = block(user, table, QueryDict('offset=1000'))
    result.append({'role_index': index, 'total': data['total'], 'queries': queries})
Path('/evidence/query-profile.json').write_text(json.dumps(result, indent=2))
print([(r['role_index'], len(r['queries']), round(sum(q['ms'] for q in r['queries']))) for r in result])
