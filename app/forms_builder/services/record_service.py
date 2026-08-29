"""Quy tắc thêm, sửa, xoá bản ghi trong bảng động.

Tầng dịch vụ (điều cấm 2). Mọi thay đổi ghi nhật ký (BR-5), xoá là đánh dấu
(BR-4), tiền lưu dạng số thập phân chính xác (BR-8).

**Không bao giờ gọi `record.save(update_fields=["data"])`.** `DataRecord.save()`
tính lại bảy cột tách `val_*` trong bộ nhớ, nhưng `update_fields` chỉ ghi cột
`data` xuống cơ sở dữ liệu. Kết quả: JSON một đằng, cột tách một nẻo — màn hình
vẫn hiện đúng còn lọc và thống kê thì sai.
"""
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
            return str(raw)
        if kieu == FieldType.INTEGER:
            return int(str(raw).replace(".", "").replace(",", "").replace(" ", ""))
        if kieu in (FieldType.DECIMAL, FieldType.MONEY):
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
