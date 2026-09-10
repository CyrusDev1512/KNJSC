"""AC-21 — Ma trận có giới hạn trên database test, snapshots trước/sau độc lập."""
import json
import os
import subprocess
import time
from pathlib import Path
import pytest
from django.db import connection
from django.test import Client
from core.constants import Rank
from forms_builder.models import DataRecord
from orders.models import WaybillAssignment
from .test_waybill_feedback import feedback


@pytest.mark.cham
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(os.environ.get('KN_NINE_CAPACITY') != '1', reason='Kiểm tải chủ động trên DB test riêng')
def test_nine_capacity(feedback, make_user, departments, nguoi_dung):
    db = connection.settings_dict['NAME']
    assert db.startswith('test_knjsc_master_capacity_nine')
    assert Path('/before/app/manage.py').exists()
    output = Path('/evidence');output.mkdir(exist_ok=True)
    table, products, source = feedback
    users = []
    for i in range(20):
        rank, dept = (Rank.ADMIN, None) if i%5==0 else (Rank.LEADER, departments['vd']) if i%5==1 else (Rank.STAFF, departments['vd']) if i%5 in (2,3) else (Rank.STAFF, departments['sale'])
        users.append(make_user(f'nine_capacity_{i}', rank, dept))
    sessions=[]
    for user in users:
        c=Client();c.force_login(user);sessions.append(c.cookies['sessionid'].value)
    env={**os.environ,'POSTGRES_DB':db,'DJANGO_SETTINGS_MODULE':'knjsc.settings.test'}
    stage=os.environ.get('NINE_STAGE','before')
    assert stage in ('before','after')
    directory='/before/app' if stage=='before' else '/app'
    log=(output/f'gunicorn-{stage}.log').open('w')
    process=subprocess.Popen(['gunicorn','master_wsgi:application','--chdir',directory,'--pythonpath','/app/tests/perf',
        '--bind','0.0.0.0:8036','--workers','3','--threads','4','--worker-class','gthread','--timeout','60'],env=env,stdout=log,stderr=log)
    try:
        time.sleep(3)
        for count in [int(n) for n in os.environ.get('NINE_COUNTS','100000,300000').split(',')]:
            assert count in (100000,300000)
            current=DataRecord.objects.filter(table=table).count()
            fields=[f for f in DataRecord._meta.concrete_fields if f.name!='id']
            columns=', '.join('"'+f.column+'"' for f in fields)
            values=[]
            for f in fields:
                if f.name=='data':values.append("s.data || jsonb_build_object('ma_don','NINE-'||g,'ten_khach','Khách kiểm tải '||g,'quoc_gia',CASE WHEN g%%2=0 THEN 'USA' ELSE 'Canada' END,'ghi_chu',repeat('Nội dung kiểm thử dài. ',20))")
                elif f.name in ('created_at','updated_at'):values.append("s.created_at - (300000-g) * interval '1 second'")
                elif f.name=='val_customer':values.append("'Khách kiểm tải '||g")
                else:values.append('s."'+f.column+'"')
            with connection.cursor() as cur:
                cur.execute(f'INSERT INTO forms_builder_datarecord ({columns}) SELECT '+', '.join(values)+' FROM forms_builder_datarecord s CROSS JOIN generate_series(%s,%s) g WHERE s.id=%s',[current,count-1,source[0].pk])
                cur.execute('INSERT INTO orders_waybillitem (created_at,updated_at,record_id,product_id,quantity,unit_price,paid_amount) SELECT r.created_at,r.updated_at,r.id,%s,1,10,0 FROM forms_builder_datarecord r WHERE r.table_id=%s AND NOT EXISTS (SELECT 1 FROM orders_waybillitem i WHERE i.record_id=r.id)',[products[0].pk,table.pk])
                # Phân công quay vòng: scope Staff nhỏ hơn scope Leader/Admin.
                staff=[u.pk for u in users if u.profile.department_id==departments['vd'].pk and u.profile.rank==Rank.STAFF]
                sale=[u.pk for u in users if u.profile.department_id==departments['sale'].pk]
                cur.execute('INSERT INTO orders_waybillassignment (record_id,delivery_id,care_id,version) SELECT id,(%s::bigint[])[1+mod(id,%s)],(%s::bigint[])[1+mod(id,%s)],1 FROM forms_builder_datarecord WHERE table_id=%s ON CONFLICT (record_id) DO NOTHING',[staff,len(staff),sale,len(sale),table.pk])
                cur.execute('ANALYZE forms_builder_datarecord');cur.execute('ANALYZE orders_waybillassignment');cur.execute('ANALYZE orders_waybillitem')
            actors=[]
            for i,user in enumerate(users):
                qs=DataRecord.objects.in_scope(user).filter(table=table)
                # Sale được giao chỉ xem: tải đọc, lượt ghi riêng dùng dòng do Sale tạo.
                if user.profile.department_id==departments['sale'].pk:
                    row=qs.order_by('pk')[i]
                    DataRecord.objects.filter(pk=row.pk).update(created_by=user,department=departments['sale'])
                else:row=qs.order_by('pk')[i]
                actors.append({'session':sessions[i],'row':row.pk,'code':row.data['ma_don'],'total':qs.count()})
            manifest=output/f'manifest-{stage}.json';manifest.write_text(json.dumps({'database':db,'rows':count,'csrf':'a'*32,'actors':actors}))
            for concurrency in [int(n) for n in os.environ.get('NINE_USERS','10,20').split(',')]:
                assert concurrency in (10,20)
                label=f'{stage}-{count}-{concurrency}'
                with (output/f'{label}.log').open('w') as runlog:
                    run=subprocess.run(['locust','-f','tests/perf/locust_master_nine.py','--headless','--host','http://127.0.0.1:8036','--users',str(concurrency),'--spawn-rate','20','--run-time',os.environ.get('NINE_DURATION','360s'),'--only-summary'],env={**env,'MASTER_MANIFEST':str(manifest),'MASTER_RESULT':str(output/f'{label}.json'),'MASTER_WARMUP':os.environ.get('NINE_WARMUP','60')},stdout=runlog,stderr=runlog,timeout=410)
                assert run.returncode in (0,1)
                data=json.loads((output/f'{label}.json').read_text());assert data['samples']
                assert not data.get('integrity_errors'), 'Dừng: sai dữ liệu'
                errors=sum(bool(s['error']) for s in data['samples']);assert errors/len(data['samples'])<.05, 'Dừng: lỗi vượt 5%'
                print(label, 'samples',len(data['samples']),'errors',errors,flush=True)
            if os.environ.get('NINE_BROWSER') == '0':
                continue  # Chỉ dùng lượt smoke HTTP; không thay bằng chứng Chrome.
            marker=output/'nine-browser-ready.json';done=output/'nine-browser-done.json';done.unlink(missing_ok=True)
            marker.write_text(json.dumps({'stage':stage,'rows':count,'session':sessions[0],'port':8036,
                'endurance':stage=='after' and os.environ.get('NINE_ENDURANCE')=='1'}))
            end=time.monotonic()+180
            while not done.exists() and time.monotonic()<end:time.sleep(.2)
            assert done.exists() and json.loads(done.read_text()).get('ok'), 'Chưa có đo Chrome'
            marker.unlink(missing_ok=True);done.unlink(missing_ok=True)
        if stage=='after' and os.environ.get('NINE_ENDURANCE')=='1':
            # Ma trận trước/sau giữ workload giống nhau; chạy kéo dài bổ sung tranh chấp.
            for i,actor in enumerate(actors):
                if i%5 in (0,1):actor.update(row=source[0].pk,code=source[0].data['ma_don'])
            manifest.write_text(json.dumps({'database':db,'rows':count,'csrf':'a'*32,'actors':actors}))
            with (output/'endurance.log').open('w') as runlog:
                run=subprocess.run(['locust','-f','tests/perf/locust_master_nine.py','--headless','--host','http://127.0.0.1:8036','--users','20','--spawn-rate','20','--run-time','1860s','--only-summary'],env={**env,'MASTER_MANIFEST':str(manifest),'MASTER_RESULT':str(output/'endurance.json'),'MASTER_WARMUP':'60'},stdout=runlog,stderr=runlog,timeout=1920)
                assert run.returncode in (0,1)
                data=json.loads((output/'endurance.json').read_text());assert data['samples']
                assert not data.get('integrity_errors'), 'Dừng: sai dữ liệu'
                errors=sum(bool(s['error']) for s in data['samples'])
                assert errors/len(data['samples'])<.05, 'Dừng: lỗi vượt 5%'
                print('endurance', 'samples', len(data['samples']), 'errors', errors, flush=True)
    finally:
        process.terminate()
        try:process.wait(timeout=10)
        except subprocess.TimeoutExpired:process.kill();process.wait()
        (output/f'manifest-{stage}.json').unlink(missing_ok=True)
        (output/'nine-browser-ready.json').unlink(missing_ok=True)
