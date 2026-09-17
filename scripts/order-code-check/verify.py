import os,json
from pathlib import Path
from decimal import Decimal
import django
django.setup()
from django.db import connection
from orders.models import Order,OrderLine,WaybillItem,WaybillAssignment
from forms_builder.models import DataRecord
from crm.models import GridCellHistory
assert connection.settings_dict['NAME']=='test_knjsc_code_load' and connection.settings_dict['HOST']=='knjsc-code-db'
phase=os.environ['PHASE'];r=Path('/runtime/results');m=json.loads((r/(phase+'.json')).read_text());errors=[]
for item in m['orders']:
 o=Order.objects.filter(code=item['code']).first()
 if not o or o.seller_id!=item['actor'] or o.note!='LOADTEST-'+item['token'] or o.total!=Decimal('40.40') or o.lines.count()!=2 or not o.record_id:errors.append({'kind':'order','code':item['code']});continue
 if o.record.data.get('gia_tien')!='40.40' or WaybillItem.objects.filter(record_id=o.record_id).count()!=2:errors.append({'kind':'snapshot','code':o.code})
checks=dict(m['writes']);browser=r/(phase+'-browser.json')
if browser.exists():
 for v in json.loads(browser.read_text()).get('writes',[]):
  h=GridCellHistory.objects.filter(after=v['value'],column='ghi_chu',receipt__actor__username='test_delivery_09').first()
  if h is None:errors.append({'kind':'browser_history_missing','id':v['id']});continue
  if v['id'] and h.record_id!=v['id']:errors.append({'kind':'browser_wrong_record','id':v['id']})
  checks[str(h.record_id)]=v['value']
actual={str(i):d.get('ghi_chu') for i,d in DataRecord.objects.filter(pk__in=checks).values_list('pk','data')}
for k,v in checks.items():
 if actual.get(k)!=v:errors.append({'kind':'cell','id':k})
attempts={i['token'] for i in m['attempts']};ack={i['token'] for i in m['orders']}
persisted=set(Order.objects.filter(note__in=['LOADTEST-'+i for i in attempts]).values_list('note',flat=True))
unknown=[i for i in attempts-ack if 'LOADTEST-'+i in persisted]
result={'orders_acknowledged':len(m['orders']),'order_attempts':len(attempts),'persisted_attempts':len(persisted),'committed_without_success_response':len(unknown),'verified_cells':len(checks),'errors':errors,'total_orders':Order.objects.count(),'total_records':DataRecord.objects.count(),'new_orders_assigned':WaybillAssignment.objects.filter(record__order__note__startswith='LOADTEST-').count()}
(r/(phase+'-integrity.json')).write_text(json.dumps(result,indent=2));print(json.dumps(result))
