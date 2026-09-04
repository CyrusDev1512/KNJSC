"""Quy tắc thêm, sửa, xoá bản ghi trong bảng động.

Tầng dịch vụ (điều cấm 2). Mọi thay đổi ghi nhật ký (BR-5), xoá là đánh dấu
(BR-4), tiền lưu dạng số thập phân chính xác (BR-8).

**Không bao giờ gọi `record.save(update_fields=["data"])`.** `DataRecord.save()`
tính lại bảy cột tách `val_*` trong bộ nhớ, nhưng `update_fields` chỉ ghi cột
`data` xuống cơ sở dữ liệu. Kết quả: JSON một đằng, cột tách một nẻo — màn hình
vẫn hiện đúng còn lọc và thống kê thì sai.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction

from core.audit import record
from core.constants import AuditAction
from core.exceptions import BusinessError
from core.money import parse_money

from .. import choice_registry
from ..meaning import FieldType
from ..models import DataRecord

#: Giá trị người dùng gõ vào được hiểu là "đúng"
TRUE_WORDS = frozenset({"1", "true", "co", "có", "x", "yes", "dung", "đúng"})


def parse_value(column, raw):
    """Ép giá trị người dùng gõ về đúng kiểu của cột.

    Trả về giá trị đã chuẩn hoá, hoặc ném `BusinessError` với thông báo tiếng
    Việt nói rõ cột nào sai (NFR-6).
    """
    if raw is None:
        return None
    if isinstance(raw, str):
        raw = raw.strip()
        if raw == "":
            return None

    kieu = column.field_type
    try:
        if kieu in (FieldType.TEXT, FieldType.LONG_TEXT, FieldType.CHOICE):
            # Excel hay tự đổi số điện thoại thành số thực: 7788599010.0
            if isinstance(raw, float) and raw.is_integer():
                raw = str(int(raw))
            raw = str(raw)
            if kieu == FieldType.CHOICE:
                # Cột có sổ danh sách thì chỉ nhận giá trị trong sổ, và đưa
                # về đúng nhãn ("Đã Thanh Toán" → "Đã thanh toán")
                raw, hop_le = choice_registry.normalise(column.table.code, column.code, raw)
                if not hop_le:
                    raise BusinessError(
                        f'Giá trị "{raw}" không có trong danh sách của cột "{column.name}". '
                        "Chọn: " + ", ".join(choice_registry.options_for(column.table.code, column.code))
                    )
            return raw
        if kieu == FieldType.INTEGER:
            if isinstance(raw, bool):
                raise ValueError(raw)
            if isinstance(raw, (int, float, Decimal)):
                # Ô Excel là số thật: 3.0 là 3, còn 3.5 thì không phải số nguyên
                so = Decimal(str(raw))
                if so != so.to_integral_value():
                    raise ValueError(raw)
                return int(so)
            return int(str(raw).replace(".", "").replace(",", "").replace(" ", ""))
        if kieu in (FieldType.DECIMAL, FieldType.MONEY):
            # Số thật từ Excel nhận nguyên trạng — đưa "1234.567" qua
            # parse_money sẽ bị hiểu là 1.234.567 theo tập quán Việt Nam.
            if isinstance(raw, (int, float, Decimal)) and not isinstance(raw, bool):
                return str(Decimal(str(raw)))
            # Tiền và số thập phân luôn qua Decimal, không qua float (BR-8).
            # Đọc theo tập quán Việt Nam để nhận lại được đúng thứ màn hình
            # đang hiện — xem core.money.parse_money
            return str(parse_money(raw))
        if kieu == FieldType.DATE:
            if isinstance(raw, (date, datetime)):
                return raw.strftime("%Y-%m-%d")
            return date.fromisoformat(str(raw)).isoformat()
        if kieu == FieldType.DATETIME:
            if isinstance(raw, datetime):
                return raw.isoformat()
            return datetime.fromisoformat(str(raw)).isoformat()
        if kieu == FieldType.BOOLEAN:
            return str(raw).strip().lower() in TRUE_WORDS
    except (ValueError, TypeError, InvalidOperation):
        raise BusinessError(
            f'Giá trị "{raw}" không đúng kiểu {FieldType(kieu).label} '
            f'của cột "{column.name}".'
        )
    return str(raw)


def _thieu_bat_buoc(columns, values):
    """Tên các cột bắt buộc còn để trống."""
    return [
        c.name for c in columns
        if c.required and not c.is_computed and values.get(c.code) in (None, "")
    ]


@transaction.atomic
def create_record(table, values, *, actor=None, request=None, columns=None):
    """Thêm một dòng vào bảng.

    Bộ phận và team lấy theo hồ sơ người tạo, để phạm vi quyền áp đúng ngay từ
    lúc sinh ra bản ghi.
    """
    columns = columns if columns is not None else list(table.columns.all())
    du_lieu = {}
    for cot in columns:
        if cot.is_computed:
            continue
        if cot.code in values:
            du_lieu[cot.code] = parse_value(cot, values[cot.code])

    thieu = _thieu_bat_buoc(columns, du_lieu)
    if thieu:
        raise BusinessError("Chưa điền các trường bắt buộc: " + ", ".join(thieu))

    ho_so = getattr(actor, "profile", None)
    ban_ghi = DataRecord(
        table=table, data=du_lieu, created_by=actor,
        # Dòng thuộc về bộ phận **sở hữu bảng**, không phải bộ phận người ghi.
        # Hai cái này trùng nhau ở mọi bảng báo cáo, nhưng khác nhau ở bảng
        # vận đơn: Sale lên đơn, dòng phải thuộc về Vận đơn để họ thấy mà đi
        # giao. Lấy theo người ghi là bộ phận đích không thấy gì cả.
        department=table.department,
        team=getattr(ho_so, "team", None),
    )
    ban_ghi.apply_computed_columns(columns)
    ban_ghi.sync_indexed_columns(columns)
    ban_ghi.save(skip_sync=True)

    record(
        AuditAction.CREATE, actor=actor, target=ban_ghi,
        detail=f"Thêm dòng vào bảng {table.code}", request=request,
    )
    return ban_ghi


@dataclass
class BulkResult:
    """Kết quả nhập hàng loạt: số dòng đã vào và danh sách (số dòng, lỗi)."""

    created: int = 0
    errors: list = field(default_factory=list)


def create_records_bulk(table, rows, *, actor=None, request=None, columns=None,
                        batch=500, on_progress=None, row_numbers=None):
    """Thêm nhiều dòng một lượt — nền của nhập tệp Excel (FR-7.5) và seed.

    Khác `create_record` ở ba chỗ, cố ý:

    - **Dòng lỗi không chặn dòng sau** (AC-7.6): lỗi thu vào `errors` kèm số
      dòng, dòng hợp lệ vẫn vào. `row_numbers` cho biết số hàng thật trong
      tệp để người dùng tìm lại được; không có thì đếm từ 1.
    - **Ghi theo lô** bằng `bulk_create`, mỗi lô một giao dịch. `bulk_create`
      không gọi `save()`, nên cột tính sẵn và cột tách phải gọi tay ở đây —
      quên là lọc và thống kê sai âm thầm (xem cảnh báo đầu tệp).
    - **Một dòng nhật ký** tóm tắt cho cả lượt, không mỗi dòng một dòng nhật
      ký — 5.000 dòng nhật ký cho một lần bấm nhập là che mất mọi thứ khác.
    """
    columns = columns if columns is not None else list(table.columns.all())
    ho_so = getattr(actor, "profile", None)
    team = getattr(ho_so, "team", None)
    ket_qua = BulkResult()
    lo = []

    def ghi_lo():
        if not lo:
            return
        with transaction.atomic():
            DataRecord.objects.bulk_create(lo)
        ket_qua.created += len(lo)
        lo.clear()

    for i, values in enumerate(rows):
        so_dong = row_numbers[i] if row_numbers else i + 1
        try:
            du_lieu = {}
            for cot in columns:
                if cot.is_computed:
                    continue
                gia_tri = values.get(cot.code)
                if gia_tri in (None, ""):
                    continue
                du_lieu[cot.code] = parse_value(cot, gia_tri)
            thieu = _thieu_bat_buoc(columns, du_lieu)
            if thieu:
                raise BusinessError("Thiếu cột bắt buộc: " + ", ".join(thieu))
        except BusinessError as loi:
            ket_qua.errors.append((so_dong, str(loi)))
            continue

        ban_ghi = DataRecord(
            table=table, data=du_lieu, created_by=actor,
            department=table.department, team=team,
        )
        ban_ghi.apply_computed_columns(columns)
        ban_ghi.sync_indexed_columns(columns)
        lo.append(ban_ghi)
        if len(lo) >= batch:
            ghi_lo()
            if on_progress:
                on_progress(i + 1)
    ghi_lo()

    record(
        AuditAction.IMPORT, actor=actor, target=table,
        detail=(f"Nhập {ket_qua.created} dòng vào bảng {table.code}"
                + (f", bỏ qua {len(ket_qua.errors)} dòng lỗi" if ket_qua.errors else "")),
        request=request,
    )
    return ket_qua


@transaction.atomic
def update_cell(ban_ghi, code, raw, *, actor=None, request=None, columns=None):
    """Sửa đúng một ô trên bảng — FR-7.4.

    Truyền sẵn `columns` khi sửa nhiều ô liên tiếp: mỗi lần để hàm tự lấy là
    thêm một lệnh truy vấn (quy tắc Q2).
    """
    columns = columns if columns is not None else list(ban_ghi.table.columns.all())
    cot = next((c for c in columns if c.code == code), None)
    if cot is None:
        raise BusinessError("Cột này không có trong bảng.")
    if cot.is_computed:
        raise BusinessError(f'Cột "{cot.name}" là cột tính sẵn, không sửa tay được.')

    cu = ban_ghi.data.get(code)
    moi = parse_value(cot, raw)
    if cu == moi:
        return ban_ghi
    if cot.required and moi in (None, ""):
        raise BusinessError(f'Cột "{cot.name}" bắt buộc nhập, không để trống được.')

    ban_ghi.data[code] = moi
    ban_ghi.apply_computed_columns(columns)
    ban_ghi.sync_indexed_columns(columns)
    ban_ghi.save(skip_sync=True)

    record(
        AuditAction.UPDATE, actor=actor, target=ban_ghi,
        detail=(
            f"Sửa ô {ban_ghi.table.code}.{code} — "
            f"{_hien(cu)} → {_hien(moi)}"
        ),
        request=request,
    )
    return ban_ghi


@transaction.atomic
def delete_record(ban_ghi, *, actor=None, request=None):
    """Xoá một dòng. Đánh dấu chứ không xoá khỏi cơ sở dữ liệu (BR-4)."""
    ma_bang = ban_ghi.table.code
    ban_ghi.delete(by=actor)
    record(
        AuditAction.DELETE, actor=actor, target=ban_ghi,
        detail=f"Xoá dòng khỏi bảng {ma_bang}", request=request,
    )
    return ban_ghi


def _hien(gia_tri):
    """Giá trị rỗng hiện thành dấu gạch cho nhật ký dễ đọc."""
    return "—" if gia_tri in (None, "") else str(gia_tri)


# ══ ĐỊNH DẠNG Ô — ADR-010 ═════════════════════════════════════════

#: Sổ định dạng ô: khoá ngắn, giá trị đóng. Không nhận CSS tự do từ người
#: dùng (an toàn), và giao diện dịch từng giá trị sang một lớp CSS cố định
#: (`crm.services.grid_service.STYLE_CLASSES`). Muốn thêm màu hay cỡ chữ thì
#: thêm ở cả hai chỗ.
#: Bảng 40 màu chữ và nền (theo bảng màu của KN Demo — ADR-011). Giá trị lưu
#: là khoá `m01`…`m40`; mã màu chỉ nằm ở đây và trong khối CSS sinh từ đây
#: (`scripts/sinh-css-mau.py`), không bao giờ vào dữ liệu hay trang.
PALETTE = (
    ("m01", "#000000"), ("m02", "#334155"), ("m03", "#64748b"), ("m04", "#94a3b8"),
    ("m05", "#cbd5e1"), ("m06", "#e2e8f0"), ("m07", "#f1f5f9"), ("m08", "#ffffff"),
    ("m09", "#7f1d1d"), ("m10", "#b91c1c"), ("m11", "#ef4444"), ("m12", "#f97316"),
    ("m13", "#f59e0b"), ("m14", "#eab308"), ("m15", "#84cc16"), ("m16", "#22c55e"),
    ("m17", "#14b8a6"), ("m18", "#06b6d4"), ("m19", "#3b82f6"), ("m20", "#3370ff"),
    ("m21", "#6366f1"), ("m22", "#8b5cf6"), ("m23", "#a855f7"), ("m24", "#d946ef"),
    ("m25", "#ec4899"), ("m26", "#f43f5e"), ("m27", "#fecaca"), ("m28", "#fed7aa"),
    ("m29", "#fde68a"), ("m30", "#fef08a"), ("m31", "#d9f99d"), ("m32", "#bbf7d0"),
    ("m33", "#99f6e4"), ("m34", "#a5f3fc"), ("m35", "#bfdbfe"), ("m36", "#c7d2fe"),
    ("m37", "#ddd6fe"), ("m38", "#e9d5ff"), ("m39", "#f5d0fe"), ("m40", "#fbcfe8"),
)
PALETTE_KEYS = frozenset(k for k, _ in PALETTE)
#: Sáu tên màu nền của ADR-010 vẫn nhận — dữ liệu cũ không phải chuyển đổi
BG_LEGACY = frozenset({"vang", "xanh", "do", "luc", "xam", "cam"})
#: Khoá bật/tắt: chỉ có giá trị 1 (bật); gửi rỗng là tắt
STYLE_ON = frozenset({"b", "i", "u", "st", "wr", "bd"})
STYLE_SCHEMA = {
    "b": {1},                                             # in đậm
    "i": {1},                                             # nghiêng
    "u": {1},                                             # gạch chân
    "st": {1},                                            # gạch ngang
    "wr": {1},                                            # xuống dòng trong ô
    "bd": {1},                                            # kẻ viền ô
    "bg": BG_LEGACY | PALETTE_KEYS,                       # màu nền
    "c": PALETTE_KEYS,                                    # màu chữ
    "fs": {10, 11, 12, 13, 14, 16, 18, 20, 24, 28},       # cỡ chữ (px); 13 là cỡ lưới
    "al": {"l", "c", "r"},                                # căn lề
    "fmt": {"num", "pct", "usd", "vnd", "text"},          # định dạng số khi hiển thị
}
STYLE_LABELS = {
    "b": "đậm", "i": "nghiêng", "u": "gạch chân", "st": "gạch ngang", "wr": "xuống dòng",
    "bd": "viền", "bg": "nền", "c": "màu chữ", "fs": "cỡ", "al": "căn", "fmt": "định dạng số",
}
#: Gửi lên với giá trị này nghĩa là **bỏ** thuộc tính đó
STYLE_EMPTY = (None, "", 0, "0", False)


def normalise_style(raw):
    """Chuẩn hoá một bộ định dạng theo sổ. Khoá rỗng bị bỏ; khoá hoặc giá trị
    ngoài sổ thì `BusinessError` — tham số đến từ trình duyệt, không tin được."""
    if not isinstance(raw, dict):
        raise BusinessError("Định dạng ô không hợp lệ.")
    ket_qua = {}
    for khoa, gia_tri in raw.items():
        if khoa not in STYLE_SCHEMA:
            raise BusinessError(f'Định dạng "{khoa}" không có trong sổ.')
        if gia_tri in STYLE_EMPTY:
            continue
        if khoa in STYLE_ON or khoa == "fs":
            try:
                gia_tri = int(gia_tri)
            except (TypeError, ValueError):
                raise BusinessError(f'Giá trị "{gia_tri}" không dùng được cho {STYLE_LABELS[khoa]}.')
        if gia_tri not in STYLE_SCHEMA[khoa]:
            raise BusinessError(f'Giá trị "{gia_tri}" không dùng được cho {STYLE_LABELS[khoa]}.')
        ket_qua[khoa] = gia_tri
    return ket_qua


def _ta_style(style):
    return " ".join(f"{STYLE_LABELS[k]}={v}" for k, v in sorted((style or {}).items())) or "trống"


def _ap_dinh_dang(ban_ghi, code, style, columns, *, replace=False):
    """Gộp (hoặc thay hẳn) định dạng một ô trong bộ nhớ. Trả `(đổi không, cũ, mới)`."""
    if not any(c.code == code for c in columns):
        raise BusinessError("Cột này không có trong bảng.")
    moi = normalise_style(style)
    hien = dict(ban_ghi.style or {})
    cu = dict(hien.get(code) or {})
    if replace:
        gop = moi
    else:
        gop = dict(cu)
        for khoa, gia_tri in (style or {}).items():
            if khoa in STYLE_SCHEMA and gia_tri in STYLE_EMPTY:
                gop.pop(khoa, None)
        gop.update(moi)
    if gop == cu:
        return False, cu, gop
    if gop:
        hien[code] = gop
    else:
        hien.pop(code, None)
    ban_ghi.style = hien
    return True, cu, gop


@transaction.atomic
def update_style(ban_ghi, code, style, *, actor=None, request=None, columns=None, replace=False):
    """Đổi định dạng một ô — ADR-010. Lưu vào `DataRecord.style`, mọi người
    cùng thấy; mỗi lần đổi một dòng nhật ký (BR-5). Không đụng `data` nên
    ghi bằng `update_fields`, an toàn với bảy cột tách."""
    columns = columns if columns is not None else list(ban_ghi.table.columns.all())
    doi, cu, moi = _ap_dinh_dang(ban_ghi, code, style, columns, replace=replace)
    if not doi:
        return ban_ghi
    ban_ghi.save(update_fields=["style", "updated_at"], skip_sync=True)
    record(
        AuditAction.UPDATE, actor=actor, target=ban_ghi,
        detail=f"Định dạng ô {ban_ghi.table.code}.{code} — {_ta_style(cu)} → {_ta_style(moi)}",
        request=request,
    )
    return ban_ghi


@transaction.atomic
def update_styles(cells, style, *, actor=None, request=None, columns=None, replace=False):
    """Đổi định dạng nhiều ô một lần — `cells` là danh sách `(bản ghi, mã cột)`.
    Một giao dịch, mỗi bản ghi ghi một lần, một dòng nhật ký tóm tắt.
    Trả về số ô đã đổi."""
    da_doi = 0
    ban_ghi_doi = {}
    for ban_ghi, code in cells:
        cot = columns if columns is not None else list(ban_ghi.table.columns.all())
        doi, _, _ = _ap_dinh_dang(ban_ghi, code, style, cot, replace=replace)
        if doi:
            da_doi += 1
            ban_ghi_doi[ban_ghi.pk] = ban_ghi
    if not da_doi:
        return 0
    for ban_ghi in ban_ghi_doi.values():
        ban_ghi.save(update_fields=["style", "updated_at"], skip_sync=True)
    dau = cells[0][0]
    record(
        AuditAction.UPDATE, actor=actor, target=dau,
        detail=(f"Định dạng {da_doi} ô của bảng {dau.table.code} — "
                + ("bỏ hết" if replace and not normalise_style(style) else _ta_style(normalise_style(style)))),
        request=request,
    )
    return da_doi
