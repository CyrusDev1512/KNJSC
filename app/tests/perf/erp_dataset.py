"""Synthetic ERP dataset. Explicit isolated database guard; never a dev seed."""
import os,sys
sys.path.insert(0,"/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE","knjsc.settings.dev")
import django
django.setup()
from django.conf import settings
assert settings.DATABASES["default"]["NAME"] == "knjsc_erp_verify", "Test DB only"
from django.contrib.auth import get_user_model
from django.db import connection
from datetime import date,timedelta
from org.models import Department,UserProfile,Team
from forms_builder.models import TableDef,ColumnDef,DataRecord,FormDef,FieldDef,FormField,FormTableLink
from reports.models import DailyReport
from orders.models import WaybillItem,WaybillAssignment,Product
from decimal import Decimal
User=get_user_model()
if DataRecord.objects.count():
 print("Dataset already exists; preserved",flush=True)
else:
 admin=User.objects.create_user("erp_admin",password="erp-test-only-2026")
 UserProfile.objects.create(user=admin,full_name="ERP test admin",rank="admin",must_change_password=False)
 products=[Product.objects.create(code=f"erp-p{i}",name=f"ERP product {i}") for i in range(8)]
 for deptcode,kind,count in [("marketing","mkt",30000),("sale","sale",30000),("van-don","vd",40000)]:
  dept=Department.objects.create(name=deptcode,code=deptcode)
  manager=User.objects.create_user(f"erp_{kind}_manager",password="erp-test-only-2026")
  UserProfile.objects.create(user=manager,full_name=f"ERP {kind} manager",rank="manager",department=dept,must_change_password=False)
  team=Team.objects.create(name=kind,department=dept)
  users=[]
  for n in range(20):
   u=User.objects.create_user(f"erp_{kind}_{n}",password="erp-test-only-2026")
   UserProfile.objects.create(user=u,full_name=f"ERP {kind} staff {n}",rank="staff",department=dept,team=team,must_change_password=False)
   users.append(u)
  table=TableDef.objects.create(code="van_don_moi" if kind=="vd" else f"bao_cao_{kind}",name=f"ERP {kind}",department=dept,created_by=manager)
  specs=[("Ngày","ngay","date","date"),("Marketer" if kind=="mkt" else "Sale","marketer" if kind=="mkt" else "sale","text","seller"),("Sản phẩm","san_pham","choice","product"),("Số Mess","so_mess","integer",""),("Số đơn","so_don","integer",""),("Doanh số","doanh_so","money","revenue"),("Thị trường","thi_truong","choice","")]
  if kind=="mkt":specs.append(("CPQC","cpqc","money",""))
  form=FormDef.objects.create(code=f"bc_{kind}_ngay",name=f"Báo cáo {kind}",table=table,department=dept,created_by=manager)
  for pos,(name,code,typ,meaning) in enumerate(specs):
   opts=["Canada","Hoa Kỳ","Philippines"] if code=="thi_truong" else [p.name for p in products] if code=="san_pham" else []
   c=ColumnDef.objects.create(table=table,name=name,code=code,field_type=typ,meaning=meaning,options=opts,order=pos)
   f=FieldDef.objects.create(department=dept,name=name,code=kind+"_"+code,field_type=typ,meaning=meaning)
   ff=FormField.objects.create(form=form,field=f,order=pos,required=code in ("ngay","san_pham","thi_truong"))
   FormTableLink.objects.create(form_field=ff,column=c)
  for start in range(0,count,1000):
   rows=[]
   for i in range(start,min(start+1000,count)):
    u=users[i%20]; day=date(2020,1,1)+timedelta(days=i//20)
    data={"ngay":day.isoformat(),"san_pham":products[i%8].name,"so_mess":100,"so_don":5,"doanh_so":"1000","cpqc":"200","thi_truong":["Canada","Hoa Kỳ","Philippines"][i%3],"quoc_gia":["Canada","Hoa Kỳ","Philippines"][i%3],"trang_thai_vc":"Đang giao"}
    rows.append(DataRecord(table=table,department=dept,team=team,created_by=u,data=data,val_date=day,val_product=products[i%8].name,val_seller=u.username,val_revenue=Decimal(1000)))
   DataRecord.objects.bulk_create(rows)
   if kind!="vd":
    DailyReport.objects.bulk_create([DailyReport(form=form,record=r,created_by=r.created_by,department=dept,team=team,report_date=r.val_date) for r in rows])
   else:
    WaybillAssignment.objects.bulk_create([WaybillAssignment(record=r,delivery=r.created_by) for r in rows])
    WaybillItem.objects.bulk_create([WaybillItem(record=r,product=products[(start+j+k)%8],quantity=k+1,unit_price=Decimal(10),paid_amount=Decimal(0)) for j,r in enumerate(rows) for k in range(2)])
  leader=users[19]
  leader.profile.rank="leader"
  leader.profile.save(update_fields=["rank"])
  team.leader=leader
  team.save(update_fields=["leader"])
  print(kind,count,flush=True)
 with connection.cursor() as cursor:cursor.execute("ANALYZE")
 print("Dataset: 100000 records",flush=True)
