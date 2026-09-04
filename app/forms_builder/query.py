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
    # Hai phép đặc biệt, không phải tra cứu Django: ô trống và ô có giá trị
    "rong": "blank",
    "co": "nonblank",
}

#: Giá trị của phép "trong" là danh sách; trên đường dẫn là nhiều tham số
#: cùng tên (`f_cot__trong=a&f_cot__trong=b`)
LIST_OPERATORS = {"trong"}

#: Cột tách nhận được phép so sánh số; cột JSON thì so sánh chuỗi là chính,
#: vì giá trị trong JSON không có kiểu ổn định.
NUMERIC_OPERATORS = {"gt", "gte", "lt", "lte"}
#: Kiểu cột JSON mà phép so sánh khoảng vẫn đúng
JSON_RANGE_TYPES = {"integer", "date", "datetime"}


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
        if phep in ("blank", "nonblank"):
            trong = Q(**{f"{duong_dan}__isnull": True}) | Q(**{duong_dan: ""})
            queryset = queryset.filter(trong) if phep == "blank" else queryset.exclude(trong)
            continue
        if phep == "in":
            gia_tri = [v for v in (gia_tri if isinstance(gia_tri, (list, tuple)) else [gia_tri]) if v != ""]
            if not gia_tri:
                continue
        cot = column_map.by_code.get(code)
        if not column_map.is_indexed(code):
            # Giá trị trong JSON giữ kiểu lúc lưu: số nguyên là số thật, nên
            # tham số chuỗi trên URL phải ép về số mới khớp được
            gia_tri = _ep_kieu_json(cot, gia_tri)
            # So sánh khoảng trên JSON chỉ tin được với số nguyên (jsonb so số)
            # và ngày ISO (so chuỗi đúng thứ tự); còn lại rơi về so bằng
            if phep in NUMERIC_OPERATORS and cot.field_type not in JSON_RANGE_TYPES:
                phep = "exact"
        try:
            queryset = queryset.filter(**{f"{duong_dan}__{phep}": gia_tri})
        except (FieldError, ValueError, TypeError):
            continue
    return queryset


def _ep_kieu_json(cot, gia_tri):
    if cot is None or cot.field_type != "integer":
        return gia_tri
    def _mot(v):
        try:
            return int(str(v).strip())
        except (ValueError, TypeError):
            return v
    return [_mot(v) for v in gia_tri] if isinstance(gia_tri, list) else _mot(gia_tri)


def read_filters(params, columns):
    """Đọc bộ lọc từ tham số đường dẫn: `f_<cột>` hoặc `f_<cột>__<phép>`.

    Chỉ nhận cột có thật; phép "trong" gom nhiều tham số cùng tên thành danh
    sách. Dùng chung cho màn hình bảng, xuất tệp và Bảng tính — một chỗ đọc
    duy nhất để xuất ra đúng thứ đang hiện (ADR-002).
    """
    ma_cot = {c.code for c in columns}
    bo_loc = {}
    lay_nhieu = getattr(params, "getlist", None)
    for khoa in params.keys():
        if not khoa.startswith("f_"):
            continue
        ten = khoa[2:]
        code, _, phep = ten.partition("__")
        if code not in ma_cot:
            continue
        if phep in LIST_OPERATORS and lay_nhieu:
            gia_tri = [v.strip() for v in lay_nhieu(khoa) if v.strip()]
            if gia_tri:
                bo_loc[ten] = gia_tri
            continue
        gia_tri = params.get(khoa)
        if isinstance(gia_tri, (list, tuple)):
            gia_tri = gia_tri[0] if gia_tri else ""
        if gia_tri is not None and str(gia_tri).strip():
            bo_loc[ten] = str(gia_tri).strip()
    return bo_loc


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
