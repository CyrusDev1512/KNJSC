import json
from pathlib import Path
from decimal import Decimal
import django
django.setup()
from django.db import connection
from orders.models import Order,WaybillItem
assert connection.settings_dict['NAME']=='test_knjsc_code_load' and connection.settings_dict['HOST']=='knjsc-code-db'
r=Path('/runtime/results');m=json.loads((r/'e2e.json').read_text());errors=[]
for row in m['orders']:
 o=Order.objects.select_related('record','customer').get(code=row['code'])
 if o.seller_id!=row['actor'] or o.customer.phone!=row['phone'] or o.total!=Decimal('40.40') or o.lines.count()!=2 or WaybillItem.objects.filter(record=o.record).count()!=2:errors.append(row['code'])
 if list(o.lines.order_by('id').values_list('unit',flat=True))!=['hộp','túi']:errors.append('units '+row['code'])
result={'orders':len(m['orders']),'cases':len(m['cases']),'errors':errors+m['errors']}
(r/'e2e-integrity.json').write_text(json.dumps(result));print(json.dumps(result));assert not result['errors']
