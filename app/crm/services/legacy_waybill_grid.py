"""Giữ cột Trùng và màu trạng thái của Vận đơn cũ trên bộ lưới chung."""
from . import grid_service
from crm import choices


def grid_columns(columns):
    return [{'code':'__duplicates','name':'Trùng','type':'integer','required':False,
        'computed':True,'options':[],'detail':False,'assignment':False,'protected':True,
        'renderer':'value','width':72,'frozen':True,'filterable':False}]


def grid_extras(rows, columns):
    if not rows:return {}
    grid_service.attach_duplicate_counts(rows[0].table, rows)
    return {row.pk:{'row_class':choices.row_class(row.data.get('trang_thai_vc')),
        'virtual_cells':{'__duplicates':{'value':row.so_trung,'display':row.so_trung if row.so_trung>1 else '',
            'editable':False,'style':{},'class':'tien'}}} for row in rows}
