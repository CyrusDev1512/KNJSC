"""Chuyển bảng placeholder theo yêu cầu rõ ràng; giữ nguyên dòng và đích hiện hành."""
import pytest
from django.core.management import call_command
from core.exceptions import BusinessError, OutOfScopeError
from forms_builder.models import DataRecord
from orders.services import destination_service
from .test_order_destination import destination, create
from .test_waybill_feedback import feedback

pytestmark = pytest.mark.django_db


@pytest.fixture
def populated(destination):
    return DataRecord.objects.create(table=destination, department=destination.department,
                                    data={'ma_don': 'PLACEHOLDER-1', 'ghi_chu': 'giữ nguyên'})


def test_prepare_preserves_rows_and_destination_then_accepts_new_orders(
        client, feedback, destination, populated, nguoi_dung):
    before = list(DataRecord.all_objects.filter(table=destination).values())
    columns = list(destination.columns.order_by('id').values())
    admin = nguoi_dung['admin']
    assert destination_service.eligibility(destination)
    call_command('chuan_bi_bang_nhan_don', table=destination.code,
                 actor=admin.username, expected_rows=1)
    destination.refresh_from_db()
    assert destination.workflow == 'waybill' and destination.is_shared
    assert destination.delivery_view_version == 1
    assert not destination.receives_orders
    assert destination_service.current().pk == feedback[0].pk
    assert list(DataRecord.all_objects.filter(table=destination).values()) == before
    assert list(destination.columns.order_by('id').values()) == columns
    assert destination_service.eligibility(destination) == ''
    # Chạy lại không thay phiên bản hoặc phân công giả cho dữ liệu cũ.
    destination_service.prepare_existing(admin, destination.pk, expected_rows=1)
    destination.refresh_from_db()
    assert destination.delivery_view_version == 1
    assert not DataRecord.objects.in_scope(nguoi_dung['staff_vd'], table=destination).exists()
    client.force_login(admin)
    assert client.post('/cau-hinh/nhan-don/', {'table': destination.pk}).status_code == 302
    order = create(nguoi_dung['staff_sale_1'], feedback[1], '0909888877')
    assert order.record.table_id == destination.pk
    assert order.total == 50
    populated.refresh_from_db()
    assert populated.data == before[0]['data']


def test_prepare_rejects_count_drift_bad_schema_and_non_admin(
        destination, populated, nguoi_dung):
    prepare = destination_service.prepare_existing
    with pytest.raises(OutOfScopeError):
        prepare(nguoi_dung['manager_sale'], destination.pk, expected_rows=1)
    with pytest.raises(BusinessError, match='Số dòng'):
        prepare(nguoi_dung['admin'], destination.pk, expected_rows=2)
    destination.columns.filter(code='ma_don').delete()
    with pytest.raises(BusinessError, match='Cột'):
        prepare(nguoi_dung['admin'], destination.pk, expected_rows=1)
    destination.refresh_from_db()
    assert destination.workflow == '' and not destination.receives_orders


def test_prepare_rolls_back_if_audit_fails(destination, populated, nguoi_dung, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError('test audit rollback')
    monkeypatch.setattr(destination_service, 'record', fail)
    with pytest.raises(RuntimeError, match='test audit'):
        destination_service.prepare_existing(nguoi_dung['admin'], destination.pk, expected_rows=1)
    destination.refresh_from_db()
    assert destination.workflow == '' and not destination.is_shared
    assert DataRecord.objects.filter(pk=populated.pk).exists()
