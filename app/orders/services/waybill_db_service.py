"""Cấu hình có thể tái tạo của bảng động Vận đơn DB."""
from copy import deepcopy

from django.db import transaction
from django.utils import timezone

from core.audit import record
from core.constants import AuditAction
from forms_builder.models import ColumnDef, TableDef
from orders.constants import ACTIVE_WAYBILL_TABLE_CODE, WAYBILL_TABLE_CODE, ACTIVE_PAYMENT_LABELS


TABLE_CODE = "van_don_db"
TABLE_NAME = "Vận đơn DB"
COLUMN_CODES = (
    "ngay",
    "dia_chi",
    "thanh_pho",
    "bang",
    "quoc_gia",
    "zipcode",
    "so_dien_thoai",
    "san_pham",
    "so_luong",
    "gia_tien",
    "loai_tien",
    "pttt",
    "nguoi_ban",
    "phu_trach_cskh",
    "phu_trach_mkt",
    "phu_trach_vd",
    "ma_don",
    "trang_thai_vc",
    "ngay_tt",
    "ten_khach",
    "so_tien_tt",
    "bill",
    "ghi_chu",
    "trang_thai_tt",
    "pttt_thuc_te",
    "doi_soat",
)


def _column_values(source, order):
    return {
        "name": source.name,
        "field_type": source.field_type,
        "meaning": source.meaning,
        "required": source.required,
        "order": order,
        "is_key": source.is_key,
        "options": deepcopy(ACTIVE_PAYMENT_LABELS if source.code in ('pttt', 'pttt_thuc_te') else source.options),
        "highlight": source.highlight,
        "alert_op": source.alert_op,
        "alert_value": source.alert_value,
        "is_computed": source.is_computed,
        "compute_op": source.compute_op,
        "compute_left": source.compute_left,
        "compute_right": source.compute_right,
        "compute_decimals": source.compute_decimals,
    }


@transaction.atomic
def ensure_table(*, actor=None):
    """Tạo/bổ sung Vận đơn DB từ hai bảng nguồn mà không đụng dữ liệu đã nhập."""
    source_tables = {
        table.code: table
        for table in TableDef.all_objects.select_for_update().filter(
            code__in=(ACTIVE_WAYBILL_TABLE_CODE, WAYBILL_TABLE_CODE)
        )
    }
    active = source_tables[ACTIVE_WAYBILL_TABLE_CODE]
    legacy = source_tables[WAYBILL_TABLE_CODE]

    table, created = TableDef.all_objects.get_or_create(
        code=TABLE_CODE,
        defaults={
            "name": TABLE_NAME,
            "department": active.department,
            "created_by": actor,
            "description": "Bảng vận đơn độc lập theo cấu hình ngày 14.09.2026.",
            "is_shared": False,
        },
    )
    if created:
        record(
            AuditAction.CREATE,
            actor=actor,
            target=table,
            detail="Tạo Vận đơn DB từ cấu hình đã duyệt ngày 14.09.2026",
        )

    active_columns = {column.code: column for column in active.columns.all()}
    legacy_columns = {column.code: column for column in legacy.columns.all()}
    existing = {column.code: column for column in table.columns.order_by("order", "id")}

    for order, code in enumerate(COLUMN_CODES):
        if code in existing:
            continue
        source = legacy_columns[code] if code == "doi_soat" else active_columns[code]
        existing[code] = ColumnDef.objects.create(
            table=table,
            code=code,
            **_column_values(source, order),
        )

    configured = [existing[code] for code in COLUMN_CODES]
    extras = [column for code, column in existing.items() if code not in COLUMN_CODES]
    changed = []
    changed_at = timezone.now()
    for order, column in enumerate(configured + extras):
        if column.order != order:
            column.order = order
            column.updated_at = changed_at
            changed.append(column)
    if changed:
        ColumnDef.objects.bulk_update(changed, ["order", "updated_at"])

    return table
