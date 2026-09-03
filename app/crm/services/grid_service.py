"""Lưới làm việc của bộ phận Vận đơn trên bảng vận đơn — ADR-009.

Không có model riêng. Lưới là một cách nhìn khác lên `DataRecord` của bảng
`van_don`: đọc qua `in_scope` (quy tắc 11), lọc và sắp xếp bằng đúng bộ dựng
truy vấn của màn hình bảng (`forms_builder.query`), cộng thêm ba thứ tệp thật
có mà màn hình bảng không có:

- **Lọc trùng** — cột ảo đếm số dòng cùng số điện thoại, tô màu khi > 1.
- **Lọc theo từng cột** — danh sách giá trị kèm số đếm, khoảng số/ngày,
  ô trống, cộng dồn nhiều cột; trạng thái lọc nằm trên URL (`f_<cột>`).
- **Thứ tự cột theo tệp** — thông tin khách, số lượng từng sản phẩm, tiền,
  trạng thái — không theo thứ tự tạo cột.

Trạng thái lưới (bộ lọc, sắp xếp) sống trên URL để chia sẻ được bằng cách
chép đường dẫn; độ rộng cột và cột ẩn do trình duyệt nhớ (localStorage).
"""
from dataclasses import dataclass, field

from django.db.models import Case, Count, F, IntegerField, OuterRef, Subquery, Value, When
from django.db.models.fields.json import KeyTextTransform

from core.constants import GRID_FILTER_OPTIONS_MAX, GRID_FROZEN_COLUMNS
from forms_builder import choice_registry, query
from forms_builder.meaning import FieldType
from forms_builder.models import DataRecord
from forms_builder.services import grant_service
from orders.services import dispatch_service

from .. import choices

#: Nhãn hiển thị của các phép lọc trên chip "đang lọc"
OPERATOR_LABELS = {
    "bang": "=", "chua": "chứa", "bat_dau": "bắt đầu", "lon_hon": ">", "lon_bang": "≥",
    "nho_hon": "<", "nho_bang": "≤", "trong": "thuộc", "rong": "trống", "co": "có giá trị",
}

#: Kiểu cột → cách lọc trên giao diện
FILTER_KIND = {
    FieldType.TEXT: "danh_sach", FieldType.CHOICE: "danh_sach", FieldType.BOOLEAN: "danh_sach",
    FieldType.LONG_TEXT: "chua",
    FieldType.INTEGER: "khoang", FieldType.DECIMAL: "khoang", FieldType.MONEY: "khoang",
    FieldType.DATE: "khoang", FieldType.DATETIME: "khoang",
}


@dataclass
class Grid:
    table: object
    columns: list
    queryset: object
    filters: dict
    search: str = ""
    sort: str = ""
    descending: bool = False
    duplicates_only: bool = False
    chips: list = field(default_factory=list)


def waybill_table():
    return dispatch_service.waybill_table()


def display_columns(table, columns=None):
    """Cột theo thứ tự của tệp thật; cột sản phẩm chèn vào chỗ đánh dấu;
    cột lạ xếp cuối theo thứ tự tạo."""
    columns = list(columns if columns is not None else table.columns.order_by("order", "id"))
    thu_tu = {ma: i for i, ma in enumerate(dispatch_service.GRID_ORDER)}
    cho_san_pham = thu_tu["__san_pham__"]
    cuoi = len(thu_tu) + 1

    def khoa(c):
        if dispatch_service.is_product_column(c.code):
            return (cho_san_pham, 0, c.name)
        if c.code in thu_tu:
            return (thu_tu[c.code], 0, "")
        return (cuoi, c.order, c.code)

    return sorted(columns, key=khoa)


def frozen_columns(columns):
    """Các cột cố định bên trái khi cuộn ngang, kèm vị trí `left` (px)."""
    ket_qua = []
    trai = 0
    for cot, rong in zip(columns[:GRID_FROZEN_COLUMNS], choices.FROZEN_WIDTHS):
        ket_qua.append((cot.code, trai, rong))
        trai += rong
    return ket_qua


def duplicate_count(table):
    """Biểu thức đếm số dòng cùng số điện thoại trong bảng — cột "Lọc trùng".
    Số trống thì không tính là trùng với nhau."""
    cung_so = (
        DataRecord.objects.filter(table=table, val_phone=OuterRef("val_phone"))
        .order_by().values("val_phone").annotate(n=Count("id")).values("n")
    )
    return Case(
        When(val_phone="", then=Value(0)),
        default=Subquery(cung_so, output_field=IntegerField()),
        output_field=IntegerField(),
    )


def build_grid(user, params, *, table=None):
    """Queryset của lưới đúng như URL mô tả — chưa cắt trang."""
    table = table or waybill_table()
    columns = display_columns(table)
    bo_loc = query.read_filters(params, columns)
    tim = (params.get("tim") or "").strip()
    sap = params.get("sap") or ""
    giam = params.get("chieu") == "giam"
    ds, _ = query.build(
        DataRecord.objects.in_scope(user), table,
        filters=bo_loc, search=tim, sort=sap, descending=giam, columns=columns,
    )
    ds = ds.annotate(so_trung=duplicate_count(table))
    chi_trung = params.get("trung") == "1"
    if chi_trung:
        ds = ds.filter(so_trung__gt=1)
    ds = ds.select_related("table", "created_by")
    return Grid(
        table=table, columns=columns, queryset=ds, filters=bo_loc, search=tim,
        sort=sap, descending=giam, duplicates_only=chi_trung,
        chips=filter_chips(bo_loc, columns),
    )


def filter_chips(bo_loc, columns):
    """Mỗi bộ lọc đang bật thành một chip `(khoá tham số, nhãn)`."""
    ten = {c.code: c.name for c in columns}
    chips = []
    for khoa, gia_tri in bo_loc.items():
        code, _, phep = khoa.partition("__")
        nhan_phep = OPERATOR_LABELS.get(phep or "bang", phep)
        if phep in ("rong", "co"):
            mo_ta = nhan_phep
        elif isinstance(gia_tri, list):
            mo_ta = f"{nhan_phep} {', '.join(gia_tri[:3])}" + (" …" if len(gia_tri) > 3 else "")
        else:
            mo_ta = f"{nhan_phep} {gia_tri}"
        chips.append((f"f_{khoa}", f"{ten.get(code, code)} {mo_ta}"))
    return chips


NUMERIC_TYPES = {FieldType.MONEY, FieldType.INTEGER, FieldType.DECIMAL}


def cell_class(column, frozen=None, editable=True, editing=False, error=False):
    """Lớp CSS của một ô — tính ở đây để template chỉ in ra, vì bài quét lớp
    CSS (`test_giao_dien`) không đọc được điều kiện Django trong thuộc tính."""
    lop = ["o-sua" if editable and not column.is_computed else "o-xem"]
    if editing:
        lop.append("dang-sua")
    if error:
        lop.append("o-loi")
    if frozen:
        lop.append("co-dinh")
    if column.field_type == FieldType.LONG_TEXT:
        lop.append("o-ghi-chu")
    if column.field_type in NUMERIC_TYPES:
        lop.append("tien")
    if column.is_computed:
        lop.append("o-tinh")
    return " ".join(lop)


def frozen_style(frozen):
    """Thuộc tính style của cột cố định: `left` cộng bề rộng cột Lọc trùng."""
    if not frozen:
        return ""
    trai, rong = frozen
    return f"left:{trai + DUPLICATE_COLUMN_WIDTH}px;min-width:{rong}px;max-width:{rong}px"


#: Bề rộng cột "Trùng" đứng trước mọi cột cố định
DUPLICATE_COLUMN_WIDTH = 72


def header_columns(columns, filters=None):
    """Tiêu đề cột cho template: cột, style cố định, lớp, có đang lọc không."""
    co_dinh = {ma: (trai, rong) for ma, trai, rong in frozen_columns(columns)}
    dang_loc = {k.partition("__")[0] for k in (filters or {})}
    ket_qua = []
    for c in columns:
        cd = co_dinh.get(c.code)
        lop = ["sap-xep"]
        if cd:
            lop.append("co-dinh")
        if c.field_type in NUMERIC_TYPES:
            lop.append("phai")
        ket_qua.append({
            "cot": c, "style": frozen_style(cd), "lop": " ".join(lop),
            "lop_nut_loc": "nut-loc dang-loc" if c.code in dang_loc else "nut-loc",
        })
    return ket_qua


def rows(records, columns, user):
    """Dòng cho template: ô theo thứ tự cột, lớp màu, số trùng, sửa được không."""
    co_dinh = {ma: (trai, rong) for ma, trai, rong in frozen_columns(columns)}
    ket_qua = []
    for r in records:
        sua = grant_service.can_edit_record(user, r)
        so_trung = getattr(r, "so_trung", 0) or 0
        ket_qua.append({
            "ban_ghi": r,
            "cac_o": [
                {"cot": c, "gia_tri": r.data.get(c.code),
                 "lop": cell_class(c, co_dinh.get(c.code), sua),
                 "style": frozen_style(co_dinh.get(c.code))}
                for c in columns
            ],
            "sua": sua,
            "lop": choices.row_class(r.data.get("trang_thai_vc")),
            "so_trung": so_trung,
            "lop_trung": "co-dinh tien o-trung" if so_trung > 1 else "co-dinh tien",
        })
    return ket_qua


def filter_kind(column):
    return FILTER_KIND.get(column.field_type, "chua")


def filter_options(user, table, column, search="", limit=GRID_FILTER_OPTIONS_MAX):
    """Giá trị khác nhau của một cột trong phạm vi người xem, kèm số dòng —
    như hộp lọc của Excel. Tối đa `limit` giá trị, nhiều nhất trước."""
    cmap = query.ColumnMap(table, [column])
    ds = DataRecord.objects.in_scope(user).filter(table=table)
    if cmap.is_indexed(column.code):
        ds = ds.annotate(gt=F(cmap.path(column.code)))
    else:
        ds = ds.annotate(gt=KeyTextTransform(column.code, "data"))
    if search:
        ds = ds.filter(gt__icontains=search)
    hang = (
        ds.order_by().values("gt").annotate(n=Count("id")).order_by("-n", "gt")[:limit]
    )
    return [("" if h["gt"] is None else str(h["gt"]), h["n"]) for h in hang]


def choice_list(table, column):
    """`(danh sách, chặt)` của cột chọn, hoặc `(None, False)` nếu cột không có sổ."""
    so = choice_registry.get(table.code, column.code)
    if so is None:
        return None, False
    return list(so.options()), so.strict
