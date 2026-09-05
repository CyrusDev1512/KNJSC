"""Quy tắc tạo và sửa bảng động.

Tầng dịch vụ, không biết gì về HTTP (điều cấm 2). Mọi thao tác ghi đều ghi
nhật ký hoạt động (BR-5) và nằm trong một giao dịch.

`ColumnDef.clean()` **không** tự chạy khi gọi `save()` — Django chỉ chạy nó qua
`full_clean()`. Nên mọi hàm ở đây gọi `full_clean()` trước khi lưu; bỏ qua là
lọt cấu hình hỏng vào cơ sở dữ liệu.
"""
from django.db import transaction

from core.audit import record
from core.constants import AuditAction

from ..models import ColumnDef, DataRecord, TableDef


@transaction.atomic
def create_table(*, name, code, department, description="", actor=None, request=None):
    """Tạo một bảng mới. Bảng thuộc về bộ phận, không thuộc về team."""
    bang = TableDef(
        name=name, code=code, department=department,
        description=description, created_by=actor,
    )
    bang.full_clean(exclude=["created_by"])
    bang.save()
    record(
        AuditAction.CREATE, actor=actor, target=bang,
        detail=f"Tạo bảng dữ liệu {code}", request=request,
    )
    return bang


@transaction.atomic
def update_table(table, changes, *, actor=None, request=None):
    """Sửa tên hoặc mô tả bảng. Không đổi được tên kỹ thuật."""
    da_doi = []
    for ten in ("name", "description", "is_active"):
        if ten not in changes:
            continue
        cu, moi = getattr(table, ten), changes[ten]
        if cu == moi:
            continue
        da_doi.append(f"{table._meta.get_field(ten).verbose_name}: {cu} → {moi}")
        setattr(table, ten, moi)

    if not da_doi:
        return table

    table.full_clean(exclude=["created_by"])
    table.save()
    record(
        AuditAction.UPDATE, actor=actor, target=table,
        detail=f"Sửa bảng {table.code} — " + " · ".join(da_doi), request=request,
    )
    return table


# ══ CỘT ═══════════════════════════════════════════════════════════

#: Trường của cột mà người dùng sửa được
COLUMN_FIELDS = (
    "name", "code", "field_type", "meaning", "required", "order", "is_key",
    "is_computed", "compute_op", "compute_left", "compute_right", "compute_decimals",
)

#: Đổi một trong những trường này thì số liệu đã lưu phải tính lại — ADR-006
RECOMPUTE_FIELDS = frozenset(
    {"is_computed", "compute_op", "compute_left", "compute_right", "compute_decimals"}
)


@transaction.atomic
def add_column(table, *, actor=None, request=None, **fields):
    """Thêm một cột vào bảng.

    Cột mang nhãn ý nghĩa sẽ được tách sang cột riêng có chỉ mục trên
    `DataRecord` (ADR-001). Bản ghi đã có sẽ được đồng bộ ngay, nếu không thì
    lọc theo cột đó sẽ bỏ sót toàn bộ dữ liệu cũ.
    """
    cot = ColumnDef(table=table, **{k: v for k, v in fields.items() if k in COLUMN_FIELDS})
    if not cot.order:
        cot.order = _thu_tu_ke_tiep(table)
    cot.full_clean()
    cot.save()

    if cot.meaning or cot.is_computed:
        resync_table(table)

    record(
        AuditAction.CREATE, actor=actor, target=cot,
        detail=f"Thêm cột {cot.code} vào bảng {table.code}", request=request,
    )
    return cot


@transaction.atomic
def update_column(column, changes, *, actor=None, request=None):
    """Sửa một cột. Đổi công thức thì tính lại toàn bộ bản ghi cũ."""
    da_doi, phai_tinh_lai = [], False
    for ten in COLUMN_FIELDS:
        if ten not in changes:
            continue
        cu, moi = getattr(column, ten), changes[ten]
        if cu == moi:
            continue
        da_doi.append(f"{column._meta.get_field(ten).verbose_name}: {cu} → {moi}")
        setattr(column, ten, moi)
        if ten in RECOMPUTE_FIELDS or ten == "meaning":
            phai_tinh_lai = True

    if not da_doi:
        return column

    column.full_clean()
    column.save()

    # ADR-006: đổi công thức mà không tính lại thì bản ghi cũ giữ số cũ, bản
    # ghi mới có số mới, cùng một cột — không ai phát hiện ra cho tới lúc đối
    # chiếu báo cáo
    if phai_tinh_lai:
        resync_table(column.table)

    record(
        AuditAction.UPDATE, actor=actor, target=column,
        detail=f"Sửa cột {column.code} — " + " · ".join(da_doi), request=request,
    )
    return column


@transaction.atomic
def remove_column(column, *, actor=None, request=None):
    """Bỏ một cột khỏi bảng.

    Xoá định nghĩa cột, nhưng **không** xoá giá trị đã nhập trong JSON — dữ
    liệu người dùng gõ vào không tự biến mất (tinh thần BR-4). Cột không còn
    hiển thị, và gán lại đúng tên kỹ thuật đó thì dữ liệu cũ hiện trở lại.
    """
    bang, ma = column.table, column.code
    column.delete()
    resync_table(bang)
    record(
        AuditAction.DELETE, actor=actor, target=bang,
        detail=f"Bỏ cột {ma} khỏi bảng {bang.code}", request=request,
    )
    return bang


def _thu_tu_ke_tiep(table):
    cuoi = table.columns.order_by("-order").values_list("order", flat=True).first()
    return (cuoi or 0) + 1


def resync_table(table, *, batch=500):
    """Tính lại cột tính sẵn và cột tách cho mọi bản ghi của một bảng.

    Gọi sau khi đổi công thức hoặc đổi nhãn ý nghĩa. Lấy danh sách cột **một
    lần** rồi truyền vào từng bản ghi — để `DataRecord.save()` tự lấy thì mỗi
    dòng tốn thêm một lệnh truy vấn (quy tắc Q2).

    Không ghi nhật ký: đây là hệ quả của một thao tác đã được ghi, không phải
    thao tác của người dùng.
    """
    cot = list(table.columns.all())
    ds = DataRecord.all_objects.filter(table=table).order_by("pk")
    da_sua = 0
    for ban_ghi in ds.iterator(chunk_size=batch):
        ban_ghi.apply_computed_columns(cot)
        ban_ghi.sync_indexed_columns(cot)
        ban_ghi.save(skip_sync=True)
        da_sua += 1
    return da_sua
