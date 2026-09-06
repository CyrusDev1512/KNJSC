"""Lớp CSS của cột và ô trên Bảng dữ liệu — FR-8.8, FR-8.9, Q60.

Tính ở đây, template chỉ in ra `{{ lop }}`. Hai lý do:

- Bài quét lớp CSS (`core/tests/test_giao_dien.py`) không đọc được điều kiện
  Django nằm trong thuộc tính `class`; chuỗi lớp sinh từ Python thì bài
  `test_mau_cot.py` khẳng định từng tên có thật trong `main.css`.
- Sổ đóng: màu cột và ngưỡng là giá trị trong danh sách cố định, không có CSS
  nào sinh từ dữ liệu người dùng.
"""
from decimal import Decimal, InvalidOperation

from . import query
from .models import AlertOp, Highlight

#: Mỗi giá trị của `ColumnDef.highlight` là một lớp cố định trong main.css
HIGHLIGHT_CLASSES = {
    Highlight.VANG: "cot-nen-vang",
    Highlight.DO: "cot-nen-do",
    Highlight.LUC: "cot-nen-luc",
    Highlight.XANH: "cot-nen-xanh",
}
#: Ô vượt ngưỡng cảnh báo (đỏ) và ô đạt (xanh lá)
ALERT_HIT = "o-vuot-nguong"
ALERT_OK = "o-dat-nguong"


def _so(gia_tri):
    if gia_tri is None or gia_tri == "":
        return None
    try:
        return Decimal(str(gia_tri))
    except (InvalidOperation, ValueError, TypeError):
        return None


def column_class(column):
    """Lớp màu của cả cột — áp cho tiêu đề lẫn mọi ô."""
    return HIGHLIGHT_CLASSES.get(column.highlight or "", "")


def alert_class(column, value):
    """Lớp cảnh báo của một ô theo ngưỡng của cột; ô trống hay không phải số thì không tô."""
    if not column.alert_op or column.alert_value is None:
        return ""
    so = _so(value)
    if so is None:
        return ""
    if column.alert_op == AlertOp.GT:
        vuot = so > column.alert_value
    else:
        vuot = so < column.alert_value
    return ALERT_HIT if vuot else ALERT_OK


def decorate_columns(columns):
    """Gắn `lop_cot` lên từng cột để template in vào `<th>` và ô."""
    for cot in columns:
        cot.lop_cot = column_class(cot)
    return columns


def cell_class(column, value):
    """Chuỗi lớp của một `<td>`: cột tính sẵn, màu cột, cảnh báo.

    Không có lớp "ô sửa được": Bảng dữ liệu chỉ để xem với mọi bảng (ADR-014).
    """
    phan = []
    if column.is_computed:
        phan += ["tien", "o-tinh"]
    phan += [column_class(column), alert_class(column, value)]
    return " ".join(p for p in phan if p)


def row_cells(record, columns):
    """`[(cột, giá trị, lớp)]` cho một dòng — thay cho `query.read_row` khi vẽ bảng."""
    return [
        (cot, gia_tri, cell_class(cot, gia_tri))
        for cot, gia_tri in query.read_row(record, columns)
    ]
