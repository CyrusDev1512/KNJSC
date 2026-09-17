"""CRM-UPDATE: tính nguyên tử, CAS, kiểu, quyền và vòng đời."""
import threading, uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import pytest
from django.db import connection, connections, transaction
from django.http import QueryDict
from core.constants import JobKind, JobStatus
from core.models import BackgroundJob
from core.exceptions import BusinessError, OutOfScopeError
from forms_builder.models import ColumnDef, DataRecord
from forms_builder.services import lifecycle_service as life, record_service, form_service
from crm.services import master_grid_service as grid
from .test_shared_grid import generic

pytestmark=pytest.mark.django_db


def packet(row,code,old,value,**extra):
    return {'operation':str(uuid.uuid4()),'cells':[{'id':row.pk,'column':code,'old':old,'value':value}],**extra}


@pytest.fixture
def calculated(generic):
    table,row=generic
    for code in ['a','b']:ColumnDef.objects.create(table=table,code=code,name=code,field_type='decimal')
    ColumnDef.objects.create(table=table,code='total',name='Tổng',field_type='decimal',is_computed=True,
        compute_op='add',compute_left='a',compute_right='b')
    row.data.update(a='1.25',b='2.35');row.save()
    return table,row


def test_formula_atomic_and_style_preserved(calculated,nguoi_dung):
    table,row=calculated;user=nguoi_dung['staff_mkt']
    row.style={'bill':{'b':1,'fmt':'text'}};row.save()
    result=grid.save(user,table,packet(row,'a','1.25','2.25'))
    assert Decimal(result['rows'][0]['cells']['total']['value'])==Decimal('4.60')
    grid.save(user,table,packet(row,'a','2.25','1.25',kind='undo'))
    row.refresh_from_db();assert Decimal(row.data['total'])==Decimal('3.60')
    assert row.style['bill']=={'b':1,'fmt':'text'}
    payload=packet(row,'bill','Bình thường','Không được ghi')
    payload['cells'].append({'id':row.pk,'column':'total','old':row.data['total'],'value':99})
    with pytest.raises(BusinessError):grid.save(user,table,payload)
    row.refresh_from_db();assert row.data['bill']=='Bình thường'


@pytest.mark.parametrize('field,value,bad',[('date','2026-09-12','31/99/2026'),('datetime','2026-09-12T10:33','sai'),('boolean','true','khong-hop-le'),('integer','25','abc'),('money','1234.50','abc')])
def test_types_and_atomic_bad_value(generic,nguoi_dung,field,value,bad):
    table,row=generic;user=nguoi_dung['staff_mkt']
    ColumnDef.objects.create(table=table,code='typed',name='Có kiểu',field_type=field)
    grid.save(user,table,packet(row,'typed',None,value));row.refresh_from_db();saved=row.data['typed']
    p=packet(row,'typed',saved,bad);p['cells'].append({'id':row.pk,'column':'bill','old':'Bình thường','value':'Không được ghi'})
    with pytest.raises(BusinessError):grid.save(user,table,p)
    row.refresh_from_db();assert row.data['typed']==saved and row.data['bill']=='Bình thường'


def test_schema_change_keeps_all_values(generic,nguoi_dung):
    table,row=generic;user=nguoi_dung['staff_mkt'];schema=grid.block(user,table,QueryDict())['schema_version']
    ColumnDef.objects.create(table=table,code='extra',name='Mới',field_type='text')
    with pytest.raises(BusinessError):grid.save(user,table,packet(row,'bill','Bình thường','Không',schema_version=schema))
    row.refresh_from_db();assert row.data['bill']=='Bình thường'


@pytest.mark.parametrize('path',['o/{id}/bill/','luu-o/','dinh-dang/','dong-moi/','xoa-dong/','khoi-phuc-dong/'])
def test_retired_writes_cannot_bypass_cas(client,generic,nguoi_dung,path):
    table,row=generic;client.force_login(nguoi_dung['staff_mkt'])
    response=client.post('/bang-tinh/'+table.code+'/'+path.format(id=row.pk),{'gia_tri':'Không'})
    assert response.status_code==409
    assert 'tải lại trang' in response.content.decode()
    row.refresh_from_db();assert row.data['bill']=='Bình thường'


def test_deleted_guard_blocks_services_and_pages(client,generic,nguoi_dung):
    table,row=generic;admin=nguoi_dung['admin']
    life.delete(admin,table,table.name)
    with pytest.raises(OutOfScopeError):record_service.create_record(table,{'bill':'Không'},actor=admin)
    with pytest.raises(OutOfScopeError):record_service.update_cell(row,'bill','Không',actor=admin)
    with pytest.raises(OutOfScopeError):form_service.create_form(name='Không',code='no',department=table.department,table=table,actor=admin)
    client.force_login(admin)
    for suffix in ['','du-lieu/','lich-su/?record='+str(row.pk),'xuat/','moi-nhat/','loc/bill/']:
        assert client.get('/bang-tinh/'+table.code+'/'+suffix).status_code in (403,404)
    assert client.get('/bang-da-xoa/').status_code==200


@pytest.mark.parametrize('kind',[JobKind.IMPORT,JobKind.RECOMPUTE])
def test_pending_writer_blocks_delete(generic,nguoi_dung,kind):
    table,row=generic
    job=BackgroundJob.objects.create(kind=kind,status=JobStatus.PENDING,target_type='table',target_id=table.code,title='Test',created_by=nguoi_dung['admin'])
    with pytest.raises(BusinessError,match=str(job.pk)):life.delete(nguoi_dung['admin'],table,table.name)
    assert DataRecord.objects.filter(pk=row.pk).exists()


@pytest.mark.django_db(transaction=True)
def test_concurrent_inputs_recompute_from_locked_row(calculated,nguoi_dung):
    table,row=calculated;user=nguoi_dung['staff_mkt'];barrier=threading.Barrier(2)
    def change(code,old,new):
        try:
            barrier.wait(timeout=5)
            return grid.save(user,table,packet(row,code,old,new))
        finally:connections.close_all()
    with ThreadPoolExecutor(2) as pool:
        results=[pool.submit(change,'a','1.25','10.25'),pool.submit(change,'b','2.35','20.35')]
        for result in results:result.result(timeout=15)
    row.refresh_from_db();assert Decimal(row.data['total'])==Decimal('30.60')


@pytest.mark.django_db(transaction=True)
def test_lifecycle_lock_allows_shared_writes_then_blocks_deleted(generic,nguoi_dung):
    table,row=generic;held=threading.Event();release=threading.Event();deleted=threading.Event()
    def holder():
        try:
            with transaction.atomic():life.lock(table);held.set();assert release.wait(8)
        finally:connections.close_all()
    def deleter():
        try:life.delete(nguoi_dung['admin'],table,table.name);deleted.set()
        finally:connections.close_all()
    with ThreadPoolExecutor(2) as pool:
        h=pool.submit(holder);assert held.wait(5)
        # Một khóa chia sẻ khác không đợi khóa chia sẻ đang giữ.
        with transaction.atomic():
            with connection.cursor() as c:
                c.execute('SELECT pg_try_advisory_xact_lock_shared(%s,%s)',[life.LOCK_NAMESPACE,table.pk]);assert c.fetchone()[0]
        d=pool.submit(deleter);assert not deleted.wait(.15);release.set();h.result(5);d.result(5)
    with pytest.raises(OutOfScopeError):record_service.update_cell(row,'bill','Không',actor=nguoi_dung['admin'])


def test_create_2000_cells_uses_batches(generic,nguoi_dung,django_assert_max_num_queries):
    table,row=generic;user=nguoi_dung['staff_mkt']
    # Làm ấm hồ sơ/quyền, không tính truy vấn phiên đầu.
    grid.block(user,table,QueryDict())
    payload={'operation':str(uuid.uuid4()),'kind':'paste','cells':[
        {'id':-i,'column':code,'old':None,'value':str(i)}
        for i in range(1,501) for code in ['bill','phu_trach_vd','san_pham','ma_don']]}
    with django_assert_max_num_queries(35):result=grid.save(user,table,payload)
    assert len(result['id_map'])==500 and DataRecord.objects.filter(table=table).count()==501
    assert grid.save(user,table,payload)['replayed']
    assert DataRecord.objects.filter(table=table).count()==501


def test_invalid_new_row_reports_actual_column(calculated,nguoi_dung):
    table,row=calculated
    with pytest.raises(BusinessError) as error:
        grid.save(nguoi_dung['staff_mkt'],table,{'operation':str(uuid.uuid4()),'cells':[
            {'id':-1,'column':'bill','old':None,'value':'Nháp'},
            {'id':-1,'column':'a','old':None,'value':'Không phải số'}]})
    assert error.value.pk==-1 and error.value.column=='a'
    assert DataRecord.objects.filter(table=table).count()==1


def test_csrf_required_for_lifecycle_and_grid(generic,nguoi_dung):
    from django.test import Client
    client=Client(enforce_csrf_checks=True);client.force_login(nguoi_dung['admin'])
    table,row=generic
    for suffix,body in [('xoa-bang/',{'name':table.name}),('khoi-phuc-bang/',{}),('luu-json/',{})]:
        assert client.post('/bang-tinh/'+table.code+'/'+suffix,body).status_code==403


def test_generic_export_revocation_and_deleted_table(generic,nguoi_dung,settings,tmp_path,monkeypatch):
    from forms_builder.services import export_service
    table,row=generic;user=nguoi_dung['staff_mkt']
    settings.STORAGE_DIR=tmp_path;settings.EXPORT_DIR=tmp_path/'exports'
    monkeypatch.setattr(export_service,'EXPORT_SYNC_MAX_ROWS',0)
    kind,job=export_service.export(user,table,QueryDict(),builder='grid')
    job.refresh_from_db();assert kind=='job' and job.status==JobStatus.DONE
    assert job.summary['exported_row_ids']==[row.pk]
    assert export_service.result_file(job).exists()
    life.delete(nguoi_dung['admin'],table,table.name)
    with pytest.raises(BusinessError):export_service.check_download(job,user)
    life.restore(nguoi_dung['admin'],table)
    export_service.check_download(job,user)
    # Bảng vẫn trong phòng ban nhưng dòng không còn thuộc người xuất.
    row.created_by=nguoi_dung['manager_mkt'];row.save()
    with pytest.raises(BusinessError):export_service.check_download(job,user)


def test_replay_checks_current_grant(generic,nguoi_dung):
    from forms_builder.services import grant_service
    from forms_builder.models import GrantAction
    table,row=generic;user=nguoi_dung['staff_sale_1'];admin=nguoi_dung['admin']
    permission=grant_service.grant(table=table,user=user,action=GrantAction.EDIT,actor=admin)
    payload=packet(row,'bill','Bình thường','Grant')
    grid.save(user,table,payload)
    grant_service.revoke(permission,actor=admin)
    with pytest.raises(OutOfScopeError):grid.save(user,table,payload)


def test_undo_creation_conflict_rolls_back_other_cells(client,generic,nguoi_dung):
    table,row=generic;user=nguoi_dung['staff_mkt'];operation=str(uuid.uuid4())
    result=grid.save(user,table,{'operation':operation,'cells':[
        {'id':row.pk,'column':'bill','old':'Bình thường','value':'Đổi'},
        {'id':-1,'column':'bill','old':None,'value':'Mới'}]})
    new=DataRecord.objects.get(pk=result['id_map']['-1']);version=new.updated_at.isoformat()
    grid.save(nguoi_dung['manager_mkt'],table,packet(new,'bill','Mới','Đồng nghiệp'))
    with pytest.raises(BusinessError):grid.save(user,table,{'operation':str(uuid.uuid4()),'kind':'undo',
        'cells':[{'id':row.pk,'column':'bill','old':'Đổi','value':'Bình thường'}],
        'row_changes':[{'id':new.pk,'source':operation,'action':'delete','version':version}]})
    row.refresh_from_db();new.refresh_from_db()
    assert row.data['bill']=='Đổi' and new.deleted_at is None and new.data['bill']=='Đồng nghiệp'


def test_restore_detaches_deleted_folder(generic,nguoi_dung):
    from forms_builder.services import folder_service
    table,row=generic;admin=nguoi_dung['admin']
    folder=folder_service.create_folder(name='Thư mục',department=table.department,actor=admin)
    table.folder=folder;table.save()
    life.delete(admin,table,table.name);folder_service.delete_folder(folder,actor=admin)
    restored=life.restore(admin,table)
    assert restored.pk==table.pk and restored.folder is None
