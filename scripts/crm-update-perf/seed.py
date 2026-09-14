import os,json
from pathlib import Path
import django
django.setup()
from django.db import connection
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.test import Client
from core.constants import Rank
from org.models import Department,UserProfile
from forms_builder.models import TableDef,ColumnDef,DataRecord,ComputeOp
from forms_builder.meaning import FieldType,Meaning
from forms_builder.services import record_service
assert connection.settings_dict['HOST']=='knjsc-crm-update-db'
assert connection.settings_dict['NAME'].startswith('test_crm_update_load_')
count=int(os.environ['LOAD_ROWS']);assert count in (100000,300000)
call_command('migrate',interactive=False,verbosity=0)
assert not TableDef.objects.exists(),'Refuse to seed nonempty database'
actors=[]
for di,(dept_code,table_code) in enumerate([('marketing','mkt_load'),('sale','sale_load'),('van-don','van_don')]):
 dept=Department.objects.create(code=dept_code,name=dept_code)
 table=TableDef.objects.create(code=table_code,name=table_code,department=dept,is_shared=di==2)
 users=[]
 for i in range(20):
  user=get_user_model().objects.create_user(username=f'load_{di}_{i}')
  UserProfile.objects.create(user=user,rank=Rank.STAFF,department=dept,must_change_password=False)
  users.append(user)
 fields=[('ma_don','text',''),('ngay','date','date'),('ten_khach','text','customer'),('so_dien_thoai','text','phone'),('so_mess','integer',''),('so_don','integer',''),('cpqc','money',''),('ghi_chu','long_text','')]
 for n,(code,kind,meaning) in enumerate(fields):ColumnDef.objects.create(table=table,name=code,code=code,field_type=kind,meaning=meaning,order=n,is_key=code=='ma_don')
 if di<2:ColumnDef.objects.create(table=table,name='CPO',code='cpo',field_type='decimal',is_computed=True,compute_op=ComputeOp.DIVIDE,compute_left='cpqc',compute_right='so_don',compute_decimals=2,order=8)
 source=record_service.create_record(table,{'ma_don':'LOAD-0','ngay':'2026-09-12','ten_khach':'Khach test','so_dien_thoai':'0900000000','so_mess':100,'so_don':5,'cpqc':'100.00','ghi_chu':'Du lieu kiem thu '*12},actor=users[0])
 model_fields=[f for f in DataRecord._meta.concrete_fields if f.name!='id'];select=[]
 for f in model_fields:
  if f.name=='data':select.append("s.data || jsonb_build_object('ma_don','LOAD-'||g,'ten_khach','Khach test '||g)")
  elif f.name=='created_by':select.append(f"(ARRAY[{','.join(str(u.pk) for u in users)}]::bigint[])[1+mod(g,20)]")
  elif f.name=='val_customer':select.append("'Khach test '||g")
  elif f.name in ('created_at','updated_at'):select.append("s.created_at + g * interval '1 second'")
  else:select.append('s."'+f.column+'"')
 with connection.cursor() as cursor:
  cursor.execute('INSERT INTO forms_builder_datarecord ('+','.join('"'+f.column+'"' for f in model_fields)+') SELECT '+','.join(select)+' FROM forms_builder_datarecord s CROSS JOIN generate_series(1,%s) g WHERE s.id=%s',[count-1,source.pk])
 for i,user in enumerate(users):
  row=DataRecord.objects.filter(table=table,created_by=user).order_by('id').first()
  client=Client();client.force_login(user)
  actors.append({'table':table.code,'group':dept_code,'session':client.cookies['sessionid'].value,'row':row.pk,'user':user.pk,'note':row.data['ghi_chu'],'code':row.data['ma_don']})
with connection.cursor() as cursor:cursor.execute('ANALYZE forms_builder_datarecord')
Path('/runtime/ready.json').write_text(json.dumps({'database':connection.settings_dict['NAME'],'rows':count,'actors':actors,'csrf':'a'*32}))
print('Ready',count,'rows per table')
