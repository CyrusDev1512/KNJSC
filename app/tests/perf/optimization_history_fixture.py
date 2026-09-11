"""300k mục lịch sử tổng hợp giống nhau trước/sau, không đọc dữ liệu thật."""
import json
import os
from pathlib import Path
import optimization_wsgi
from django.db import connection,transaction
from crm.services import master_grid_service,grid_service
from forms_builder.models import DataRecord
from django.contrib.auth import get_user_model

m=json.loads(Path(os.environ['OPT_MANIFEST']).read_text())
assert connection.settings_dict['NAME']==m['database'] and m['database'].startswith('test_knjsc_opt_')
actor=get_user_model().objects.get(pk=m['actors'][0]['user'])
row=DataRecord.objects.get(pk=m['actors'][0]['row'])
cols=grid_service.display_columns(row.table)
for c in cols:c.table=row.table
result={'rows':master_grid_service.serialize([row],cols,actor),'kind':'edit','changed':1,'replayed':False}
with transaction.atomic(),connection.cursor() as c:
    c.execute("SELECT count(*) FROM crm_gridmutationreceipt WHERE fingerprint LIKE 'opt-history-%'")
    if c.fetchone()[0]==0:
        c.execute("INSERT INTO crm_gridmutationreceipt(actor_id,table_id,operation,fingerprint,result,created_at) SELECT %s,%s,md5('optimization-history-'||g)::uuid,'opt-history-'||g,%s::jsonb,clock_timestamp() FROM generate_series(1,300000) g",[actor.pk,row.table_id,json.dumps(result)])
        c.execute("INSERT INTO crm_gridcellhistory(record_id,receipt_id,\"column\",property,before,after,created_at) SELECT %s,id,'ghi_chu','value','\"Trước\"'::jsonb,'\"Sau\"'::jsonb,created_at FROM crm_gridmutationreceipt WHERE fingerprint LIKE 'opt-history-%%'",[row.pk])
    c.execute('ANALYZE crm_gridcellhistory');c.execute('ANALYZE crm_gridmutationreceipt')
print('Đã có 300000 mục lịch sử fixture; không xuất nội dung hay phiên đăng nhập.')
