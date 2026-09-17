"""Đưa hai trường đã dùng trong smoke về cùng dữ liệu tổng hợp để đo Chrome."""
import json
import os
from pathlib import Path
import psycopg
import optimization_wsgi
from django.db import connection,transaction
from forms_builder.models import DataRecord

marker=json.loads(Path('/runtime/ready.json').read_text())
assert marker['database']==connection.settings_dict['NAME']=='test_knjsc_opt_after300'
ids=marker['actors'][0]['bulk_ids'];assert len(ids)==2000
with psycopg.connect(host=os.environ['POSTGRES_HOST'],dbname='test_knjsc_opt_before300',
    user=os.environ['POSTGRES_USER'],password=os.environ['POSTGRES_PASSWORD']) as conn,conn.cursor() as c:
    c.execute('SELECT id,data,style FROM forms_builder_datarecord WHERE id=ANY(%s)',[ids])
    source={pk:(data,style) for pk,data,style in c.fetchall()}
assert set(source)==set(ids)
with transaction.atomic():
    rows=list(DataRecord.objects.filter(pk__in=ids).select_for_update().order_by('pk'))
    for row in rows:
        data,style=source[row.pk];assert data['ma_don']==row.data['ma_don']
        if 'ghi_chu' in data:row.data['ghi_chu']=data['ghi_chu']
        else:row.data.pop('ghi_chu',None)
        row.style=style
    DataRecord.bulk_save(rows,fields=('data','style'))
print('Đã đồng nhất ghi chú/style của 2000 dòng fixture; không xóa lịch sử/biên nhận.')
