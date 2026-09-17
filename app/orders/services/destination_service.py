"""Một bảng nhận đơn mới; profile vận hành của bảng cũ luôn được giữ lại."""
from django.db import connection, transaction
from core.audit import record
from core.constants import AuditAction, Rank
from core.exceptions import BusinessError
from core.permissions import assert_rank
from forms_builder.models import TableDef, DataRecord
from forms_builder.services import lifecycle_service
from orders.constants import ACTIVE_WAYBILL_TABLE_CODE, WAYBILL_TABLE_CODE, is_waybill_table
from . import waybill_service

LOCK_NAMESPACE = 0x4B4E4453


def _lock(*, exclusive=False):
    function = 'pg_advisory_xact_lock' if exclusive else 'pg_advisory_xact_lock_shared'
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT {function}(%s, %s)', [LOCK_NAMESPACE, 1])


def current(*, for_write=False):
    if for_write:
        if not connection.in_atomic_block:
            raise RuntimeError('Chọn bảng nhận đơn phải nằm trong giao dịch tạo đơn.')
        _lock()
    # Không rơi về bảng mặc định nếu bảng đã chọn bị ngừng hoạt động.
    table = TableDef.all_objects.filter(receives_orders=True).first()
    if table is None:
        table = TableDef.all_objects.filter(code=ACTIVE_WAYBILL_TABLE_CODE).first()
    if table is None:
        raise BusinessError('Chưa có bảng vận đơn để nhận đơn. Admin kiểm tra cấu hình Bảng nhận đơn.')
    if table.deleted_at is not None or not table.is_active:
        raise BusinessError('Chưa có bảng nhận đơn khả dụng. Admin kiểm tra cấu hình Bảng nhận đơn.')
    if for_write:
        lifecycle_service.lock(table)
    return table


def _schema_error(table):
    if table.deleted_at is not None or not table.is_active:
        return 'Bảng không hoạt động.'
    if table.code == WAYBILL_TABLE_CODE:
        return 'Bảng Vận đơn cũ chỉ giữ dữ liệu lịch sử.'
    if table.department.code != 'van-don' or not table.department.is_active:
        return 'Bảng phải thuộc bộ phận Vận đơn đang hoạt động.'
    columns = {c.code: c for c in table.columns.all()}
    from forms_builder import choice_registry
    for label, code, kind, meaning in waybill_service.COLUMNS:
        column = columns.get(code)
        if column is None or column.field_type != kind or column.is_computed or column.meaning != meaning:
            return f'Cột {label} chưa có hoặc không đúng cấu trúc Vận đơn.'
        options = waybill_service.OPTIONS.get(code)
        source = choice_registry.for_column(column) if options else None
        actual_options = list(source.options()) if source else (column.options or [])
        if options and not set(options).issubset(actual_options):
            return f'Cột {label} thiếu lựa chọn chuẩn.'
    return ''


def eligibility(table):
    reason = _schema_error(table)
    if reason:
        return reason
    if not is_waybill_table(table) and DataRecord.all_objects.filter(table=table).exists():
        return 'Bảng đã có dữ liệu nhưng chưa có profile Vận đơn; cần chuyển đổi riêng trước khi chọn.'
    return ''


def _prepare_workflow(table):
    if not is_waybill_table(table):
        # Chỉ gắn profile; không suy người phụ trách từ nội dung ô cũ.
        table.is_shared = True
        table.delivery_view_version += 1
    table.workflow = 'waybill'


@transaction.atomic
def prepare_existing(actor, table_id, *, expected_rows, request=None):
    """Chuyển bảng đã được duyệt riêng; không tự chọn đích hoặc sửa dữ liệu cũ."""
    assert_rank(actor, Rank.ADMIN, request)
    if type(expected_rows) is not int or expected_rows < 0:
        raise BusinessError('Số dòng xác nhận phải là số nguyên không âm.')
    _lock(exclusive=True)
    table = TableDef.all_objects.select_related('department').get(pk=table_id)
    lifecycle_service.lock(table, exclusive=True)
    table.refresh_from_db()
    reason = _schema_error(table)
    if reason:
        raise BusinessError(reason)
    count = DataRecord.all_objects.filter(table=table).count()
    if count != expected_rows:
        raise BusinessError(f'Số dòng đã thay đổi: xác nhận {expected_rows}, hiện có {count}.')
    if is_waybill_table(table):
        return table
    _prepare_workflow(table)
    table.save(update_fields=['workflow', 'is_shared', 'delivery_view_version', 'updated_at'])
    record(AuditAction.UPDATE, actor=actor, target=table, request=request,
           detail=f'Chuẩn bị bảng nhận đơn: {table.code}; giữ {count} dòng; chưa đổi đích nhận đơn')
    return table


def candidates():
    tables = TableDef.objects.filter(is_active=True, department__code='van-don').exclude(code=WAYBILL_TABLE_CODE).select_related('department').prefetch_related('columns')
    return [(table, eligibility(table)) for table in tables]


@transaction.atomic
def configure(actor, table_id, *, request=None):
    assert_rank(actor, Rank.ADMIN, request)
    _lock(exclusive=True)
    table = TableDef.objects.select_related('department').filter(pk=table_id, is_active=True).first()
    if table is None:
        raise BusinessError('Bảng nhận đơn không hợp lệ.')
    lifecycle_service.lock(table, exclusive=True)
    table.refresh_from_db()
    reason = eligibility(table)
    if reason:
        raise BusinessError(reason)
    previous = TableDef.all_objects.filter(receives_orders=True).first()
    if previous and previous.pk == table.pk:
        return table
    TableDef.all_objects.filter(receives_orders=True).update(receives_orders=False)
    _prepare_workflow(table)
    table.receives_orders = True
    table.save(update_fields=['workflow', 'receives_orders', 'delivery_view_version', 'is_shared', 'updated_at'])
    record(AuditAction.UPDATE, actor=actor, target=table, request=request,
           detail=f'Bảng nhận đơn: {previous.pk if previous else ACTIVE_WAYBILL_TABLE_CODE} → {table.pk}; chỉ áp dụng đơn mới')
    return table
