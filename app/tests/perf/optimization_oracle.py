"""Đóng băng ID tham chiếu bằng ORM chung trước mỗi lượt đo, không qua API."""
import json
import os
from pathlib import Path
import optimization_wsgi
from django.contrib.auth import get_user_model
from django.http import QueryDict
from django.db import transaction
from forms_builder.models import TableDef
from crm.services.grid_service import build_grid

path=Path(os.environ['OPT_MANIFEST'])
manifest=json.loads(path.read_text())
assert manifest['database']==os.environ['POSTGRES_DB']
with transaction.atomic():
    table=TableDef.objects.get(code='van_don_moi')
    for actor in manifest['actors']:
        user=get_user_model().objects.get(pk=actor['user'])
        qs=build_grid(user,QueryDict(),table=table).queryset
        actor['total']=qs.count()
        offsets=sorted(set([0,100,1000,actor['total']//2,max(0,actor['total']-100)]))
        actor['pages']={str(n):list(qs.values_list('pk',flat=True)[n:n+100]) for n in offsets}
        if actor is manifest['actors'][0]:actor['bulk_ids']=list(qs.values_list('pk',flat=True)[:2000])
        filtered=build_grid(user,QueryDict('f_quoc_gia=USA'),table=table).queryset
        actor['filtered']={'total':filtered.count(),'ids':list(filtered.values_list('pk',flat=True)[:100])}
path.write_text(json.dumps(manifest))
