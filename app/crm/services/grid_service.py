"""Lưới làm việc kiểu Excel trên bảng động — ADR-009, mở rộng cho mọi bảng ở ADR-010.

Không có model riêng. Lưới là một cách nhìn khác lên `DataRecord` của một
bảng: đọc qua `in_scope` (quy tắc 11), lọc và sắp xếp bằng đúng bộ dựng truy
vấn của màn hình bảng (`forms_builder.query`), cộng thêm những thứ Excel có mà
màn hình bảng không có:

- **Lọc theo từng cột** — danh sách giá trị kèm số đếm, khoảng số/ngày, ô
  trống, cộng dồn nhiều cột; trạng thái lọc nằm trên URL (`f_<cột>`).
- **Dòng trống cuối lưới** để gõ bản ghi mới, **cột khoá** bấm là lọc.
- **Định dạng ô** đọc từ `DataRecord.style` (Giai đoạn B).

Riêng **bảng vận đơn** giữ ba thứ theo tệp thật (ADR-009), bật theo
`is_waybill`: cột Lọc trùng đếm số điện thoại, thứ tự cột theo tệp, tô màu
dòng theo trạng thái, và lọc "có sản phẩm" trên các cột `sl_<mã>`.

Trạng thái lưới (bộ lọc, sắp xếp) sống trên URL để chia sẻ được bằng cách
chép đường dẫn; độ rộng cột và cột ẩn do trình duyệt nhớ (localStorage).
"""
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from html import escape          # bản chuẩn: không qua lớp lazy của Django, 20.000 lần/trang (K27)
from urllib.parse import quote

from django.db.models import Case, Count, F, IntegerField, OuterRef, Q, Subquery, Value, When
from django.db.models.fields.json import KeyTextTransform
from django.http import QueryDict
from django.urls import reverse
from django.utils.safestring import mark_safe

from core.constants import (
    GRID_FILLER_COLUMNS, GRID_FILTER_OPTIONS_MAX, GRID_FROZEN_COLUMNS, GRID_FROZEN_COLUMNS_GENERIC,
    GRID_FROZEN_WIDTH_DEFAULT, GRID_MIN_COLUMNS, GRID_ROW_NUMBER_WIDTH, GRID_SPARE_ROWS,
)
from forms_builder import choice_registry, query
from forms_builder.meaning import FieldType
from forms_builder.models import DataRecord
from forms_builder.services import grant_service, record_service
from orders.constants import WAYBILL_TABLE_CODE, ACTIVE_WAYBILL_TABLE_CODE
from orders.services import dispatch_service
from orders.services import waybill_service

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

#: Tham số không phải bộ lọc — không chép vào biểu mẫu lọc, không thành chip
SYSTEM_PARAMS = {"trang", "moi_trang"}

#: Tham số lọc "có sản phẩm" của bảng vận đơn — nhiều giá trị cùng tên
PRODUCT_PARAM = "sp"

NUMERIC_TYPES = {FieldType.MONEY, FieldType.INTEGER, FieldType.DECIMAL}

#: Bề rộng cột "Trùng" đứng trước mọi cột cố định của bảng vận đơn
DUPLICATE_COLUMN_WIDTH = 72


def left_offset(waybill):
    """Cột cố định phải chừa chỗ cho cột số dòng (ADR-011) và, ở bảng vận đơn,
    cột Lọc trùng đứng trước nó."""
    return GRID_ROW_NUMBER_WIDTH + (DUPLICATE_COLUMN_WIDTH if waybill else 0)


def duplicate_style():
    """Thuộc tính style của cột Lọc trùng: dính ngay sau cột số dòng."""
    return (f"left:{GRID_ROW_NUMBER_WIDTH}px;width:{DUPLICATE_COLUMN_WIDTH}px;"
            f"min-width:{DUPLICATE_COLUMN_WIDTH}px;max-width:{DUPLICATE_COLUMN_WIDTH}px")


def filler_letters(n_real, *, offset=0):
    """Chữ của các cột trống bên phải để lưới luôn trông như một sheet đủ chữ
    tới Z (ADR-011): nối tiếp sau `n_real` cột thật (đứng sau `offset` cột
    không có mã như cột Lọc trùng), ít nhất `GRID_FILLER_COLUMNS` cột."""
    dau = n_real + offset
    cuoi = max(GRID_MIN_COLUMNS, dau + GRID_FILLER_COLUMNS)
    return [column_letter(i) for i in range(dau, cuoi)]


def display_value(column, value, style=None):
    """Chữ hiện trong ô: giá trị thô, hoặc số đã định dạng theo `fmt` của ô
    (ADR-011). Tính bằng `Decimal` (BR-8); giá trị không phải số thì giữ nguyên."""
    fmt = (style or {}).get("fmt")
    if not fmt or value in (None, "") or isinstance(value, bool):
        return value
    if fmt == "text":
        return str(value)
    try:
        so = Decimal(str(value))
    except InvalidOperation:
        return value
    if fmt == "num":
        return f"{so:,.2f}"
    if fmt == "pct":
        return f"{so * 100:,.2f}%"
    if fmt == "usd":
        return ("-" if so < 0 else "") + f"${abs(so):,.2f}"
    if fmt == "vnd":
        return f"{so:,.0f}".replace(",", ".") + " ₫"
    return value


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
    is_waybill: bool = False
    key_column: object = None
    products: list = field(default_factory=list)


def waybill_table():
    return dispatch_service.waybill_table()


def is_waybill(table):
    """Bảng vận đơn có thêm luật riêng theo tệp thật — ADR-009."""
    return table.code == WAYBILL_TABLE_CODE


def key_column(columns):
    """Cột khoá của bảng, hoặc None."""
    return next((c for c in columns if c.is_key), None)


def params_without(params, exclude=()):
    """Các cặp `(khoá, giá trị)` của mọi tham số **trừ** hệ thống và `exclude`
    — để một bộ lọc mới cộng dồn với bộ lọc cũ."""
    return [
        (k, v) for k in params.keys()
        if k not in SYSTEM_PARAMS and k not in exclude
        for v in params.getlist(k)
    ]


def qs_without(params, exclude=()):
    """Chuỗi truy vấn của `params_without` — chip "bỏ lọc" bỏ đúng một cái."""
    q = QueryDict("", mutable=True)
    for k, v in params_without(params, exclude):
        q.appendlist(k, v)
    return q.urlencode()


def display_columns(table, columns=None):
    """Cột theo thứ tự hiển thị. Bảng vận đơn: theo tệp thật, cột sản phẩm
    chèn vào chỗ đánh dấu, cột lạ xếp cuối. Bảng khác: theo thứ tự tạo cột."""
    columns = list(columns if columns is not None else table.columns.order_by("order", "id"))
    if table.code == ACTIVE_WAYBILL_TABLE_CODE:
        order = {c[1]: i for i, c in enumerate(waybill_service.COLUMNS)}
        return sorted(columns, key=lambda c: (order.get(c.code, len(order)), c.order, c.pk))
    if not is_waybill(table):
        return columns
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


def waybill_groups(columns):
    """Tiêu đề nhóm cố định của mẫu; cột người dùng thêm nằm cuối."""
    info = {c[1] for c in waybill_service.COLUMNS[:15]}
    payment = {c[1] for c in waybill_service.COLUMNS[16:]}
    groups = []
    for c in columns:
        label = ("THÔNG TIN ĐƠN HÀNG" if c.code in info else
                 "THÔNG TIN THANH TOÁN" if c.code in payment else
                 "VẬN CHUYỂN" if c.code == "trang_thai_vc" else "BỔ SUNG")
        if groups and groups[-1]["label"] == label:
            groups[-1]["span"] += 1
            groups[-1]["codes"].append(c.code)
        else:
            groups.append({"label": label, "span": 1, "codes": [c.code]})
    return groups


def frozen_columns(columns, *, waybill=True):
    """Các cột cố định bên trái khi cuộn ngang, kèm vị trí `left` (px)."""
    if waybill:
        cap = zip(columns[:GRID_FROZEN_COLUMNS], choices.FROZEN_WIDTHS)
    else:
        cap = [(c, GRID_FROZEN_WIDTH_DEFAULT) for c in columns[:GRID_FROZEN_COLUMNS_GENERIC]]
    ket_qua = []
    trai = 0
    for cot, rong in cap:
        ket_qua.append((cot.code, trai, rong))
        trai += rong
    return ket_qua


def duplicate_phones(table):
    """Queryset số điện thoại xuất hiện ở hơn một dòng của bảng — cho `?trung=1`.
    Một GROUP BY trên chỉ mục `(table, val_phone)` thay vì subquery từng dòng (K27)."""
    return (
        DataRecord.objects.filter(table=table).exclude(val_phone="")
        .order_by().values("val_phone").annotate(n=Count("id")).filter(n__gt=1).values("val_phone")
    )


def attach_duplicate_counts(table, records):
    """Gắn `so_trung` cho các dòng **của một trang**: một truy vấn đếm theo số
    điện thoại của đúng những dòng đó, thay vì subquery tương quan chạy trên
    toàn bảng trước khi cắt trang (trang 500 của 100.000 dòng: 50.000 lần, K27).
    Số trống không tính là trùng với nhau. Trả về chính danh sách đã gắn."""
    records = list(records)
    so = {r.val_phone for r in records if r.val_phone}
    dem = {}
    if so:
        dem = dict(
            DataRecord.objects.filter(table=table, val_phone__in=so)
            .order_by().values_list("val_phone").annotate(n=Count("id"))
        )
    for r in records:
        r.so_trung = dem.get(r.val_phone, 0) if r.val_phone else 0
    return records


def duplicate_count(table):
    """Biểu thức đếm số dòng cùng số điện thoại trong bảng — cột "Lọc trùng"
    cho **một vài dòng** (dòng vừa tạo, vừa dán); cả trang thì dùng
    `attach_duplicate_counts`. Số trống thì không tính là trùng với nhau."""
    cung_so = (
        DataRecord.objects.filter(table=table, val_phone=OuterRef("val_phone"))
        .order_by().values("val_phone").annotate(n=Count("id")).values("n")
    )
    return Case(
        When(val_phone="", then=Value(0)),
        default=Subquery(cung_so, output_field=IntegerField()),
        output_field=IntegerField(),
    )


def product_columns_of(columns):
    """Các cột số lượng theo sản phẩm (`sl_<mã>`) trong bảng vận đơn."""
    return [c for c in columns if dispatch_service.is_product_column(c.code)]


def read_products(params, columns):
    """Mã cột sản phẩm đang chọn trên URL (`sp=sl_a&sp=sl_b`), chỉ nhận cột có thật."""
    co_that = {c.code for c in product_columns_of(columns)}
    lay = getattr(params, "getlist", None)
    gia_tri = lay(PRODUCT_PARAM) if lay else [params.get(PRODUCT_PARAM)]
    return [v for v in gia_tri if v in co_that]


def product_any_of(codes):
    """Dòng có **ít nhất một** trong các sản phẩm — số lượng lớn hơn 0.
    Giá trị số nguyên trong JSON được lưu là số thật nên so được với 0."""
    dieu_kien = Q()
    for ma in codes:
        dieu_kien |= Q(**{f"data__{ma}__gt": 0})
    return dieu_kien


def build_grid(user, params, *, table=None):
    """Queryset của lưới đúng như URL mô tả — chưa cắt trang."""
    table = table or waybill_table()
    van_don = is_waybill(table)
    columns = display_columns(table)
    bo_loc = query.read_filters(params, columns)
    tim = (params.get("tim") or "").strip()
    sap = params.get("sap") or ""
    giam = params.get("chieu") == "giam"
    ds, _ = query.build(
        DataRecord.objects.in_scope(user), table,
        filters=bo_loc, search=tim, sort=sap, descending=giam, columns=columns,
    )
    chi_trung = False
    san_pham = []
    if van_don:
        # Cột Trùng đếm sau khi cắt trang (`attach_duplicate_counts`); lọc chỉ
        # dòng trùng thì so với danh sách số điện thoại trùng — một GROUP BY
        chi_trung = params.get("trung") == "1"
        if chi_trung:
            ds = ds.filter(val_phone__in=duplicate_phones(table))
        san_pham = read_products(params, columns)
        if san_pham:
            ds = ds.filter(product_any_of(san_pham))
    ds = ds.select_related("table", "created_by")
    return Grid(
        table=table, columns=columns, queryset=ds, filters=bo_loc, search=tim,
        sort=sap, descending=giam, duplicates_only=chi_trung,
        chips=filter_chips(bo_loc, columns, san_pham),
        is_waybill=van_don, key_column=key_column(columns), products=san_pham,
    )


def export_queryset(user, table, params):
    """Cách dựng queryset cho `export_service` — đúng lưới đang hiện, kể cả
    hai bộ lọc riêng của lưới (`trung`, `sp`) mà bộ đọc chung không biết."""
    luoi = build_grid(user, params, table=table)
    return luoi.queryset, luoi.columns, luoi.filters


def filter_chips(bo_loc, columns, products=()):
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
    if products:
        ten_sp = [ten.get(ma, ma) for ma in products]
        chips.append((PRODUCT_PARAM, "Sản phẩm " + ", ".join(ten_sp[:3]) + (" …" if len(ten_sp) > 3 else "")))
    return chips


def cell_class(column, frozen=None, editable=True, editing=False, error=False, style=None):
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
    if column.is_key:
        lop.append("o-khoa")
    if style:
        lop.extend(style_classes(style))
    return " ".join(lop)


def frozen_style(frozen, *, offset=0):
    """Thuộc tính style của cột cố định: `left` cộng bề rộng các cột đứng
    trước nó (cột Trùng của bảng vận đơn)."""
    if not frozen:
        return ""
    trai, rong = frozen
    # `width` cho bố cục bảng cố định (table-layout: fixed) đọc được bề rộng cột
    return f"left:{trai + offset}px;width:{rong}px;min-width:{rong}px;max-width:{rong}px"


def _co_dinh(columns, waybill):
    return {ma: (trai, rong) for ma, trai, rong in frozen_columns(columns, waybill=waybill)}


def column_letter(i):
    """Chữ cột kiểu Excel: 0 → A, 25 → Z, 26 → AA."""
    chu = ""
    i += 1
    while i:
        i, du = divmod(i - 1, 26)
        chu = chr(65 + du) + chu
    return chu


def header_columns(columns, filters=None, *, waybill=True):
    """Tiêu đề cột cho template: cột, chữ cột A B C, style cố định, lớp, có
    đang lọc không. Bảng vận đơn có cột Lọc trùng là chữ A nên chữ cột thật
    bắt đầu từ B. Chữ cột tính lại ở trình duyệt khi người dùng ẩn hay kéo
    đổi thứ tự cột."""
    co_dinh = _co_dinh(columns, waybill)
    lech = left_offset(waybill)
    dang_loc = {k.partition("__")[0] for k in (filters or {})}
    ket_qua = []
    for i, c in enumerate(columns):
        cd = co_dinh.get(c.code)
        lop = ["sap-xep"]
        lop_chu = ["bt-chu"]
        if cd:
            lop.append("co-dinh")
            lop_chu.append("co-dinh")
        if c.field_type in NUMERIC_TYPES:
            lop.append("phai")
        if c.is_key:
            lop.append("th-khoa")
        ket_qua.append({
            "cot": c, "chu": column_letter(i + (1 if waybill else 0)),
            "style": frozen_style(cd, offset=lech), "lop": " ".join(lop), "lop_chu": " ".join(lop_chu),
            "lop_nut_loc": "nut-loc dang-loc" if c.code in dang_loc else "nut-loc",
        })
    return ket_qua


def grid_url(table):
    """URL của lưới một bảng — gốc để ghép URL từng ô."""
    return reverse("bang_tinh_xem", args=[table.code])


def cell_url(goc, pk, code):
    """URL sửa một ô, ghép chuỗi trên gốc lưới `goc` (`grid_url`).

    Cùng khuôn với `bang_tinh_o` trong `crm/urls.py` — cố ý không gọi
    `reverse()` từng ô: một trang lưới có 3.900 ô, `reverse()` 7.800 lần mất
    0,4 giây (K27). `test_bang_tinh_hieu_nang` giữ hai bên khớp nhau.
    """
    return f"{goc}o/{pk}/{code}/"


def cell_html(bang, ban_ghi, cot, *, gia_tri, hien, duoc_sua, lop, style="", qs_giu="",
              oob=False, goc=None):
    """HTML của **một ô** — nơi duy nhất quyết định ô trông thế nào (ADR-011).

    Dựng bằng chuỗi thay vì template `{% include %}` từng ô: vẽ 100 dòng × 39
    cột qua template mất ~0,5 giây một trang, ghép chuỗi mất ~0,05 giây (K27).
    Dùng khi vẽ lưới, khi HTMX trả về sau khi lưu, khi huỷ sửa, khi đổi định
    dạng. Bấm một lần là chọn, bấm đúp hoặc Enter mới sửa. `gia_tri` là giá
    trị thô (vào `data-goc`), `hien` là chữ đã định dạng số (None → giá trị
    thô), `oob` vẽ lại ô tại chỗ (hx-swap-oob), `goc` là URL lưới (`grid_url`)
    để ghép URL sửa ô; thiếu thì tự tìm.
    """
    pk = ban_ghi.pk
    goc_gt = "" if gia_tri is None else str(gia_tri)
    chu = goc_gt if hien is None else str(hien)
    goc = goc if goc is not None else grid_url(bang)
    lien_ket = ""
    if cot.is_key and gia_tri:
        hoi = f"{escape(qs_giu)}&amp;" if qs_giu else ""
        lien_ket = (f'<a class="o-khoa-loc" href="{goc}?{hoi}f_{cot.code}={quote(goc_gt, safe="/")}" '
                    f'title="Lọc theo giá trị này">⌕</a>')
    thuoc = f' style="{escape(style)}"' if style else ""
    if oob:
        thuoc += ' hx-swap-oob="outerHTML"'
    if bang.code == ACTIVE_WAYBILL_TABLE_CODE and cot.code in waybill_service.DETAIL_CELLS:
        url = reverse("waybill_detail", args=[pk])
        return mark_safe(
            f'<td class="{lop}" id="o-{pk}-{cot.code}"{thuoc} tabindex="0" data-dong="{pk}" data-cot="{cot.code}" '
            f'data-goc="{escape(goc_gt)}" data-waybill-detail="{url}" '
            f'title="{escape(cot.name)} — mở chi tiết sản phẩm">{escape(chu)}</td>'
        )
    if bang.code == ACTIVE_WAYBILL_TABLE_CODE and cot.code in waybill_service.PROTECTED:
        duoc_sua = False
    if duoc_sua and not cot.is_computed:
        url = cell_url(goc, pk, cot.code)
        return mark_safe(
            f'<td class="{lop}" id="o-{pk}-{cot.code}"{thuoc} tabindex="0" data-dong="{pk}" data-cot="{cot.code}" '
            f'data-goc="{escape(goc_gt)}" data-sua-url="{url}" hx-get="{url}" hx-trigger="dblclick" hx-swap="outerHTML" '
            f'title="{escape(cot.name)} — bấm đúp hoặc Enter để sửa">{escape(chu)}{lien_ket}</td>'
        )
    return mark_safe(
        f'<td class="{lop}" id="o-{pk}-{cot.code}"{thuoc} data-dong="{pk}" data-cot="{cot.code}" '
        f'data-goc="{escape(goc_gt)}" tabindex="0">{escape(chu)}{lien_ket}</td>'
    )


def row_context(record, columns, user, *, waybill=True, co_dinh=None, stt=None, qs_giu="", goc=None):
    """Một dòng cho template: ô theo thứ tự cột, lớp màu, số trùng, sửa được
    không, số dòng `stt` (hàng tên cột là 1, dữ liệu từ 2 — ADR-011)."""
    co_dinh = co_dinh if co_dinh is not None else _co_dinh(columns, waybill)
    lech = left_offset(waybill)
    goc = goc if goc is not None else grid_url(record.table)
    sua = grant_service.can_edit_record(user, record)
    so_trung = getattr(record, "so_trung", 0) or 0
    kieu = record.style or {}
    du_lieu = record.data
    cac_o = []
    for c in columns:
        gia_tri = du_lieu.get(c.code)
        st = kieu.get(c.code)
        cd = co_dinh.get(c.code)
        lop = cell_class(c, cd, sua, style=st)
        hien = display_value(c, gia_tri, st)
        cac_o.append({
            "cot": c, "gia_tri": gia_tri, "hien": hien, "id": f"o-{record.pk}-{c.code}", "lop": lop,
            "style": frozen_style(cd, offset=lech),
            "html": cell_html(record.table, record, c, gia_tri=gia_tri, hien=hien, duoc_sua=sua, lop=lop,
                              style=frozen_style(cd, offset=lech), qs_giu=qs_giu, goc=goc),
        })
    return {
        "ban_ghi": record,
        "stt": stt,
        "cac_o": cac_o,
        "sua": sua,
        "lop": choices.row_class(record.data.get("trang_thai_vc")) if waybill or record.table.code == ACTIVE_WAYBILL_TABLE_CODE else "",
        "so_trung": so_trung,
        "lop_trung": "co-dinh tien o-trung" if so_trung > 1 else "co-dinh tien",
        "style_trung": duplicate_style(),
    }


def rows(records, columns, user, *, waybill=True, start=2, qs_giu=""):
    """Các dòng của một trang; số dòng bắt đầu từ `start` (trang đầu: 2).
    `qs_giu` là bộ lọc đang bật, để liên kết ⌕ của cột khoá cộng dồn."""
    co_dinh = _co_dinh(columns, waybill)
    records = list(records)
    goc = grid_url(records[0].table) if records else None
    return [
        row_context(r, columns, user, waybill=waybill, co_dinh=co_dinh, stt=start + i, qs_giu=qs_giu, goc=goc)
        for i, r in enumerate(records)
    ]


def spare_rows(columns, n=GRID_SPARE_ROWS, *, waybill=True, values=None, error_column=None, start=1):
    """`n` dòng trống cuối lưới để gõ bản ghi mới — như Excel luôn thừa dòng.
    `values` và `error_column` dùng khi vẽ lại một dòng bị từ chối; `start` là
    số dòng của dòng trống đầu tiên."""
    co_dinh = _co_dinh(columns, waybill)
    lech = left_offset(waybill)
    values = values or {}
    ket_qua = []
    for i in range(n):
        cac_o = []
        for c in columns:
            cd = co_dinh.get(c.code)
            lop = ["o-moi"]
            if cd:
                lop.append("co-dinh")
            if c.field_type in NUMERIC_TYPES:
                lop.append("tien")
            if c.is_computed:
                lop.append("o-tinh")
            if error_column == c.code and i == 0:
                lop.append("o-loi")
            cac_o.append({
                "cot": c, "lop": " ".join(lop), "style": frozen_style(cd, offset=lech),
                "gia_tri": values.get(c.code, "") if i == 0 else "",
            })
        ket_qua.append({"stt": start + i, "cac_o": cac_o, "style_trung": duplicate_style()})
    return ket_qua


# ── Định dạng ô — Giai đoạn B ─────────────────────────────────────

#: Khoá → giá trị → lớp CSS. Lớp là cố định để bài quét CSS kiểm được, và để
#: không có CSS tự do nào từ dữ liệu lọt vào trang.
STYLE_CLASSES = {
    "b": {1: "dd-dam"},
    "i": {1: "dd-nghieng"},
    "u": {1: "dd-gach-chan"},
    "st": {1: "dd-gach-ngang"},
    "wr": {1: "dd-xuong-dong"},
    "bd": {1: "dd-vien"},
    "bg": {
        "vang": "dd-nen-vang", "xanh": "dd-nen-xanh", "do": "dd-nen-do",
        "luc": "dd-nen-luc", "xam": "dd-nen-xam", "cam": "dd-nen-cam",
        **{k: f"dd-nen-{k}" for k in record_service.PALETTE_KEYS},
    },
    "c": {k: f"dd-chu-{k}" for k in record_service.PALETTE_KEYS},
    "fs": {n: f"dd-co-{n}" for n in sorted(record_service.STYLE_SCHEMA["fs"])},
    "al": {"l": "dd-can-trai", "c": "dd-can-giua", "r": "dd-can-phai"},
    "fmt": {
        "num": "dd-dinh-so", "pct": "dd-dinh-phan-tram", "usd": "dd-dinh-usd",
        "vnd": "dd-dinh-vnd", "text": "dd-dinh-chu",
    },
}


def style_classes(style):
    """Lớp CSS của một bộ định dạng ô; khoá hoặc giá trị lạ bị bỏ qua."""
    if not isinstance(style, dict):
        return []
    lop = []
    for khoa, gia_tri in style.items():
        bang = STYLE_CLASSES.get(khoa)
        if bang is None:
            continue
        try:
            ten = bang.get(int(gia_tri) if khoa in record_service.STYLE_ON or khoa == "fs" else gia_tri)
        except (TypeError, ValueError):
            ten = None
        if ten:
            lop.append(ten)
    return lop


# ── Lọc theo cột ──────────────────────────────────────────────────

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
