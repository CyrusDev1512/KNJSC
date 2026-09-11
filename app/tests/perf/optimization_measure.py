"""Đo bổ sung trên DB tổng hợp được fixture sở hữu, không dùng DB local/thật."""
import json
import os
import time
import uuid
from pathlib import Path
import optimization_wsgi
from django.contrib.auth import get_user_model
from django.db import connection
from django.http import QueryDict
from crm.services import grid_service, master_grid_service
from forms_builder.models import TableDef, DataRecord

manifest=json.loads(Path(os.environ['OPT_MANIFEST']).read_text())
assert connection.settings_dict['NAME']==manifest['database']
assert manifest['database'].startswith('test_knjsc_opt_')
user=get_user_model().objects.get(pk=manifest['actors'][0]['user'])
table=TableDef.objects.get(code='van_don_moi')
protocol=int(os.environ.get('OPT_PROTOCOL','1'))
result={'database':manifest['database'],'protocol':protocol}
http=os.environ.get('OPT_HTTP')
session=None
if http:
    assert http.startswith('http://crm-opt-')
    import requests
    session=requests.Session()
    session.cookies.set('sessionid',manifest['actors'][0]['session'])
    session.cookies.set('csrftoken',manifest['csrf'])
    session.headers['X-CSRFToken']=manifest['csrf']
result['mode']='http-wall-time' if http else 'service-including-commit'

def sizes():
    with connection.cursor() as c:
        c.execute("SELECT relname,pg_table_size(oid),pg_indexes_size(oid),pg_total_relation_size(oid) FROM pg_class WHERE relname IN ('crm_gridcellhistory','crm_gridmutationreceipt','crm_gridchange','crm_gridrevision')")
        values={name:{'table_toast':data,'indexes':idx,'total':total} for name,data,idx,total in c.fetchall()}
        c.execute('SELECT pg_current_wal_insert_lsn()::text');values['wal_lsn']=c.fetchone()[0]
    return values

def explain():
    qs=grid_service.build_grid(user,QueryDict(),table=table).queryset.select_related(None)
    total=manifest['rows'];queries={}
    for offset in [0,total//2,total-100]:queries[f'offset-{offset}']=qs.values('pk','created_at')[offset:offset+100]
    from django.db.models import Q
    edge=qs.values_list('created_at','pk')[total-101]
    queries['cursor-end']=qs.filter(Q(created_at__gt=edge[0])|Q(created_at=edge[0],pk__gt=edge[1])).values('pk','created_at')[:100]
    from orders.models import WaybillItem
    product=WaybillItem.objects.filter(record__table=table).values_list('product__code',flat=True).first()
    assignee=get_user_model().objects.get(pk=manifest['actors'][2]['user']).username
    sample=qs.first().data
    for name,params in {
        'country':'f_quoc_gia=USA','date':'f_ngay__lon_bang=2026-01-01&f_ngay__nho_bang=2026-12-31',
        'shipping':'f_trang_thai_vc='+sample.get('trang_thai_vc','Đã lên đơn'),
        'payment':'f_trang_thai_tt='+sample.get('trang_thai_tt','Chưa thanh toán'),
        'product':'sp='+product,'marketing':'f_phu_trach_mkt=__unassigned__','assignee':'f_phu_trach_vd='+assignee,
        'search':'tim=Kiểm tải'
    }.items():queries[name]=grid_service.build_grid(user,QueryDict(params),table=table).queryset.select_related(None).values('pk')[:100]
    return {name:[json.loads(q.explain(analyze=True,buffers=True,format='json')) for _ in range(3)] for name,q in queries.items()}

if os.environ.get('OPT_MEASURE','all') in ('all','explain'):result['plans']=explain()
if os.environ.get('OPT_MEASURE','all') in ('all','storage'):
    ids=list(grid_service.build_grid(user,QueryDict(),table=table).queryset.values_list('pk',flat=True)[:2000])
    assert len(ids)==2000
    result['storage']=[]
    for kind,repeats in [('short',100),('long',100),('style',100),('paste2000',20)]:
        before=sizes();samples=[];receipt_bytes=[];changes=0;operations=[];request_ids=[]
        for n in range(repeats):
            selected=ids if kind=='paste2000' else ids[:1]
            current={r.pk:r for r in DataRecord.objects.filter(pk__in=selected)}
            value=(('Nội dung kiểm thử dài. '*250)+str(n)) if kind=='long' else f'Test-{kind}-{n}'
            cells=[{'id':pk,'column':'ghi_chu','old':current[pk].data.get('ghi_chu'),'value':value} for pk in selected]
            if kind=='style':
                old=(current[ids[0]].style or {}).get('ghi_chu',{}).get('fs')
                cells=[{'id':ids[0],'column':'ghi_chu','property':'fs','old':old,'value':16 if old!=16 else 20}]
            payload={'protocol':protocol,'operation':str(uuid.uuid4()),'kind':'format' if kind=='style' else 'paste' if kind=='paste2000' else 'edit','cells':cells}
            operations.append(payload['operation'])
            start=time.perf_counter()
            if session:
                request_id=uuid.uuid4().hex;request_ids.append(request_id)
                response=session.post(http+'/bang-tinh/van_don_moi/luu-json/',json=payload,headers={'X-Request-ID':request_id},timeout=60)
                assert response.status_code==200,(response.status_code,request_id)
                reply=response.json()
            else:reply=master_grid_service.save(user,table,payload)
            samples.append((time.perf_counter()-start)*1000)
            assert reply['changed']==len(cells)
            changes+=reply['changed'];receipt_bytes.append(len(json.dumps(reply).encode()))
        after=sizes()
        with connection.cursor() as c:
            c.execute('SELECT pg_wal_lsn_diff(%s,%s)',[after['wal_lsn'],before['wal_lsn']]);wal=int(c.fetchone()[0])
            c.execute('SELECT count(*),sum(pg_column_size(result)) FROM crm_gridmutationreceipt WHERE operation=ANY(%s::uuid[])',[operations]);receipt_datum=c.fetchone()
            c.execute('SELECT count(*),sum(coalesce(pg_column_size(h.before),0)+coalesce(pg_column_size(h.after),0)) FROM crm_gridcellhistory h JOIN crm_gridmutationreceipt r ON r.id=h.receipt_id WHERE r.operation=ANY(%s::uuid[])',[operations]);history_datum=c.fetchone()
        assert receipt_datum[0]==repeats and history_datum[0]==changes
        result['storage'].append({'kind':kind,'operations':repeats,'changed_cells':changes,'server_ms':samples,'response_bytes':receipt_bytes,'before':before,'after':after,'wal_cluster_bytes':wal,'receipt_json_bytes':receipt_datum[1],'history_value_bytes':history_datum[1],'request_ids':request_ids})
Path(os.environ['OPT_RESULT']).write_text(json.dumps(result,default=str))
print('Đã ghi số đo; WAL là toàn cluster, không phải WAL riêng database.')
