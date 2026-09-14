"""CRM-UPDATE — cùng lõi JSON, không nhận nhầm cột nghiệp vụ."""
import uuid
import pytest
from forms_builder.models import TableDef, ColumnDef, DataRecord
from forms_builder.meaning import FieldType
from forms_builder.services import record_service

pytestmark = pytest.mark.django_db


@pytest.fixture
def generic(departments, nguoi_dung, settings):
    settings.GRID_ONLY_TABLES = set()
    table = TableDef.objects.create(code='shared_marketing', name='Marketing chung', department=departments['mkt'])
    for code in ['bill', 'phu_trach_vd', 'san_pham', 'ma_don']:
        ColumnDef.objects.create(table=table, code=code, name=code, field_type=FieldType.TEXT)
    row = record_service.create_record(table, {'bill':'Bình thường'}, actor=nguoi_dung['staff_mkt'])
    return table, row


def test_generic_json_and_plain_columns(client, generic, nguoi_dung):
    table, row = generic
    client.force_login(nguoi_dung['staff_mkt'])
    response = client.get(f'/bang-tinh/{table.code}/du-lieu/')
    assert response.status_code == 200
    data = response.json()
    assert data['total'] == 1
    assert all(not c['protected'] and not c['assignment'] and not c['detail'] for c in data['columns'])
    assert 'payments' not in data['rows'][0]['cells']['bill']
    assert data['rows'][0]['detail_url'] is None
    response = client.post(f'/bang-tinh/{table.code}/luu-json/', {'operation':str(uuid.uuid4()),
        'cells':[{'id':row.pk,'column':'phu_trach_vd','old':None,'value':'Cột thường'}]}, content_type='application/json')
    assert response.status_code == 200
    row.refresh_from_db()
    assert row.data['phu_trach_vd'] == 'Cột thường'


def test_generic_page_uses_shared_shell(client, generic, nguoi_dung):
    client.force_login(nguoi_dung['staff_mkt'])
    response = client.get(f'/bang-tinh/{generic[0].code}/')
    assert response.status_code == 200
    html = response.content.decode()
    assert 'id="master-grid"' in html and 'js/bang-tinh-o.js' not in html


def test_metadata_distinguishes_suggestions_from_strict_choices(client,generic,nguoi_dung):
    from forms_builder.meaning import Meaning
    table,row=generic
    ColumnDef.objects.create(table=table,code='seller',name='Người bán',field_type=FieldType.CHOICE,meaning=Meaning.SELLER)
    ColumnDef.objects.create(table=table,code='strict',name='Danh sách chặt',field_type=FieldType.CHOICE,options=['A','B'])
    client.force_login(nguoi_dung['staff_mkt'])
    columns={c['code']:c for c in client.get(f'/bang-tinh/{table.code}/du-lieu/').json()['columns']}
    assert columns['seller']['choice_strict'] is False and columns['seller']['options']
    assert columns['strict']['choice_strict'] is True


def test_paste_create_update_atomic_retry_and_undo(client, generic, nguoi_dung):
    table,row=generic
    client.force_login(nguoi_dung['staff_mkt'])
    url=f'/bang-tinh/{table.code}/luu-json/'
    operation=str(uuid.uuid4())
    payload={'operation':operation,'kind':'paste','cells':[
        {'id':row.pk,'column':'bill','old':'Bình thường','value':'Đã sửa'},
        {'id':-1,'column':'bill','old':None,'value':'Dòng mới'}]}
    first=client.post(url,payload,content_type='application/json')
    assert first.status_code==200
    data=first.json();new_id=data['id_map']['-1']
    again=client.post(url,payload,content_type='application/json')
    assert again.status_code==200 and again.json()['id_map']==data['id_map']
    assert DataRecord.objects.filter(table=table).count()==2
    new=DataRecord.objects.get(pk=new_id)
    undo={'operation':str(uuid.uuid4()),'kind':'undo', 'cells':[
        {'id':row.pk,'column':'bill','old':'Đã sửa','value':'Bình thường'}],
        'row_changes':[{'id':new_id,'action':'delete','source':operation,'version':new.updated_at.isoformat()}]}
    response=client.post(url,undo,content_type='application/json')
    assert response.status_code==200
    new=DataRecord.all_objects.get(pk=new_id)
    assert new.deleted_at and DataRecord.objects.filter(table=table).count()==1
    redo={'operation':str(uuid.uuid4()),'kind':'redo','cells':[],
        'row_changes':[{'id':new_id,'action':'restore','source':operation,'version':new.updated_at.isoformat()}]}
    assert client.post(url,redo,content_type='application/json').status_code==200
    assert DataRecord.objects.filter(table=table).count()==2


def test_invalid_paste_does_not_leave_created_rows(client, generic, nguoi_dung):
    table,row=generic
    ColumnDef.objects.create(table=table,code='required',name='Bắt buộc',field_type=FieldType.TEXT,required=True)
    client.force_login(nguoi_dung['staff_mkt'])
    response=client.post(f'/bang-tinh/{table.code}/luu-json/',{'operation':str(uuid.uuid4()),'cells':[
        {'id':-1,'column':'bill','old':None,'value':'Chưa đủ'},
        {'id':row.pk,'column':'bill','old':'Bình thường','value':'Không được đổi'}]},content_type='application/json')
    assert response.status_code==400
    row.refresh_from_db()
    assert row.data['bill']=='Bình thường' and DataRecord.objects.filter(table=table).count()==1
