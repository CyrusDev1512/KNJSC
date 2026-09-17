"""Đối chiếu độc lập xác nhận HTTP với PostgreSQL của bài tải."""
import json
import os
from decimal import Decimal
from pathlib import Path
import django
django.setup()
from django.db import connection
from forms_builder.models import DataRecord

assert connection.settings_dict['HOST']=='knjsc-crm-update-db'
assert connection.settings_dict['NAME'].startswith('test_crm_update_load_')
file=Path(os.environ['LOAD_RESULT'])
result=json.loads(file.read_text())
expected=result.get('expected',{})
assert expected,'Không có oracle cho lượt này'
rows={str(r.pk):r for r in DataRecord.objects.filter(pk__in=expected).select_related('table')}
errors=[]
for pk,wanted in expected.items():
    row=rows.get(pk)
    if row is None:errors.append(f'{pk}: missing');continue
    if row.table.code!=wanted['table'] or row.created_by_id!=wanted['user']:
        errors.append(f'{pk}: identity')
    for key,value in wanted['data'].items():
        actual=row.data.get(key)
        same=Decimal(str(actual))==Decimal(str(value)) if key in {'cpqc','cpo','so_don'} and actual is not None else actual==value
        if not same:errors.append(f'{pk}: {key}')
output={'checked':len(expected),'created':sum(bool(v.get('created')) for v in expected.values()),'errors':errors}
file.with_suffix('.oracle.json').write_text(json.dumps(output,indent=2))
print(json.dumps(output))
assert not errors,errors[:10]
