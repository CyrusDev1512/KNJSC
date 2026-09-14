"""AC-27.3/6: biên nhận đã commit vẫn xác nhận được sau đổi cấu trúc."""
import uuid
import pytest
from django.http import QueryDict
from forms_builder.models import ColumnDef,DataRecord
from crm.services import master_grid_service as grid
from .test_shared_grid import generic

pytestmark=pytest.mark.django_db


def test_committed_create_retry_after_schema_change_does_not_create_twice(generic,nguoi_dung):
    table,row=generic;user=nguoi_dung['staff_mkt']
    schema=grid.block(user,table,QueryDict())['schema_version']
    packet={'operation':str(uuid.uuid4()),'schema_version':schema,'cells':[
        {'id':-1,'column':'bill','old':None,'value':'Đã được xác nhận ở server'}]}
    first=grid.save(user,table,packet)
    ColumnDef.objects.create(table=table,code='added',name='Cột vừa thêm',field_type='text')
    retry=grid.save(user,table,packet)
    assert retry['replayed'] and retry['id_map']==first['id_map']
    assert DataRecord.objects.filter(table=table).count()==2
