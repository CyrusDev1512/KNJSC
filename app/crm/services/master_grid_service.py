"""Lưới master: JSON có giới hạn, so giá trị cũ và biên nhận cùng giao dịch."""
import hashlib
import json
import uuid

from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection, transaction
from django.db.models import Count, Max, F
from django.http import Http404
from django.urls import reverse

from core.constants import GRID_PASTE_CELLS_MAX
from core.exceptions import BusinessError, OutOfScopeError
from forms_builder.models import DataRecord, TableDef
from forms_builder import choice_registry
from forms_builder.services import grant_service, record_service
from orders.constants import ACTIVE_WAYBILL_TABLE_CODE
from orders.services import waybill_service, assignment_service
from crm.models import GridMutationReceipt, GridCellHistory
from . import grid_service

BLOCK_SIZE = 100


class CellConflict(BusinessError):
    def __init__(self, conflicts):
        super().__init__('Có ô vừa được thay đổi. Đối chiếu trước khi gửi lại toàn lượt.', code='conflict')
        self.conflicts = conflicts


def table_for(user, code):
    if code != ACTIVE_WAYBILL_TABLE_CODE:
        raise Http404
    table = TableDef.objects.in_scope(user).filter(code=code).first()
    if table is None:
        raise OutOfScopeError()
    return table


def digest(value):
    return hashlib.sha256(json.dumps(value, cls=DjangoJSONEncoder, sort_keys=True,
        ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def metadata(columns):
    def options(column):
        # Cùng nguồn với record_service: sổ bảng, nhãn ý nghĩa, rồi options của cột.
        source = choice_registry.for_column(column)
        return list(source.options()) if source else []

    return [{'code': c.code, 'name': c.name, 'type': c.field_type, 'required': c.required,
             'computed': c.is_computed, 'options': options(c),
             'detail': c.code in waybill_service.DETAIL_CELLS,
             'assignment': c.code in assignment_service.COLUMNS,
             'protected': c.is_computed or c.code in waybill_service.PROTECTED or c.code in assignment_service.COLUMNS,
             'width': 160, 'frozen': c.code in ('ma_don', 'ten_khach', 'so_dien_thoai')}
            for c in columns]


def serialize(rows, columns, user):
    result = []
    for row in rows:
        editable = grant_service.can_edit_visible_record(user, row)
        cells = {}
        for c in columns:
            value = row.data.get(c.code)
            if c.code in assignment_service.COLUMNS:
                value = assignment_service.display(row, c.code)
            style = (row.style or {}).get(c.code)
            cells[c.code] = {'value': value, 'display': grid_service.display_value(c, value, style),
                'class': grid_service.cell_class(c, None, editable, style=style), 'style': style or {},
                'editable': editable and not c.is_computed and c.code not in waybill_service.PROTECTED
                            and c.code not in assignment_service.COLUMNS}
        result.append({'id': row.pk, 'cells': cells, 'editable': editable,
                       'updated': row.updated_at.isoformat(),
                       'detail_url': reverse('waybill_detail', args=[row.pk])})
    return result


def stamp(user, table):
    # Bao gồm dòng xoá mềm để việc xoá/khôi phục cũng đổi mốc; vẫn trong phạm vi.
    s = DataRecord.all_objects.in_scope(user, table=table).aggregate(n=Count('*'), t=Max('updated_at'))
    return digest(s)


def block(user, table, params):
    # Tổng, phiên bản và các dòng thuộc cùng snapshot. Không buộc trình duyệt
    # tải lại chỉ vì một người vừa sửa ô trong thời gian đọc khối này.
    # Nếu caller đã mở transaction (ví dụ fixture pytest), caller sở hữu mức
    # cô lập; kiểm mốc cuối ở _block vẫn chặn kết quả không nhất quán.
    if not connection.in_atomic_block:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            return _block(user, table, params, snapshot=True)
    return _block(user, table, params)


def _block(user, table, params, *, snapshot=False):
    try:
        offset = int(params.get('offset', 0))
        if offset < 0 or offset > 2**31 - 1:
            raise ValueError
    except (ValueError, TypeError):
        raise BusinessError('Vị trí dữ liệu không hợp lệ.')
    grid = grid_service.build_grid(user, params, table=table)
    for column in grid.columns:
        column.table = table
    meta = metadata(grid.columns)
    filters = sorted((k, params.getlist(k)) for k in params if k not in {'offset', 'version', 'trang', 'moi_trang'})
    version = digest([stamp(user, table), meta, filters])
    if params.get('version') and params['version'] != version:
        raise BusinessError('Dữ liệu đã thay đổi. Đang tải lại vùng đang xem.', code='conflict')
    ordering = list(grid.queryset.query.order_by) or ['pk']
    if 'pk' not in ordering and '-pk' not in ordering:
        ordering.append('pk')
    qs = grid.queryset.order_by(*ordering)
    total = qs.count()
    # OFFSET chỉ đi qua ID/thứ tự, không JOIN và mang JSON cùng thông tin
    # tài khoản cho hàng trăm nghìn dòng sẽ bị bỏ. Tải chi tiết đúng 100 ID.
    ids = list(qs.select_related(None).values_list('pk', flat=True)[offset:offset + BLOCK_SIZE])
    by_id = {r.pk: r for r in qs.filter(pk__in=ids).order_by()}
    rows = [by_id[pk] for pk in ids if pk in by_id]
    if not snapshot and version != digest([stamp(user, table), meta, filters]):
        raise BusinessError('Dữ liệu đang cập nhật. Thử lại vùng đang xem.', code='conflict')
    return {'columns': meta, 'rows': serialize(rows, grid.columns, user), 'total': total,
            'offset': offset, 'version': version, 'block_size': BLOCK_SIZE}


@transaction.atomic
def save(user, table, payload, *, request=None):
    if not isinstance(payload, dict):
        raise BusinessError('Gói dữ liệu không hợp lệ.')
    try:
        operation = uuid.UUID(str(payload.get('operation', '')))
    except ValueError:
        raise BusinessError('Thiếu mã thao tác hợp lệ.')
    cells = payload.get('cells')
    if not isinstance(cells, list) or not 1 <= len(cells) <= GRID_PASTE_CELLS_MAX:
        raise BusinessError(f'Chỉ lưu từ 1 đến {GRID_PASTE_CELLS_MAX} ô một lượt.')
    seen = set()
    for cell in cells:
        if (not isinstance(cell, dict) or type(cell.get('id')) is not int or cell['id'] <= 0
                or not isinstance(cell.get('column'), str) or 'old' not in cell or 'value' not in cell
                or isinstance(cell['value'], (dict, list)) or isinstance(cell['old'], (dict, list))):
            raise BusinessError('Ô thiếu định danh hoặc giá trị hợp lệ.')
        if cell.get('property', 'value') not in ('value', 'fs', 'c', 'bg'):
            raise BusinessError('Thuộc tính định dạng không được hỗ trợ.')
        key = (cell['id'], cell['column'], cell.get('property', 'value'))
        if key in seen:
            raise BusinessError('Một ô xuất hiện nhiều lần trong lượt ghi.')
        seen.add(key)
    kind = payload.get('kind', 'edit')
    if kind not in ('edit','paste','clear','format','undo','redo'):
        raise BusinessError('Loại thao tác không hợp lệ.')
    fingerprint = digest({'table': table.pk, 'cells': cells, **({'kind':kind} if 'kind' in payload else {})})
    # Unique constraint tuần tự hoá cả request trùng ID nhưng khác tập dòng.
    receipt, created = GridMutationReceipt.objects.get_or_create(actor=user, operation=operation,
        defaults={'table': table, 'fingerprint': fingerprint})
    receipt = GridMutationReceipt.objects.select_for_update().get(pk=receipt.pk)
    if receipt.fingerprint != fingerprint:
        raise BusinessError('Mã thao tác đã được dùng với nội dung khác.', code='conflict')
    ids = {c['id'] for c in cells}
    rows = list(DataRecord.objects.filter(table=table, pk__in=ids).select_related('table')
                .select_for_update(of=('self',)).order_by('pk'))
    allowed = set(DataRecord.objects.in_scope(user, table=table).filter(pk__in=ids).values_list('pk', flat=True))
    if ids != allowed or len(rows) != len(ids):
        raise OutOfScopeError()
    if not created:
        return {**receipt.result, 'replayed': True}
    columns = grid_service.display_columns(table)
    for column in columns:
        column.table = table
    column_map = {c.code: c for c in columns}
    by_id = {r.pk: r for r in rows}
    changes, styles, conflicts = [], [], []
    for c in cells:
        row, column = by_id[c['id']], column_map.get(c['column'])
        if not grant_service.can_edit_visible_record(user, row):
            raise OutOfScopeError()
        if column is None or column.is_computed or column.code in waybill_service.PROTECTED or column.code in assignment_service.COLUMNS:
            raise record_service.CellError('Ô này bị khoá; lượt ghi chưa được áp dụng.', pk=row.pk, code=c['column'])
        prop = c.get('property', 'value')
        current = row.data.get(column.code) if prop == 'value' else (row.style or {}).get(column.code, {}).get(prop)
        if current != c['old']:
            conflicts.append({**c, 'current': current, 'name': column.name})
        if prop == 'value':
            changes.append((row, column.code, c['value']))
        else:
            record_service.normalise_style({prop: c['value']})
            styles.append(c)
    if conflicts:
        raise CellConflict(conflicts)
    if changes:
        record_service._update_locked_cells(changes, actor=user, request=request, columns=columns)
    # Ghi style riêng, không ghi lại JSON dữ liệu hoặc thuộc tính style không chạm tới.
    style_rows = {r.pk: r for r in DataRecord.objects.filter(pk__in={c['id'] for c in styles}).select_related('table')}
    for c in styles:
        record_service._ap_dinh_dang(style_rows[c['id']], c['column'], {c['property']: c['value']}, columns)
    if styles:
        record_service.save_rows(style_rows.values(), fields=('style',))
        from core.audit import record
        from core.constants import AuditAction
        record(AuditAction.UPDATE, actor=user, target=rows[0], detail=f'Định dạng {len(styles)} thuộc tính ô lưới master', request=request)
    fresh = list(assignment_service.related(DataRecord.objects.in_scope(user, table=table).filter(pk__in=ids)).select_related('table'))
    final = {r.pk: r for r in fresh}
    history = []
    for c in cells:
        r = final[c['id']]; prop = c.get('property', 'value')
        value = r.data.get(c['column']) if prop == 'value' else (r.style or {}).get(c['column'], {}).get(prop)
        if value != c['old']:
            history.append(GridCellHistory(record=r, receipt=receipt, column=c['column'], property=prop, before=c['old'], after=value))
    GridCellHistory.objects.bulk_create(history, batch_size=500)
    result = {'rows': serialize(fresh, columns, user), 'replayed': False,
              'operation': str(operation), 'changed': len(history), 'kind': kind}
    receipt.result = result
    receipt.save(update_fields=['result'])
    return result


def history(user, table, params):
    try:
        pk = int(params.get('record', ''))
        before = int(params.get('before', 0))
    except (TypeError, ValueError):
        raise BusinessError('Định danh lịch sử không hợp lệ.')
    if not DataRecord.objects.in_scope(user, table=table).filter(pk=pk).exists():
        raise OutOfScopeError()
    qs = GridCellHistory.objects.filter(record_id=pk)
    if params.get('column'):
        qs = qs.filter(column=params['column'])
    if before:
        qs = qs.filter(pk__lt=before)
    # Kết quả một biên nhận có thể chứa hàng nghìn ô. Chỉ lấy loại thao tác,
    # không nhân payload đó lên theo 50 mục lịch sử trên mỗi trang.
    entries = list(qs.annotate(operation_kind=F('receipt__result__kind'))
                   .select_related('receipt__actor__profile').defer('receipt__result')
                   .order_by('-pk')[:51])
    return {'items': [{'id': h.pk, 'column': h.column, 'property': h.property,
                      'before': h.before, 'after': h.after, 'time': h.created_at.isoformat(),
                      'actor': h.receipt.actor.username,
                      'name': getattr(getattr(h.receipt.actor, 'profile', None), 'full_name', ''),
                      'operation': str(h.receipt.operation), 'kind': h.operation_kind or 'edit'} for h in entries[:50]],
            'next': entries[49].pk if len(entries) > 50 else None}
