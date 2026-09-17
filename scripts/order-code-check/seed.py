import os,json,secrets
from pathlib import Path
from datetime import date,timedelta
from decimal import Decimal
import django
django.setup()
from django.db import connection
assert connection.settings_dict['NAME']=='test_knjsc_code_load'
assert connection.settings_dict['HOST']=='knjsc-code-db'
from django.contrib.auth import get_user_model
from django.test import Client
from org.models import Department,UserProfile
from core.constants import Rank
from orders.models import Product,Customer,Order,OrderLine,WaybillItem,WaybillAssignment
from orders.constants import ShippingStatus,Market,PaymentMethod,PaymentStatus
from orders.services import dispatch_service
from forms_builder.models import TableDef,DataRecord
assert not Order.all_objects.exists()
sale=Department.objects.create(name='Sale TEST',code='sale')
vd=Department.objects.create(name='Van don TEST',code='van-don')
User=get_user_model();users=[]
for role,n,dept in [('sale',30,sale),('delivery',10,vd)]:
 for i in range(n):
  u=User.objects.create_user(username=f'test_{role}_{i:02}',password=secrets.token_urlsafe(24))
  UserProfile.objects.create(user=u,rank=Rank.STAFF,department=dept,must_change_password=False)
  c=Client();c.force_login(u)
  users.append({'role':role,'index':i,'id':u.pk,'username':u.username,'session':c.cookies['sessionid'].value})
admin=User.objects.create_user(username='test_admin',password=secrets.token_urlsafe(24))
UserProfile.objects.create(user=admin,rank=Rank.ADMIN,must_change_password=False)
c=Client();c.force_login(admin)
users.append({'role':'admin','index':0,'id':admin.pk,'username':admin.username,'session':c.cookies['sessionid'].value})
dispatch_service.ensure_waybill_table(actor=admin)
table=TableDef.objects.get(code='van_don_moi')
products=[Product.objects.create(code=f'test-product-{i}',name=f'San pham TEST {i}',unit='hop') for i in range(8)]
cols=list(table.columns.all());sellers=[u for u in users if u['role']=='sale'];handlers=[u for u in users if u['role']=='delivery']
for start in range(0,100000,2000):
 customers=Customer.objects.bulk_create([Customer(name=f'Khach TEST {i}',phone=f'090{i:07}') for i in range(start,start+2000)])
 records=[];orders=[]
 for i,c in enumerate(customers,start):
  seller=sellers[i%30];day=date(2026,1,1)+timedelta(days=i%365);status=ShippingStatus.labels[i%len(ShippingStatus.labels)]
  a,b=products[i%8],products[(i+1)%8]
  data={'ma_don':f'TEST-{i:07}','ngay':day.isoformat(),'ten_khach':c.name,'so_dien_thoai':c.phone,'san_pham':a.name+' + '+b.name,'so_luong':3,'gia_tien':'40.40','so_tien_tt':'0.00','trang_thai_tt':PaymentStatus.UNPAID.label,'loai_tien':'USD','quoc_gia':Market.labels[i%len(Market.labels)],'trang_thai_vc':status,'nguoi_ban':seller['username'],'ghi_chu':'','dia_chi':'Dia chi TEST','pttt':PaymentMethod.CARD.label}
  r=DataRecord(table=table,data=data,department=sale,created_by_id=seller['id']);r.sync_indexed_columns(cols);records.append(r)
 records=DataRecord.objects.bulk_create(records,batch_size=1000)
 for i,(c,r) in enumerate(zip(customers,records),start):
  orders.append(Order(code=f'TEST-{i:07}',customer=c,department=sale,created_by_id=sellers[i%30]['id'],seller_id=sellers[i%30]['id'],record=r,total=Decimal('40.40'),currency='USD'))
 orders=Order.objects.bulk_create(orders,batch_size=1000)
 ol=[];wi=[]
 for i,(o,r) in enumerate(zip(orders,records),start):
  for product,qty,price in [(products[i%8],2,Decimal('10.10')),(products[(i+1)%8],1,Decimal('20.20'))]:
   ol.append(OrderLine(order=o,product=product,quantity=qty,unit='hop',unit_price=price))
   wi.append(WaybillItem(record=r,product=product,quantity=qty,unit='hop',unit_price=price,paid_amount=0))
 OrderLine.objects.bulk_create(ol,batch_size=2000);WaybillItem.objects.bulk_create(wi,batch_size=2000)
 WaybillAssignment.objects.bulk_create([WaybillAssignment(record=r,delivery_id=handlers[i%10]['id']) for i,r in enumerate(records,start)],batch_size=1000)
 if start%20000==0:print('seeded',start+2000,flush=True)
with connection.cursor() as c:c.execute('ANALYZE')
Path('/runtime/ready.json').write_text(json.dumps({'database':'test_knjsc_code_load','rows':100000,'users':users,'products':[p.code for p in products],'market':Market.US,'payment':PaymentMethod.CARD,'status':ShippingStatus.labels[0]}))
print('READY',Order.objects.count(),DataRecord.objects.count(),WaybillItem.objects.count(),flush=True)
