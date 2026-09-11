"""Server dữ liệu kiểm tải riêng; Locust/Gunicorn chạy container khác."""
import json
import os
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
@pytest.mark.skipif(os.environ.get('OPT_CAPACITY')!='1',reason='Fixture kiểm tải tối ưu riêng')
def test_capacity(feedback, make_user, departments):
    database=connection.settings_dict['NAME'];assert database.startswith('test_knjsc_opt_')
    count=int(os.environ.get('OPT_ROWS','100000'));assert count in (100000,300000)
    table,products,source=feedback
    fields=[f for f in DataRecord._meta.concrete_fields if f.name!='id']
    columns=', '.join('"'+f.column+'"' for f in fields);select=[]
    for f in fields:
        if f.name=='data':select.append("s.data || jsonb_build_object('ma_don','OPT-'||g,'ten_khach','Khách kiểm tải '||g,'quoc_gia',CASE WHEN g%%5=0 THEN 'Canada' ELSE 'USA' END,'ghi_chu',repeat('Nội dung kiểm thử. ',20))")
        elif f.name in ('created_at','updated_at'):select.append("s.created_at + g * interval '1 second'")
        elif f.name=='val_customer':select.append("'Khách kiểm tải '||g")
        else:select.append('s."'+f.column+'"')
    with connection.cursor() as cursor:
        cursor.execute(f'INSERT INTO forms_builder_datarecord ({columns}) SELECT '+', '.join(select)+' FROM forms_builder_datarecord s CROSS JOIN generate_series(2,%s) g WHERE s.id=%s',[count-1,source[0].pk])
        cursor.execute("INSERT INTO orders_waybillitem (created_at,updated_at,record_id,product_id,quantity,unit_price,paid_amount,unit) SELECT r.created_at,r.updated_at,r.id,%s,1,10,0,'cái' FROM forms_builder_datarecord r WHERE r.table_id=%s AND NOT EXISTS (SELECT 1 FROM orders_waybillitem i WHERE i.record_id=r.id)",[products[0].pk,table.pk])
    users=[]
    for i in range(20):
        rank,dept=(Rank.ADMIN,None) if i%5==0 else (Rank.LEADER,departments['vd']) if i%5==1 else (Rank.STAFF,departments['sale']) if i%5==4 else (Rank.STAFF,departments['vd'])
        users.append(make_user(f'opt_{i}',rank,dept))
    staff=[u.pk for i,u in enumerate(users) if i%5 in (2,3)]
    sale=[u.pk for i,u in enumerate(users) if i%5==4]
    with connection.cursor() as cursor:
        cursor.execute('INSERT INTO orders_waybillassignment (record_id,delivery_id,care_id,version) SELECT id,(%s::bigint[])[1+mod(id,%s)],(%s::bigint[])[1+mod(id,%s)],1 FROM forms_builder_datarecord WHERE table_id=%s ON CONFLICT (record_id) DO NOTHING',[staff,len(staff),sale,len(sale),table.pk])
        for name in ('forms_builder_datarecord','orders_waybillitem','orders_waybillassignment'):cursor.execute('ANALYZE '+name)
    actors=[]
    for i,user in enumerate(users):
        qs=DataRecord.objects.in_scope(user,table=table).order_by('created_at','id');row=qs[i]
        if i%5==4:DataRecord.objects.filter(pk=row.pk).update(created_by=user,department=departments['sale'])
        client=Client();client.force_login(user)
        actors.append({'session':client.cookies['sessionid'].value,'row':row.pk,'code':row.data['ma_don'],'total':qs.count(),'user':user.pk})
    runtime=Path('/runtime');runtime.mkdir(exist_ok=True)
    marker=runtime/'ready.json';done=runtime/'done.json';done.unlink(missing_ok=True)
    marker.write_text(json.dumps({'database':database,'rows':count,'actors':actors,'csrf':'a'*32}))
    try:
        deadline=time.monotonic()+7200
        while not done.exists() and time.monotonic()<deadline:time.sleep(.5)
        assert done.exists(),'Chưa kết thúc kiểm tải'
    finally:marker.unlink(missing_ok=True);done.unlink(missing_ok=True)
