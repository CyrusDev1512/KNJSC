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
                return str(int(raw))
            return str(raw)
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
