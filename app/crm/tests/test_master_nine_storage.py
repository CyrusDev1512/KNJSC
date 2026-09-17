"""Đo lịch sử/biên nhận thực tế trên PostgreSQL test, không suy ra từ mã nguồn."""
import json
import os
import time
import uuid
from pathlib import Path
import pytest
from django.db import connection
from .test_waybill_feedback import feedback
from .test_master_grid import BASE
from forms_builder.models import DataRecord
from crm.models import GridCellHistory, GridMutationReceipt


@pytest.mark.cham
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(os.environ.get('KN_NINE_STORAGE')!='1', reason='Phép đo dung lượng trên DB test riêng')
def test_storage(client, feedback, nguoi_dung):
    assert connection.settings_dict['NAME'].startswith('test_knjsc_nine_storage')
    client.force_login(nguoi_dung['admin']);table,_,source=feedback
    result={'database':'test only','samples':{},'sizes':{}}
    def sizes():
        with connection.cursor() as c:
            c.execute("SELECT name,pg_table_size(name::regclass),pg_indexes_size(name::regclass),pg_total_relation_size(name::regclass) FROM unnest(ARRAY['crm_gridcellhistory','crm_gridmutationreceipt']) name")
            return {r[0]:{'table_toast_bytes':r[1],'index_bytes':r[2],'total_bytes':r[3]} for r in c.fetchall()}
    def write(cells):
        start=time.perf_counter();r=client.post(BASE+'luu-json/',{'operation':str(uuid.uuid4()),'cells':cells},content_type='application/json');elapsed=(time.perf_counter()-start)*1000
        assert r.status_code==200,r.status_code
        return elapsed,r.json()
    row=source[0];old=row.data.get('ghi_chu');result['sizes']['empty']=sizes()
    for label in ('short','long','format'):
        timings=[];style=None
        for i in range(100):
            value=uuid.uuid4().hex if label=='short' else ''.join(uuid.uuid4().hex for _ in range(30)) if label=='long' else (18 if i%2==0 else 14)
            cell={'id':row.pk,'column':'ghi_chu','old':style if label=='format' else old,'value':value}
            if label=='format':cell['property']='fs';style=value
            else:old=value
            elapsed,_=write([cell]);timings.append(elapsed)
        result['samples'][label]=timings;result['sizes'][label]=sizes()
    rows=DataRecord.objects.bulk_create([DataRecord(table=table,created_by=nguoi_dung['admin'],data={**row.data,'ma_don':f'SIZE-{i}'}) for i in range(1000)])
    timings=[]
    for trial in range(20):
        cells=[{'id':r.pk,'column':col,'old':r.data.get(col),'value':f'{trial}-{r.pk}'} for r in rows for col in ('ghi_chu','bang')]
        elapsed,data=write(cells);timings.append(elapsed)
        for r in rows:r.data.update(ghi_chu=f'{trial}-{r.pk}',bang=f'{trial}-{r.pk}')
    result['samples']['batch2000']=timings;result['sizes']['batch2000']=sizes()
    count=GridCellHistory.objects.count();receipt=GridMutationReceipt.objects.first()
    with connection.cursor() as c:
        c.execute('INSERT INTO crm_gridcellhistory (record_id,receipt_id,"column",property,before,after,created_at) SELECT %s,%s,\'ghi_chu\',\'value\',to_jsonb(md5(g::text)),to_jsonb(md5((g+1)::text)),now() FROM generate_series(1,%s) g',[row.pk,receipt.pk,300000-count])
        c.execute('ANALYZE crm_gridcellhistory');c.execute('ANALYZE crm_gridmutationreceipt')
    result['sizes']['history300000']=sizes();result['history_count']=GridCellHistory.objects.count();result['receipt_count']=GridMutationReceipt.objects.count()
    timings=[]
    for i in range(100):
        start=time.perf_counter();r=client.get(BASE+'lich-su/',{'record':row.pk});timings.append((time.perf_counter()-start)*1000)
        assert r.status_code==200 and len(r.json()['items'])==50
    result['samples']['history300000']=timings
    Path('/evidence/storage.json').write_text(json.dumps(result))
