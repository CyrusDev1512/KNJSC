"""Hook lưới của bảng vận đơn duy nhất (ADR-036): cột ảo Trùng và màu trạng thái của lưới
cũ gộp với detail/assignment/protected/bill của `waybill_service`. `grid_for` ưu tiên grid
policy theo mã bảng, nên mọi hook ở đây phải gọi tiếp `waybill_service`."""
from crm import choices
from orders.services import waybill_service

from . import grid_service


def grid_columns(columns):
    return [{'code':'__duplicates','name':'Trùng','type':'integer','required':False,
        'computed':True,'options':[],'detail':False,'assignment':False,'protected':True,
        'renderer':'value','width':72,'frozen':True,'filterable':False}]


def grid_column(column):
    return waybill_service.grid_column(column)


def grid_value(row, column):
    return waybill_service.grid_value(row, column)


def grid_extras(rows, columns):
    if not rows:
        return {}
    extras = waybill_service.grid_extras(rows, columns)
    grid_service.attach_duplicate_counts(rows[0].table, rows)
    for row in rows:
        item = extras.setdefault(row.pk, {})
        item['row_class'] = choices.row_class(row.data.get('trang_thai_vc'))
        item.setdefault('virtual_cells', {})['__duplicates'] = {
            'value': row.so_trung, 'display': row.so_trung if row.so_trung > 1 else '',
            'editable': False, 'style': {}, 'class': 'tien'}
    return extras
