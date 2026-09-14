"""Fixture E2E lưới chung, Chrome host kết nối DB kiểm thử độc lập."""
import json, os, time
from pathlib import Path
import pytest
from forms_builder.models import ColumnDef, TableDef
from forms_builder.meaning import Meaning
from .test_shared_grid import generic


@pytest.mark.trinh_duyet
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(os.environ.get('CRM_UPDATE_BROWSER')!='1',reason='Cần Chrome host và server test riêng')
def test_shared_browser(live_server, generic, nguoi_dung, settings):
    from django.db import connection
    assert connection.settings_dict['NAME'].startswith('test_')
    settings.DEBUG=True;settings.ALLOWED_HOSTS=['*']
    table,row=generic
    empty=TableDef.objects.create(code='shared_empty',name='Bảng rỗng',department=table.department)
    ColumnDef.objects.create(table=empty,code='bill',name='Nội dung',field_type='text',required=True)
    ColumnDef.objects.filter(table=table,code='bill').update(required=True)
    for code in ['a','b']:
        ColumnDef.objects.create(table=table,name=code,code=code,field_type='integer')
    ColumnDef.objects.create(table=table,name='Tổng',code='total',field_type='decimal',is_computed=True,
        compute_op='add',compute_left='a',compute_right='b')
    row.data.update(a=1,b=2);row.save()
    ColumnDef.objects.create(table=table,code='suggestion',name='Người bán gợi ý',field_type='choice',meaning=Meaning.SELLER)
    ColumnDef.objects.create(table=table,code='moment',name='Ngày giờ',field_type='datetime')
    row.data.update(suggestion='Người đã nghỉ',moment='2026-09-12T10:33:00+07:00');row.save()
    root=Path('/evidence');result=root/'shared-browser-result.json';result.unlink(missing_ok=True)
    (root/'shared-browser-ready.json').write_text(json.dumps({'table':table.code,'row':row.pk,'name':table.name,'empty':empty.code}))
    try:
        deadline=time.monotonic()+600
        while not result.exists() and time.monotonic()<deadline:time.sleep(.2)
        assert result.exists(),'Chưa có kết quả Chrome'
        outcome=json.loads(result.read_text())
        assert outcome['ok'],outcome
    finally:(root/'shared-browser-ready.json').unlink(missing_ok=True)
