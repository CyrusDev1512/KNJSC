"""Đo riêng tạo 2.000 ô qua HTTP; chỉ DB của chiến dịch kiểm tải."""
import json
import math
import time
import uuid
from decimal import Decimal
from pathlib import Path
import requests
import django
django.setup()
from django.db import connection
from forms_builder.models import DataRecord

assert connection.settings_dict['HOST']=='knjsc-crm-update-db'
assert connection.settings_dict['NAME'].startswith('test_crm_update_load_')
manifest=json.loads(Path('/runtime/ready.json').read_text())
actor=manifest['actors'][19]
session=requests.Session()
session.cookies.set('sessionid',actor['session'])
session.cookies.set('csrftoken',manifest['csrf'])
session.headers['X-CSRFToken']=manifest['csrf']
samples=[]
for batch in range(30):
    operation=str(uuid.uuid4())
    values={-i:{'ma_don':f'BULK-{operation}-{i}','ten_khach':'Khach synthetic',
                'so_don':5,'cpqc':'100.00','so_dien_thoai':'0012345678'} for i in range(1,401)}
    payload={'operation':operation,'kind':'paste','cells':[
        {'id':pk,'column':column,'old':None,'value':value}
        for pk,data in values.items() for column,value in data.items()]}
    start=time.perf_counter()
    response=session.post('http://127.0.0.1:8000/bang-tinh/'+actor['table']+'/luu-json/',json=payload,timeout=30)
    elapsed=(time.perf_counter()-start)*1000
    assert response.status_code==200,(response.status_code,response.text[:200])
    mapping=response.json()['id_map']
    assert len(mapping)==400 and len(set(mapping.values()))==400
    rows=list(DataRecord.objects.filter(pk__in=mapping.values()))
    assert len(rows)==400
    by_id={r.pk:r for r in rows}
    for temporary,pk in mapping.items():
        row=by_id[pk]
        assert row.created_by_id==actor['user'] and row.data['ma_don']==values[int(temporary)]['ma_don']
        assert row.data['so_dien_thoai']=='0012345678' and Decimal(row.data['cpo'])==20
    samples.append({'ms':elapsed,'sql':response.headers.get('Server-Timing'),'request_id':response.headers.get('X-Request-ID'),'rows':400})
result={'samples':samples,'errors':[],'verified_rows':len(samples)*400}
Path('/runtime/bulk-2000.json').write_text(json.dumps(result,indent=2))
print(json.dumps({'n':len(samples),'p95':sorted(s['ms'] for s in samples)[math.ceil(len(samples)*.95)-1],'verified_rows':result['verified_rows']}))
