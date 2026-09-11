"""AC-21.1, AC-21.2, AC-21.3, AC-21.4, AC-21.5, AC-21.7 — Lưới master: phạm vi, khối dữ liệu, CAS và gửi lại an toàn."""
import uuid
import pytest
from .test_waybill_feedback import feedback, delivery_leader, assign_rows
from forms_builder.models import DataRecord

pytestmark = pytest.mark.django_db
BASE = '/bang-tinh/van_don_moi/'


def write(client, row, column='ghi_chu', old=None, value='Ghi chú mới', operation=None):
    return client.post(BASE + 'luu-json/', {'operation': operation or str(uuid.uuid4()),
        'cells': [{'id': row.pk, 'column': column, 'old': old, 'value': value}]}, content_type='application/json')


def test_blocks_scoped_and_stable(client, feedback, nguoi_dung):
    client.force_login(nguoi_dung['admin'])
    response = client.get(BASE + 'du-lieu/')
    assert response.status_code == 200
    data = response.json()
    assert data['total'] == 2 and len(data['rows']) == 2
    assert {r['id'] for r in data['rows']} == {r.pk for r in feedback[2]}
    client.force_login(nguoi_dung['staff_vd'])
    response = client.get(BASE + 'du-lieu/')
    assert response.status_code in (200, 403, 404)
    if response.status_code == 200:
        assert response.json()['rows'] == []


def test_same_cell_conflict_but_other_cell_survives(client, feedback, nguoi_dung):
    """AC-21.3 — CAS và giữ thay đổi khác ô."""
    client.force_login(nguoi_dung['admin'])
    row = feedback[2][0]
    old = row.data.get('ghi_chu')
    assert write(client, row, old=old).status_code == 200
    assert write(client, row, old=old, value='Ghi đè').status_code == 409
    assert write(client, row, column='bang', old=row.data.get('bang'), value='CA').status_code == 200
    row.refresh_from_db()
    assert row.data['ghi_chu'] == 'Ghi chú mới' and row.data['bang'] == 'CA'


def test_replay_and_changed_payload(client, feedback, nguoi_dung):
    client.force_login(nguoi_dung['admin'])
    row = feedback[2][0]
    operation = str(uuid.uuid4())
    assert write(client, row, old=row.data.get('ghi_chu'), operation=operation).status_code == 200
    replay = write(client, row, old=row.data.get('ghi_chu'), operation=operation)
    assert replay.status_code == 200 and replay.json()['replayed']
    assert write(client, row, value='Khác', operation=operation).status_code == 409


def test_protected_and_invalid_batch_atomic(client, feedback, nguoi_dung):
    client.force_login(nguoi_dung['admin'])
    row = feedback[2][0]
    result = client.post(BASE + 'luu-json/', {'operation': str(uuid.uuid4()), 'cells': [
        {'id': row.pk, 'column': 'ghi_chu', 'old': row.data.get('ghi_chu'), 'value': 'Không được lưu'},
        {'id': row.pk, 'column': 'phu_trach_vd', 'old': None, 'value': 'admin'}]}, content_type='application/json')
    assert result.status_code == 400
    row.refresh_from_db()
    assert row.data.get('ghi_chu') != 'Không được lưu'


def test_replay_revoked_scope_denied(client, feedback, nguoi_dung, delivery_leader):
    row = feedback[2][0]
    assign_rows(delivery_leader, [row], delivery=nguoi_dung['staff_vd'].pk)
    client.force_login(nguoi_dung['staff_vd'])
    operation = str(uuid.uuid4())
    assert write(client, row, old=row.data.get('ghi_chu'), operation=operation).status_code == 200
    assign_rows(delivery_leader, [row], delivery=None)
    assert write(client, row, old=row.data.get('ghi_chu'), operation=operation).status_code in (403, 404)


def test_statistics_standalone_and_counts_missing_items(client, feedback, nguoi_dung):
    client.force_login(nguoi_dung['admin'])
    response = client.get('/thong-ke/', {'nguon': 'van_don_moi'})
    assert response.status_code == 200
    assert response.context['summary']['orders'] == 2
    assert response.context['summary']['missing'] == 0
    row = feedback[2][0]
    row.waybill_items.all().delete()
    response = client.get('/thong-ke/', {'nguon': 'van_don_moi'})
    assert response.context['summary']['orders'] == 2
    assert response.context['summary']['missing'] == 1
    old = client.get('/van-don/thong-ke/?sp=feedback-0')
    assert old.status_code == 302 and 'sp=feedback-0' in old.url


def test_grid_shell_has_no_embedded_statistics_or_old_controllers(client, feedback, nguoi_dung):
    client.force_login(nguoi_dung['admin'])
    html = client.get(BASE).content.decode()
    assert 'master-grid.js' in html
    assert 'js/bang-tinh.js' not in html and 'vd-statistics' not in html


def test_waybill_master_has_scoped_design_and_three_frozen_identity_columns(
        client, feedback, nguoi_dung):
    client.force_login(nguoi_dung['admin'])
    html = client.get(BASE).content.decode()
    assert 'class="mg-root mg-waybill-master"' in html
    metadata = client.get(BASE + 'du-lieu/').json()['columns']
    assert [column['code'] for column in metadata if column['frozen']] == [
        'ma_don', 'ten_khach', 'so_dien_thoai',
    ]


def test_block_limit_and_invalidated_query(client, feedback, nguoi_dung):
    """AC-21.2 — Khối tối đa 100 dòng và phiên bản truy vấn."""
    table, _, rows = feedback
    DataRecord.objects.bulk_create([DataRecord(table=table, created_by=nguoi_dung['admin'],
        data={**rows[0].data, 'ma_don': f'BLOCK-{i:04d}'}) for i in range(130)])
    client.force_login(nguoi_dung['admin'])
    first = client.get(BASE+'du-lieu/').json()
    second = client.get(BASE+'du-lieu/', {'offset':100,'version':first['version']}).json()
    assert first['total'] == 132 and len(first['rows']) == 100 and len(second['rows']) == 32
    assert not {r['id'] for r in first['rows']} & {r['id'] for r in second['rows']}
    row=rows[0]
    assert write(client,row,old=row.data.get('ghi_chu')).status_code == 200
    assert client.get(BASE+'du-lieu/', {'offset':100,'version':first['version']}).status_code == 409
    assert client.get(BASE+'du-lieu/', {'offset':-1}).status_code == 400


def test_undo_rejects_changed_cell_and_limits(client, feedback, nguoi_dung):
    client.force_login(nguoi_dung['admin'])
    row=feedback[2][0]
    assert write(client,row,old=row.data.get('ghi_chu'),value='A').status_code == 200
    assert write(client,row,old='A',value='B').status_code == 200
    assert write(client,row,old='A',value=None).status_code == 409
    row.refresh_from_db(); assert row.data['ghi_chu']=='B'
    payload={'operation':str(uuid.uuid4()),'cells':[{'id':row.pk,'column':'ghi_chu','old':'B','value':'C'}]*2001}
    assert client.post(BASE+'luu-json/',payload,content_type='application/json').status_code == 400


@pytest.mark.django_db(transaction=True)
def test_concurrent_cells_and_receipt(feedback, nguoi_dung, make_user):
    """AC-21.3 — Hai tài khoản sửa khác ô đồng thời giữ cả hai kết quả."""
    from core.constants import Rank
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import close_old_connections, connections
    from django.contrib.auth import get_user_model
    from crm.services import master_grid_service as service
    from crm.models import GridMutationReceipt
    row=feedback[2][0]; actor_id=nguoi_dung['admin'].pk
    second_actor_id=make_user('another_grid_editor',Rank.ADMIN).pk
    barrier=Barrier(2)
    def worker(column):
        close_old_connections()
        try:
            actor=get_user_model().objects.get(pk=actor_id if column=='ghi_chu' else second_actor_id)
            table=service.table_for(actor,'van_don_moi')
            barrier.wait(timeout=10)
            return service.save(actor,table,{'operation':str(uuid.uuid4()),'cells':[
                {'id':row.pk,'column':column,'old':row.data.get(column),'value':'đồng thời'}]})
        finally: connections.close_all()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(worker,['ghi_chu','bang']))
    assert all(r['changed']==1 for r in results)
    row.refresh_from_db(); assert row.data['ghi_chu']==row.data['bang']=='đồng thời'
    assert GridMutationReceipt.objects.count()==2


@pytest.mark.django_db(transaction=True)
def test_migration_roundtrip_keeps_business_rows(feedback):
    """AC-21.7 — Đảo migration biên nhận không đổi dòng nghiệp vụ."""
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor
    ids=list(DataRecord.objects.values_list('id',flat=True))
    executor=MigrationExecutor(connection)
    executor.migrate([('crm',None)])
    try:
        assert list(DataRecord.objects.values_list('id',flat=True))==ids
    finally:
        executor=MigrationExecutor(connection);executor.migrate(executor.loader.graph.leaf_nodes())
    assert list(DataRecord.objects.values_list('id',flat=True))==ids


def test_draft_visibility_probe_rechecks_assignment(client, feedback, nguoi_dung, delivery_leader):
    row=feedback[2][0]
    assign_rows(delivery_leader, [row], delivery=nguoi_dung['staff_vd'].pk)
    client.force_login(nguoi_dung['staff_vd'])
    url=BASE+'du-lieu/?check_id='+str(row.pk)
    assert client.get(url).json()=={'visible': True}
    assign_rows(delivery_leader, [row], delivery=None)
    assert client.get(url).status_code==403


def test_chart_top_ten_keeps_full_reconciliation(client, feedback, nguoi_dung):
    table,_,source=feedback
    DataRecord.objects.bulk_create([DataRecord(table=table,created_by=nguoi_dung['admin'],
        val_date=source[0].val_date,
        data={**source[0].data,'quoc_gia':f'Thị trường {i:02d}'}) for i in range(28)])
    client.force_login(nguoi_dung['admin'])
    response=client.get('/thong-ke/',{'nguon':'van_don_moi','chart_market':2})
    chart=response.context['charts'][2]
    assert len(chart['groups'])==10
    assert chart['page'].paginator.count==29 and chart['page'].number==2
    assert sum(g['value'] for g in chart['page'].object_list)==4


@pytest.mark.django_db(transaction=True)
def test_block_reads_one_database_snapshot(client, feedback, nguoi_dung, monkeypatch):
    """AC-21.4 — Ghi giữa hai truy vấn đọc không làm khối bị rách/409 vô ích."""
    from concurrent.futures import ThreadPoolExecutor
    from django.db import close_old_connections, connections
    from django.utils import timezone
    from crm.services import master_grid_service as service
    row=feedback[2][0]; original=service.stamp; calls=[]
    def changed():
        close_old_connections()
        try: DataRecord.objects.filter(pk=row.pk).update(data={**row.data,'ghi_chu':'Đổi giữa lượt đọc'}, updated_at=timezone.now())
        finally: connections.close_all()
    def stamp(user, table):
        result=original(user, table)
        if not calls:
            calls.append(True)
            with ThreadPoolExecutor(max_workers=1) as pool: pool.submit(changed).result(timeout=5)
        return result
    monkeypatch.setattr(service,'stamp',stamp)
    client.force_login(nguoi_dung['admin'])
    response=client.get(BASE+'du-lieu/')
    assert response.status_code==200
    cells=next(r for r in response.json()['rows'] if r['id']==row.pk)['cells']
    assert cells['ghi_chu']['value']==row.data.get('ghi_chu')


def test_blank_statuses_and_currencies_stay_separate(client, feedback, nguoi_dung):
    """AC-21.5 — Rỗng một nhóm; không cộng lẫn USD/VND, thiếu chi tiết vẫn đếm."""
    table,_,source=feedback
    a,b=source
    a.data.update(trang_thai_vc=None,loai_tien='USD');a.save()
    b.data.update(trang_thai_vc='',loai_tien='VND');b.save()
    b.waybill_items.all().delete()
    client.force_login(nguoi_dung['admin'])
    response=client.get('/thong-ke/', {'nguon': 'van_don_moi'})
    blank=[g for g in response.context['charts'][0]['groups'] if g['label']=='Chưa có trạng thái']
    assert len(blank)==1 and blank[0]['value']==2
    assert response.context['summary']['orders']==2 and response.context['summary']['missing']==1
    assert {r['record__data__loai_tien'] for r in response.context['summary']['totals']}=={'USD','VND'}


@pytest.mark.django_db(transaction=True)
def test_concurrent_replay_applies_once(feedback, nguoi_dung):
    """AC-21.3 — Hai request cùng UUID chạy thật đồng thời chỉ ghi một lần."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import close_old_connections, connections
    from django.contrib.auth import get_user_model
    from crm.services import master_grid_service as service
    from crm.models import GridMutationReceipt
    row=feedback[2][0]; actor=nguoi_dung['admin'].pk; operation=str(uuid.uuid4()); barrier=Barrier(2)
    payload={'operation':operation,'cells':[{'id':row.pk,'column':'ghi_chu','old':row.data.get('ghi_chu'),'value':'Một lần'}]}
    def worker():
        close_old_connections()
        try:
            user=get_user_model().objects.get(pk=actor);barrier.wait(timeout=5)
            return service.save(user,service.table_for(user,'van_don_moi'),payload)['replayed']
        finally: connections.close_all()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(worker) for _ in range(2)]; results=[f.result(timeout=10) for f in futures]
    assert sorted(results)==[False,True]
    assert GridMutationReceipt.objects.filter(actor_id=actor,operation=operation).count()==1


def test_legacy_writers_cannot_bypass_master_cas(client, feedback, nguoi_dung):
    """AC-21.3 — Tab cũ không được ghi ô/Undo bỏ qua kiểm giá trị cũ."""
    row=feedback[2][0]; before=row.data.copy();client.force_login(nguoi_dung['admin'])
    assert client.post(BASE+f'o/{row.pk}/ghi_chu/',{'gia_tri':'Không qua CAS'}).status_code==409
    assert client.post(BASE+'luu-o/',{'o':[f'{row.pk}:ghi_chu'],'gt':['Không qua CAS']}).status_code==409
    row.refresh_from_db();assert row.data==before
