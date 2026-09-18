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
    if _schema_error(table):
        _upgrade_schema(actor, table, request=request)
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


def _upgrade_schema(actor, table, *, request=None):
    """Bổ sung cấu trúc chuẩn Vận đơn cho bảng cũ (ADR-034, 18.09): tạo cột còn thiếu theo
    `waybill_service.COLUMNS` (xếp cuối), đổi cột chữ tự do thành danh sách chọn khi chuẩn
    yêu cầu, thêm lựa chọn chuẩn còn thiếu. Không xoá, không đổi tên cột, không sửa dữ liệu:
    giá trị cũ ngoài danh sách vẫn hiện "(giá trị cũ)" trên lưới. Trả về danh sách việc đã làm."""
    from forms_builder.meaning import FieldType
    from forms_builder.services import table_service
    if table.department.code != 'van-don':
        return []
    columns = {c.code: c for c in table.columns.all()}
    taken_meanings = {c.meaning for c in columns.values() if c.meaning}
    order = max((c.order for c in columns.values()), default=-1)
    done = []
    for label, code, kind, meaning in waybill_service.COLUMNS:
        options = list(waybill_service.OPTIONS.get(code) or [])
        column = columns.get(code)
        if column is None:
            order += 1
            table_service.add_column(table, actor=actor, request=request, name=label, code=code, field_type=kind,
                                     order=order, meaning=meaning if meaning not in taken_meanings else '',
                                     options=options)
            if meaning:
                taken_meanings.add(meaning)
            done.append(f'thêm cột {code}')
            continue
        if column.is_computed:
            continue                      # cột tính sẵn: để `_schema_error` báo, không tự phá công thức
        fields = []
        if column.field_type != kind and kind == FieldType.CHOICE and column.field_type == FieldType.TEXT:
            column.field_type = FieldType.CHOICE
            fields.append('field_type')
        if column.meaning != meaning and meaning and meaning not in taken_meanings:
            column.meaning = meaning
            taken_meanings.add(meaning)
            fields.append('meaning')
        if options and not set(options).issubset(column.options or []):
            column.options = list(column.options or []) + [o for o in options if o not in (column.options or [])]
            fields.append('options')
        if fields:
            column.save(update_fields=fields + ['updated_at'] if hasattr(column, 'updated_at') else fields)
            done.append(f'sửa cột {code}: {", ".join(fields)}')
    if done:
        record(AuditAction.UPDATE, actor=actor, target=table, request=request,
               detail='Bổ sung cấu trúc chuẩn Vận đơn: ' + '; '.join(done))
    return done


def candidates():
    """Mọi bảng vận đơn đang có: bảng đã mang profile Vận đơn (kể cả `van_don` cũ — ADR-034)
    và bảng thuộc bộ phận Vận đơn đủ cấu trúc để nhận đơn. Bảng khác cùng bộ phận (báo cáo
    ngày…) không hiện vì không phải bảng vận đơn."""
    tables = TableDef.objects.filter(is_active=True).select_related('department').prefetch_related('columns').order_by('id')
    return [(table, eligibility(table)) for table in tables if _is_waybill_like(table)]


def _is_waybill_like(table):
    """Bảng vận đơn theo nghĩa nghiệp vụ: có profile Vận đơn, là bảng `van_don` cũ, hoặc
    bảng của bộ phận Vận đơn có cột Mã đơn đúng cấu trúc (bảng chưa chuyển đổi xong vẫn hiện,
    kèm lý do chưa chọn được)."""
    if is_waybill_table(table) or table.code == WAYBILL_TABLE_CODE:
        return True
    if table.department.code != 'van-don':
        return False
    spec = next((c for c in waybill_service.COLUMNS if c[1] == 'ma_don'), None)
    column = next((c for c in table.columns.all() if c.code == 'ma_don'), None)
    return bool(spec and column and column.field_type == spec[2] and column.meaning == spec[3])


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
