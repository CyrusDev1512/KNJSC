"""CRM-UPDATE — cùng lõi JSON, không nhận nhầm cột nghiệp vụ.

Từ ADR-040 (24.09.2026) KN CRM không phục vụ bảng thường qua HTTP nữa, nên lõi
dùng chung kiểm thẳng ở `master_grid_service` (engine không nhận nhầm cột trùng
tên nghiệp vụ), còn HTTP kiểm đúng chiều bị từ chối: 403/404 như ngoài phạm vi.
"""
import uuid
import pytest
from django.http import QueryDict

from crm.services import master_grid_service as grid
from core.exceptions import BusinessError
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


def _goi(row, code, old, value):
    return {'operation': str(uuid.uuid4()),
            'cells': [{'id': row.pk, 'column': code, 'old': old, 'value': value}]}


def test_generic_engine_khong_nhan_nham_cot_nghiep_vu(generic, nguoi_dung):
    """AC-40.4 — Lõi lưới trên bảng thường không nhận nhầm cột trùng tên nghiệp vụ:
    bill/phu_trach_vd/san_pham/ma_don là cột chữ thường (không protected, không
    assignment, không detail) và ghi được như mọi cột khác"""
    table, row = generic
    user = nguoi_dung['staff_mkt']
    metadata = grid.metadata(list(table.columns.order_by('order', 'id')))
    assert all(not c['protected'] and not c['assignment'] and not c['detail'] for c in metadata)
    grid.save(user, table, _goi(row, 'phu_trach_vd', None, 'Cột thường'))
    row.refresh_from_db()
    assert row.data['phu_trach_vd'] == 'Cột thường'


def test_http_tu_choi_bang_thuong_o_kn_crm(client, generic, nguoi_dung):
    """AC-40.2 — KN CRM chỉ phục vụ bảng vận đơn: trang lưới, JSON đọc và ghi của
    bảng thường đều bị từ chối (404/403), kể cả với người cùng bộ phận"""
    table, row = generic
    client.force_login(nguoi_dung['staff_mkt'])
    assert client.get(f'/bang-tinh/{table.code}/').status_code == 404
    assert client.get(f'/bang-tinh/{table.code}/du-lieu/').status_code == 403
    kq = client.post(f'/bang-tinh/{table.code}/luu-json/', _goi(row, 'bill', 'Bình thường', 'Không'),
                     content_type='application/json')
    assert kq.status_code == 403
    row.refresh_from_db()
    assert row.data['bill'] == 'Bình thường'


def test_metadata_distinguishes_suggestions_from_strict_choices(generic, nguoi_dung):
    from forms_builder.meaning import Meaning
    table, row = generic
    ColumnDef.objects.create(table=table, code='seller', name='Người bán', field_type=FieldType.CHOICE, meaning=Meaning.SELLER)
    ColumnDef.objects.create(table=table, code='strict', name='Danh sách chặt', field_type=FieldType.CHOICE, options=['A', 'B'])
    columns = {c['code']: c for c in grid.metadata(list(table.columns.order_by('order', 'id')))}
    assert columns['seller']['choice_strict'] is False and columns['seller']['options']
    assert columns['strict']['choice_strict'] is True


def test_paste_create_update_atomic_retry_and_undo(generic, nguoi_dung):
    table, row = generic
    user = nguoi_dung['staff_mkt']
    operation = str(uuid.uuid4())
    payload = {'operation': operation, 'kind': 'paste', 'cells': [
        {'id': row.pk, 'column': 'bill', 'old': 'Bình thường', 'value': 'Đã sửa'},
        {'id': -1, 'column': 'bill', 'old': None, 'value': 'Dòng mới'}]}
    data = grid.save(user, table, payload)
    new_id = data['id_map']['-1']
    again = grid.save(user, table, payload)
    assert again['id_map'] == data['id_map'] and again.get('replayed')
    assert DataRecord.objects.filter(table=table).count() == 2
    new = DataRecord.objects.get(pk=new_id)
    undo = {'operation': str(uuid.uuid4()), 'kind': 'undo', 'cells': [
        {'id': row.pk, 'column': 'bill', 'old': 'Đã sửa', 'value': 'Bình thường'}],
        'row_changes': [{'id': new_id, 'action': 'delete', 'source': operation, 'version': new.updated_at.isoformat()}]}
    grid.save(user, table, undo)
    new = DataRecord.all_objects.get(pk=new_id)
    assert new.deleted_at and DataRecord.objects.filter(table=table).count() == 1
    redo = {'operation': str(uuid.uuid4()), 'kind': 'redo', 'cells': [],
            'row_changes': [{'id': new_id, 'action': 'restore', 'source': operation, 'version': new.updated_at.isoformat()}]}
    grid.save(user, table, redo)
    assert DataRecord.objects.filter(table=table).count() == 2


def test_invalid_paste_does_not_leave_created_rows(generic, nguoi_dung):
    table, row = generic
    ColumnDef.objects.create(table=table, code='required', name='Bắt buộc', field_type=FieldType.TEXT, required=True)
    with pytest.raises(BusinessError):
        grid.save(nguoi_dung['staff_mkt'], table, {'operation': str(uuid.uuid4()), 'cells': [
            {'id': -1, 'column': 'bill', 'old': None, 'value': 'Chưa đủ'},
            {'id': row.pk, 'column': 'bill', 'old': 'Bình thường', 'value': 'Không được đổi'}]})
    row.refresh_from_db()
    assert row.data['bill'] == 'Bình thường' and DataRecord.objects.filter(table=table).count() == 1
