"""AC-21.1, AC-21.6: kiểm trình duyệt hàng biến thiên trên DB test, không chạy HTTP load."""
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
from .test_waybill_feedback import feedback


@pytest.mark.cham
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(os.environ.get('KN_MASTER_ROW_CAPACITY') != '1', reason='Chrome 100k/300k trên DB test riêng')
def test_row_capacity(feedback, make_user, settings):
    database=connection.settings_dict['NAME']
    assert database.startswith('test_knjsc_master_capacity_rows')
    output=Path('/evidence');output.mkdir(exist_ok=True)
    table,products,source=feedback
    client=Client();client.force_login(make_user('row_capacity',Rank.ADMIN))
    env={**os.environ,'POSTGRES_DB':database,'DJANGO_SETTINGS_MODULE':'knjsc.settings.test'}
    log=(output/'row-capacity-gunicorn.log').open('w')
    process=subprocess.Popen(['gunicorn','master_wsgi:application','--chdir','/app',
        '--pythonpath','/app/tests/perf','--bind','0.0.0.0:8033','--workers','3','--threads','4',
        '--worker-class','gthread','--keep-alive','5','--timeout','60'],env=env,stdout=log,stderr=log)
    try:
        time.sleep(3)
        for count in (100000,300000):
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
                    (created_at,updated_at,record_id,product_id,quantity,unit_price,paid_amount,unit)
                    SELECT r.created_at,r.updated_at,r.id,%s,1,10,0,'hộp' FROM forms_builder_datarecord r
                    WHERE r.table_id=%s AND NOT EXISTS (SELECT 1 FROM orders_waybillitem i WHERE i.record_id=r.id)''', [products[0].pk,table.pk])
                cursor.execute('ANALYZE forms_builder_datarecord');cursor.execute('ANALYZE orders_waybillitem')
            marker=output/'row-capacity-ready.json';result=output/'row-capacity-result.json'
            result.unlink(missing_ok=True)
            marker.write_text(json.dumps({'rows':count,'port':8033,'session':client.cookies['sessionid'].value}))
            deadline=time.monotonic()+300
            while not result.exists() and time.monotonic()<deadline:time.sleep(.2)
            assert result.exists(), 'Cần chạy scripts/kiem-thu-master-row-capacity.cjs'
            assert json.loads(result.read_text()).get('ok'),result.read_text()
            marker.unlink(missing_ok=True);result.unlink(missing_ok=True)
    finally:
        process.terminate()
        try:process.wait(timeout=10)
        except subprocess.TimeoutExpired:process.kill();process.wait()
        log.close()
        for name in ('row-capacity-ready.json','row-capacity-result.json'):(output/name).unlink(missing_ok=True)
