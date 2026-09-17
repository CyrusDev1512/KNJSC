"""Chuẩn bị vùng cuối không trùng ô Staff đang sửa; chỉ đọc DB test và cập nhật oracle riêng."""
import json
import os
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE','optimization_settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from django.db import connection
from forms_builder.models import DataRecord,TableDef

assert connection.settings_dict['NAME']=='test_knjsc_opt_after300'
file=Path(os.environ['OPT_MANIFEST']);data=json.loads(file.read_text())
user=get_user_model().objects.get(pk=data['actors'][0]['user'])
table=TableDef.objects.get(code='van_don_moi')
offset=298000
ids=list(DataRecord.objects.in_scope(user,table=table).order_by('created_at','id').values_list('pk',flat=True)[offset:offset+2000])
assert len(ids)==2000 and not set(ids).intersection(actor['row'] for actor in data['actors'])
data['actors'][0]['bulk_ids']=ids;data['bulk_offset']=offset;data['bulk_values_only']=True
file.write_text(json.dumps(data))
print('Oracle: 2.000 dòng cuối, không trùng đích sửa đơn ô; không sửa dữ liệu nghiệp vụ.')
