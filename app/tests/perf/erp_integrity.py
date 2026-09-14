"""Đối chiếu các lần nộp được Locust xác nhận với database test riêng."""
import os,sys,json
from pathlib import Path
from datetime import date,timedelta
sys.path.insert(0,'/app');os.environ.setdefault('DJANGO_SETTINGS_MODULE','knjsc.settings.dev')
import django
django.setup()
from django.conf import settings
from django.db.models import Sum,F
from forms_builder.models import DataRecord
from reports.models import DailyReport
from orders.models import WaybillItem
from orders.constants import Market
assert settings.DATABASES['default']['NAME']=='knjsc_erp_verify'
base=DataRecord.objects.filter(val_date__range=(date(2020,1,1),date(2025,12,31)))
assert base.count()==100000
assert DailyReport.objects.filter(record__in=base).count()==60000
items=WaybillItem.objects.for_records(base.filter(table__code='van_don_moi'))
assert items.count()==80000 and items.aggregate(n=Sum('quantity'))['n']==120000
results=[]
for file in Path('/storage/erp-verification').glob('proof-final-*.json'):
 proof=json.loads(file.read_text())
 start=date(2040,1,1)+timedelta(days=int(proof['offset'])+1)
 reports=DailyReport.objects.filter(report_date__gte=start,report_date__lt=start+timedelta(days=399))
 actual=reports.count()
 assert actual==proof['writes_including_warmup'],(file.name,actual,proof)
 assert not reports.exclude(report_date=F('record__val_date')).exists()
 assert not reports.exclude(record__data__thi_truong__in=Market.labels).exists()
 results.append({'proof':file.name,'persisted':actual,'passed':True})
Path('/storage/erp-verification/integrity.json').write_text(json.dumps({'base_records':100000,'daily_reports':60000,'items':80000,'product_quantity':120000,'runs':results},indent=2))
print(json.dumps(results))
