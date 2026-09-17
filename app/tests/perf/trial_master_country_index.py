"""Thử index biểu thức Quốc gia trên DB test được giữ lại từ phép đo."""
import json
import time
from pathlib import Path
from django.db import connection
from django.contrib.auth import get_user_model
from forms_builder.models import DataRecord, TableDef
assert connection.settings_dict['NAME'].startswith('test_knjsc_master_capacity_nine')
with connection.cursor() as cursor:
    cursor.execute('SET max_parallel_workers_per_gather=0')
table=TableDef.objects.get(code='van_don_moi')
def measure():
    result=[]
    for i in (0,1,2,4):
        user=get_user_model().objects.select_related('profile__department').get(username=f'nine_capacity_{i}')
        qs=DataRecord.objects.in_scope(user,table=table).filter(data__quoc_gia='USA')
        start=time.perf_counter();count=qs.count();elapsed=(time.perf_counter()-start)*1000
        sql,params=qs.order_by('created_at','pk').values_list('pk',flat=True)[:100].query.sql_with_params()
        with connection.cursor() as cursor:
            cursor.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+sql,params);plan=cursor.fetchone()[0]
        result.append({'role':i,'count':count,'count_ms':elapsed,'plan':plan})
    return result
before=measure()
try:
    with connection.cursor() as cursor:
        cursor.execute("CREATE INDEX nine_country_trial ON forms_builder_datarecord (table_id, (data->'quoc_gia'), created_at, id) INCLUDE (deleted_at,created_by_id)")
    after=measure()
    assert [r['count'] for r in before]==[r['count'] for r in after]
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_relation_size('nine_country_trial')");size=cursor.fetchone()[0]
    Path('/evidence/country-index-trial.json').write_text(json.dumps({'before':before,'after':after,'index_bytes':size},indent=2))
    print('count ms before/after',[(b['role'],round(b['count_ms']),round(a['count_ms'])) for b,a in zip(before,after)])
finally:
    with connection.cursor() as cursor:cursor.execute('DROP INDEX IF EXISTS nine_country_trial')
