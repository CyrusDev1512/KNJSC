"""Đọc thời gian/hàng đợi test, không đưa nội dung job hoặc phiên đăng nhập ra evidence."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'optimization_settings')
import django
django.setup()
from django.db import connection
from core.models import BackgroundJob

assert connection.settings_dict['NAME'].startswith('test_knjsc_opt_')
start = datetime.fromtimestamp(float(os.environ['OPT_SINCE']), timezone.utc)
now = datetime.now(timezone.utc)
rows = list(BackgroundJob.objects.filter(created_at__gte=start).values(
    'status', 'created_at', 'started_at', 'finished_at'))


def summary(values):
    values = sorted(values)
    if not values:
        return {'n': 0}
    import math
    return {'n': len(values), **{label: values[min(len(values)-1, math.ceil(len(values)*q)-1)]
                               for label, q in [('p50', .5), ('p95', .95), ('p99', .99)]},
            'max': values[-1]}


result = {
    'database': connection.settings_dict['NAME'], 'since': start.isoformat(), 'at': now.isoformat(),
    'status': {status: sum(row['status'] == status for row in rows)
               for status in sorted({row['status'] for row in rows})},
    'queue_seconds': summary([(row['started_at']-row['created_at']).total_seconds()
                              for row in rows if row['started_at']]),
    'execution_seconds': summary([(row['finished_at']-row['started_at']).total_seconds()
                                  for row in rows if row['finished_at'] and row['started_at']]),
    'file_ready_seconds': summary([(row['finished_at']-row['created_at']).total_seconds()
                                   for row in rows if row['status'] == 'done' and row['finished_at']]),
    'pending_age_seconds': summary([(now-row['created_at']).total_seconds()
                                    for row in rows if row['status'] == 'pending']),
}
Path(os.environ['OPT_RESULT']).write_text(json.dumps(result, indent=2))
print(json.dumps(result))
