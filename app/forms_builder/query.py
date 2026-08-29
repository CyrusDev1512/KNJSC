"""Dựng truy vấn động trên bảng do người dùng tạo.

Bảng động không có cột vật lý cho từng trường, nên mọi phép lọc và sắp xếp
phải dịch từ **tên kỹ thuật của cột** sang đường dẫn truy vấn thật:

    cột có nhãn ý nghĩa  →  cột tách có chỉ mục   (val_revenue, val_date...)
    cột không có nhãn    →  khoá trong JSON        (data__cpo)

Đây là chỗ duy nhất biết cách dịch. Không view nào tự ghép chuỗi truy vấn —
ghép sai thì hoặc nổ, hoặc tệ hơn là trả nhầm dữ liệu.

**Phạm vi quyền không do tệp này lo.** Gọi `.in_scope(user)` trước, rồi mới
đưa queryset vào đây (quy tắc 11).
"""
from django.core.exceptions import FieldError
from django.db.models import Q

from .meaning import COLUMN_OF

#: Phép so sánh cho phép, ánh xạ sang tra cứu của Django.
#: Danh sách đóng — không nhận tra cứu tuỳ ý từ tham số trên URL.
OPERATORS = {
    "bang": "exact",
    "chua": "icontains",
    "bat_dau": "istartswith",
    "lon_hon": "gt",
    "lon_bang": "gte",
    "nho_hon": "lt",
    "nho_bang": "lte",
    "trong": "in",
}

#: Cột tách nhận được phép so sánh số; cột JSON thì so sánh chuỗi là chính,
#: vì giá trị trong JSON không có kiểu ổn định.
NUMERIC_OPERATORS = {"gt", "gte", "lt", "lte"}


class ColumnMap:
    """Bảng tra: tên kỹ thuật của cột → đường dẫn truy vấn.

    Dựng một lần cho mỗi bảng rồi dùng lại, tránh truy vấn lại định nghĩa cột
    cho từng lần lọc.
    """

    def __init__(self, table, columns=None):
        self.table = table
        self.columns = list(columns if columns is not None else table.columns.all())
        self.by_code = {c.code: c for c in self.columns}

    def path(self, code):
        """Đường dẫn truy vấn của một cột. Cột lạ thì trả None."""
        cot = self.by_code.get(code)
        if cot is None:
            return None
        cot_tach = COLUMN_OF.get(cot.meaning) if cot.meaning else None
        return cot_tach or f"data__{code}"

    def is_indexed(self, code):
        """Cột này có nằm ở cột tách có chỉ mục không."""
        cot = self.by_code.get(code)
        return bool(cot and cot.meaning and COLUMN_OF.get(cot.meaning))

    def searchable_paths(self):
        """Các cột dùng để tìm kiếm chung.

        Chỉ lấy cột tách — tìm trên khoá JSON không dùng được chỉ mục, và với
        50.000 bản ghi thì sẽ quét toàn bảng (NFR-1).
        """
        return [
            COLUMN_OF[c.meaning] for c in self.columns
            if c.meaning and COLUMN_OF.get(c.meaning)
            and COLUMN_OF[c.meaning] not in ("val_date", "val_revenue")
        ]


def apply_filters(queryset, column_map, filters):
    """Lọc theo nhiều cột.

    `filters` là dict `{tên_cột: giá_trị}` hoặc `{tên_cột__phép_so_sánh: giá_trị}`.
    Cột lạ và phép so sánh lạ đều bị bỏ qua, không ném lỗi — tham số trên URL
    do người dùng gõ, không tin được.
    """
    for khoa, gia_tri in (filters or {}).items():
        if gia_tri in (None, ""):
            continue
        code, _, ten_phep = khoa.partition("__")
        phep = OPERATORS.get(ten_phep or "bang")
        duong_dan = column_map.path(code)
        if not duong_dan or not phep:
            continue
        # So sánh số chỉ có nghĩa trên cột tách; trên JSON thì so chuỗi
        if phep in NUMERIC_OPERATORS and not column_map.is_indexed(code):
            phep = "exact"
        try:
            queryset = queryset.filter(**{f"{duong_dan}__{phep}": gia_tri})
        except (FieldError, ValueError, TypeError):
            continue
    return queryset


def apply_search(queryset, column_map, term):
    """Tìm kiếm chung trên các cột tách."""
    term = (term or "").strip()
    if not term:
        return queryset
    duong_dan = column_map.searchable_paths()
    if not duong_dan:
        return queryset
    dieu_kien = Q()
    for p in duong_dan:
        dieu_kien |= Q(**{f"{p}__icontains": term})
    return queryset.filter(dieu_kien)


def apply_sort(queryset, column_map, sort_code, descending=False):
    """Sắp xếp theo một cột.

    Cột lạ thì rơi về thứ tự mặc định, không ném lỗi.
    """
    duong_dan = column_map.path(sort_code) if sort_code else None
    if not duong_dan:
        return queryset.order_by("-created_at")
    return queryset.order_by(f"{'-' if descending else ''}{duong_dan}")


def build(queryset, table, *, filters=None, search="", sort=None, descending=False,
          columns=None):
    """Dựng trọn truy vấn cho một màn hình bảng dữ liệu.

    Nhận queryset **đã áp phạm vi quyền**, trả về queryset đã lọc và sắp xếp.
    Việc cắt trang do `core.pagination` lo (quy tắc 1).
    """
    column_map = ColumnMap(table, columns)
    queryset = queryset.filter(table=table)
    queryset = apply_filters(queryset, column_map, filters)
    queryset = apply_search(queryset, column_map, search)
    queryset = apply_sort(queryset, column_map, sort, descending)
    return queryset, column_map


def read_row(record, columns):
    """Đọc một bản ghi ra dạng `[(cột, giá trị), ...]` theo đúng thứ tự hiển thị.

    Dùng ở tầng giao diện để khỏi phải biết giá trị nằm ở JSON hay cột tách.
    """
    return [(cot, record.data.get(cot.code)) for cot in columns]
