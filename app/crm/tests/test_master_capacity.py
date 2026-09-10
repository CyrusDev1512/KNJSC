"""AC-21.6: phép đo trước/sau trên DB pytest, không seed dữ liệu đang dùng."""
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
from orders.models import WaybillItem
from .test_waybill_feedback import feedback


@pytest.mark.cham
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(os.environ.get('KN_MASTER_CAPACITY') != '1', reason='Kiểm tải riêng, có giới hạn và DB test')
def test_master_capacity(feedback, make_user, settings):
    database=connection.settings_dict['NAME']
    assert database.startswith('test_knjsc_master_capacity')
    assert Path('/before/app/manage.py').exists(), 'Cần snapshot HEAD trước sửa, chỉ đọc'
    output=Path('/evidence'); output.mkdir(exist_ok=True)
    table, products, source=feedback
    clients=[]
    for i in range(20):
        user=make_user(f'capacity_{i}', Rank.ADMIN)
        client=Client(); client.force_login(user); clients.append(client)
    env={**os.environ, 'POSTGRES_DB':database, 'DJANGO_SETTINGS_MODULE':'knjsc.settings.test'}
    processes=[]
    try:
        for stage, directory, port in [('before','/before/app',8032),('after','/app',8033)]:
            log=(output/f'gunicorn-{stage}.log').open('w')
            processes.append(subprocess.Popen(['gunicorn','master_wsgi:application','--chdir',directory,
                '--pythonpath','/app/tests/perf','--bind',f'0.0.0.0:{port}','--workers','3','--threads','4',
                '--worker-class','gthread','--keep-alive','5','--timeout','60'],env=env,stdout=log,stderr=log))
        time.sleep(3)
        for count in (100000,300000):
            if count==100000 and os.environ.get('MASTER_SKIP_100')=='1':
                for stage in ('before','after'):
                    for users in (10,20):
                        recorded=json.loads((output/f'{stage}-{count}-{users}.json').read_text())
                        assert recorded['samples'] and not any(s['error'] for s in recorded['samples'])
                continue
            # Nhân bản fixture bằng SQL có tham số trong DB test, đủ 25 cột + chi tiết.
            current=DataRecord.objects.filter(table=table).count()
            fields=[f for f in DataRecord._meta.concrete_fields if f.name!='id']
            columns=', '.join('"'+f.column+'"' for f in fields)
            select=[]
            for f in fields:
                if f.name=='data':
                    select.append("s.data || jsonb_build_object('ma_don','CAP-'||g, 'ten_khach','Khách kiểm tải '||g, 'quoc_gia', CASE WHEN g%%2=0 THEN 'USA' ELSE 'Canada' END, 'ghi_chu',repeat('Nội dung kiểm thử. ',20))")
                elif f.name in ('created_at','updated_at'):
                    select.append("s.created_at - g * interval '1 second'")
                elif f.name=='val_customer': select.append("'Khách kiểm tải '||g")
                else: select.append('s."'+f.column+'"')
            with connection.cursor() as cursor:
                cursor.execute(f'INSERT INTO forms_builder_datarecord ({columns}) SELECT '+', '.join(select)+
                    ' FROM forms_builder_datarecord s CROSS JOIN generate_series(%s,%s) g WHERE s.id=%s', [current,count-1,source[0].pk])
                cursor.execute('''INSERT INTO orders_waybillitem
                    (created_at,updated_at,record_id,product_id,quantity,unit_price,paid_amount)
                    SELECT r.created_at,r.updated_at,r.id,%s,1,10,0 FROM forms_builder_datarecord r
                    WHERE r.table_id=%s AND NOT EXISTS (SELECT 1 FROM orders_waybillitem i WHERE i.record_id=r.id)''', [products[0].pk,table.pk])
                cursor.execute('ANALYZE forms_builder_datarecord');cursor.execute('ANALYZE orders_waybillitem')
            ids=list(DataRecord.objects.filter(table=table).order_by('pk').values_list('pk',flat=True)[:20])
            for stage, port in [('before',8032),('after',8033)]:
                if stage=='before' and os.environ.get('MASTER_ONLY_AFTER')=='1':
                    for users in (10,20):
                        assert json.loads((output/f'{stage}-{count}-{users}.json').read_text())['samples']
                    continue
                for users in (10,20):
                    with connection.cursor() as cursor:
                        cursor.execute("UPDATE forms_builder_datarecord SET data=jsonb_set(data,'{ghi_chu}','null'::jsonb) WHERE id=ANY(%s)",[ids])
                    manifest={'database':database,'rows':count,'csrf':'a'*32,
                        'actors':[{'session':client.cookies['sessionid'].value,'row':pk,'old':None} for client,pk in zip(clients,ids)]}
                    manifest_path=output/'capacity-manifest.json';manifest_path.write_text(json.dumps(manifest))
                    label=f'{stage}-{count}-{users}'
                    if os.environ.get('MASTER_SKIP_BEFORE100') == '1' and stage=='before' and count==100000:
                        recorded=json.loads((output/f'{label}.json').read_text())
                        assert recorded['samples'] and not any(s['error'] for s in recorded['samples'])
                        continue  # Lượt HTTP cùng snapshot/cấu hình vừa hoàn tất; chạy lại Chrome lỗi harness.
                    with (output/f'{label}.log').open('w') as log:
                        completed=subprocess.run(['locust','-f','tests/perf/locustfile_master.py','--headless',
                            '--host',f'http://127.0.0.1:{port}','--users',str(users),'--spawn-rate','20','--run-time','45s',
                            '--only-summary'],env={**env,'MASTER_MANIFEST':str(manifest_path),'MASTER_STAGE':stage,
                            'MASTER_USERS':str(users),'MASTER_RESULT':str(output/f'{label}.json')},stdout=log,stderr=log,timeout=80)
                    assert completed.returncode in (0,1), (label,(output/f'{label}.log').read_text()[-3000:])
                    measured=json.loads((output/f'{label}.json').read_text())['samples']
                    assert measured and sum(bool(s['error']) for s in measured)/len(measured)<.05, 'Dừng: lỗi vượt 5%'
                    # Mọi lỗi giữ trong JSON. Kết quả kỹ thuật chạy xong không đồng nghĩa đạt ngưỡng.
                    print('Đã đo',label,flush=True)
                # Chrome đo riêng, không trộn với tải HTTP.
                marker=output/'capacity-browser-ready.json';result=output/'capacity-browser-result.json'
                result.unlink(missing_ok=True)
                marker.write_text(json.dumps({'stage':stage,'rows':count,'port':port,'session':clients[0].cookies['sessionid'].value}))
                deadline=time.monotonic()+120
                while not result.exists() and time.monotonic()<deadline: time.sleep(.2)
                assert result.exists(), 'Cần chạy scripts/kiem-thu-master-capacity.cjs'
                assert json.loads(result.read_text()).get('ok'), result.read_text()
                marker.unlink(missing_ok=True);result.unlink(missing_ok=True)
    finally:
        for process in processes:
            process.terminate()
        for process in processes:
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired: process.kill();process.wait()
        for name in ('capacity-manifest.json','capacity-browser-ready.json','capacity-browser-result.json'):
            (output/name).unlink(missing_ok=True)
