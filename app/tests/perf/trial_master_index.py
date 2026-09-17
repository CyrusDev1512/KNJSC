"""Thử chỉ mục có hoàn tác trên DB test; không được chạy DB đang sử dụng."""
import json
from pathlib import Path
from django.db import connection
assert connection.settings_dict['NAME'].startswith('test_knjsc_master_capacity_nine')
profile = Path('/evidence/query-profile.json')
exec(Path('tests/perf/inspect_master_nine.py').read_text())
before = json.loads(profile.read_text())
try:
    with connection.cursor() as cursor:
        cursor.execute('CREATE INDEX nine_trial_cover ON forms_builder_datarecord (table_id, created_at, id) INCLUDE (deleted_at, updated_at, created_by_id)')
    exec(Path('tests/perf/inspect_master_nine.py').read_text())
    after = json.loads(profile.read_text())
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_relation_size('nine_trial_cover')")
        size = cursor.fetchone()[0]
    Path('/evidence/index-trial.json').write_text(json.dumps({'before': before, 'after': after, 'index_bytes': size}, indent=2))
finally:
    with connection.cursor() as cursor:
        cursor.execute('DROP INDEX IF EXISTS nine_trial_cover')
