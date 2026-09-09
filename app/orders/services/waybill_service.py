"""Vận đơn theo CRM Tân: chi tiết, tổng và quyền dùng một nguồn — ADR-018."""
import json
import sys
from decimal import Decimal, InvalidOperation
from types import SimpleNamespace

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Sum, F, DecimalField, ExpressionWrapper
from django.utils import timezone

from core.audit import record
from core.constants import AuditAction, Currency
from core.exceptions import BusinessError, OutOfScopeError
from core.money import parse_money
from forms_builder import record_policies
from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, DataRecord, TableDef, Grant
from forms_builder.services import grant_service, record_service
from orders.constants import ACTIVE_WAYBILL_TABLE_CODE, PaymentMethod, PaymentStatus, ShippingStatus, Market
from orders.models import Product, WaybillItem
from . import assignment_service

DETAIL_CODE = "chi_tiet_sp"
PROTECTED = frozenset({"san_pham", "so_luong", "gia_tien", "so_tien_tt", "trang_thai_tt"})
DETAIL_CELLS = PROTECTED - {"trang_thai_tt"}
COLUMNS = [
    ("Mã đơn", "ma_don", FieldType.TEXT, ""),
    ("Tên khách", "ten_khach", FieldType.TEXT, Meaning.CUSTOMER),
    ("Số điện thoại", "so_dien_thoai", FieldType.TEXT, Meaning.PHONE),
    ("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
    ("Sản phẩm", "san_pham", FieldType.TEXT, Meaning.PRODUCT),
    ("Quốc gia", "quoc_gia", FieldType.CHOICE, ""),
    ("Bang", "bang", FieldType.TEXT, ""),
    ("Thành phố", "thanh_pho", FieldType.TEXT, ""),
    ("Zipcode", "zipcode", FieldType.TEXT, ""),
    ("Chi tiết số nhà, đường", "dia_chi", FieldType.TEXT, ""),
    ("Số lượng sản phẩm", "so_luong", FieldType.INTEGER, ""),
    ("Giá tiền", "gia_tien", FieldType.MONEY, Meaning.REVENUE),
    ("Loại tiền", "loai_tien", FieldType.CHOICE, ""),
    ("PTTT lên đơn", "pttt", FieldType.CHOICE, ""),
    ("SALE/CSKH", "nguoi_ban", FieldType.TEXT, Meaning.SELLER),
    ("Trạng thái vận chuyển", "trang_thai_vc", FieldType.CHOICE, Meaning.STATUS),
    ("Ngày thanh toán", "ngay_tt", FieldType.DATE, ""),
    ("Trạng thái thanh toán", "trang_thai_tt", FieldType.CHOICE, ""),
    ("Số tiền thanh toán", "so_tien_tt", FieldType.MONEY, ""),
    ("Bill", "bill", FieldType.TEXT, ""),
    ("PTTT thực tế", "pttt_thuc_te", FieldType.CHOICE, ""),
    ("Ghi chú", "ghi_chu", FieldType.LONG_TEXT, ""),
    ("Phụ trách Vận đơn", "phu_trach_vd", FieldType.TEXT, ""),
    ("Phụ trách CSKH", "phu_trach_cskh", FieldType.TEXT, ""),
    ("Phụ trách Marketing", "phu_trach_mkt", FieldType.TEXT, ""),
]
REQUIRED = {"ma_don", "ten_khach", "so_dien_thoai", "ngay", "loai_tien"}
OPTIONS = {
    "quoc_gia": Market.labels, "pttt": PaymentMethod.labels,
    "pttt_thuc_te": PaymentMethod.labels, "loai_tien": Currency.values,
    "trang_thai_vc": ShippingStatus.labels, "trang_thai_tt": PaymentStatus.labels,
}


def register():
    record_policies.register(ACTIVE_WAYBILL_TABLE_CODE, sys.modules[__name__])


@transaction.atomic
def ensure_table(legacy, *, actor=None):
    # Khoá cùng một bảng cũ để hai dịch vụ khởi động không sao chép quyền hai lần.
    legacy = TableDef.all_objects.select_for_update().get(pk=legacy.pk)
    table, created = TableDef.all_objects.get_or_create(
        code=ACTIVE_WAYBILL_TABLE_CODE,
        defaults={"name": "Vận đơn", "department": legacy.department,
                  "folder": legacy.folder, "is_shared": True, "created_by": actor,
                  "description": "Theo CRM Tân: lên đơn, vận hành và thống kê."},
    )
    if created:
        Grant.objects.bulk_create([
            Grant(table=table, user_id=g.user_id, team_id=g.team_id,
                  action=g.action, granted_by_id=g.granted_by_id)
            for g in legacy.grants.filter(deleted_at__isnull=True)
        ])
        record(AuditAction.CREATE, actor=actor, target=table,
               detail="Tạo bảng vận đơn mới theo ADR-018")
    if legacy.name != "Vận đơn cũ":
        legacy.name = "Vận đơn cũ"
        legacy.save(update_fields=["name", "updated_at"])
        record(AuditAction.UPDATE, actor=actor, target=legacy, detail="Đổi tên thành Vận đơn cũ")
    existing = set(table.columns.values_list("code", flat=True))
    for order, (name, code, kind, meaning) in enumerate(COLUMNS):
        if code not in existing:
            ColumnDef.objects.create(table=table, name=name, code=code, field_type=kind,
                                     meaning=meaning, order=order, required=code in REQUIRED,
                                     is_key=code == "ma_don", options=OPTIONS.get(code, []))
    return table


def money(value):
    try:
        amount = parse_money(value) if isinstance(value, str) else Decimal(str(value))
        if amount is None or not amount.is_finite() or amount < 0 or amount != amount.quantize(Decimal("0.01")):
            raise ValueError
        return amount
    except (ValueError, TypeError, InvalidOperation):
        raise BusinessError("Số tiền phải không âm và có tối đa hai chữ số thập phân.")


def validate_items(raw):
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (ValueError, TypeError):
            raise BusinessError("Chi tiết sản phẩm phải là danh sách JSON từ tệp xuất của bảng này.")
    if not isinstance(raw, list) or not raw or len(raw) > 200:
        raise BusinessError("Cần từ 1 đến 200 dòng chi tiết sản phẩm; không thể suy ra từ tổng tiền hoặc tên gộp.")
    codes = [d.get("product") for d in raw if isinstance(d, dict)]
    if len(codes) != len(raw) or any(not isinstance(c, str) for c in codes):
        raise BusinessError("Mỗi dòng chi tiết phải có mã sản phẩm.")
    products = {p.code: p for p in Product.objects.filter(code__in=codes)}
    result = []
    for d in raw:
        product = products.get(d["product"])
        if product is None:
            raise BusinessError("Mã sản phẩm trong chi tiết không có trong danh mục.")
        try:
            qty = Decimal(str(d.get("quantity", "")))
            if not qty.is_finite() or qty <= 0 or qty != qty.to_integral_value():
                raise ValueError
            item = WaybillItem(product=product, quantity=int(qty),
                               unit_price=money(d.get("unit_price")), paid_amount=money(d.get("paid_amount", 0)))
            item.full_clean(exclude=["record"])
        except (ValueError, TypeError, InvalidOperation, ValidationError):
            raise BusinessError("Kiểm tra số lượng nguyên dương và số tiền hợp lệ của từng sản phẩm.")
        result.append(item)
    return result


def totals(items):
    price = sum((i.quantity * i.unit_price for i in items), Decimal(0))
    paid = sum((i.paid_amount for i in items), Decimal(0))
    if price >= Decimal("10000000000000000") or paid >= Decimal("10000000000000000"):
        raise BusinessError("Tổng tiền vượt giới hạn 16 chữ số phần nguyên.")
    status = PaymentStatus.UNPAID if paid == 0 else PaymentStatus.PARTIAL if paid < price else PaymentStatus.PAID
    return {"san_pham": " + ".join(f"{i.product.name} ×{i.quantity}" for i in items),
            "so_luong": sum(i.quantity for i in items), "gia_tien": str(price),
            "so_tien_tt": str(paid), "trang_thai_tt": status.label}


def prepare_values(values):
    if any(values.get(code) not in (None, '') for code in assignment_service.COLUMNS):
        raise BusinessError('Không nhập phân công qua tệp hoặc ô. Dùng hộp Phân công sau khi nhập.')
    items = validate_items(values.get(DETAIL_CODE))
    computed = totals(items)
    for code in ("so_luong", "gia_tien", "so_tien_tt"):
        if values.get(code) not in (None, "") and money(values[code]) != Decimal(str(computed[code])):
            raise BusinessError("Tổng số lượng hoặc tiền không khớp chi tiết sản phẩm. Hãy sửa tệp trước khi nhập.")
    result = {**values, **computed, "_items": items}
    result.setdefault("trang_thai_vc", ShippingStatus.DA_LEN_DON.label)
    return result


def after_create(row, values):
    for item in values["_items"]:
        item.record = row
    WaybillItem.objects.bulk_create(values["_items"])


def assert_editable(code):
    if code in assignment_service.COLUMNS:
        raise BusinessError('Cột này chỉ được sửa bằng hộp Phân công.')
    if code in PROTECTED:
        raise BusinessError("Sửa trong Chi tiết sản phẩm; tổng và trạng thái thanh toán được tính tự động.")


def assert_column_change(column, changes=None):
    if column.code not in {c[1] for c in COLUMNS}:
        return
    structural = {"code", "field_type", "meaning", "is_computed", "required", "is_key", "options"}
    if changes is None or any(k in changes and changes[k] != getattr(column, k) for k in structural):
        raise BusinessError("Cột chuẩn của Vận đơn được giữ để lên đơn và thống kê đúng. Có thể đổi nhãn, màu, độ rộng.")


def extra_columns(table):
    return [SimpleNamespace(name="Chi tiết sản phẩm (JSON)", code=DETAIL_CODE,
                            field_type=FieldType.LONG_TEXT, required=True, is_computed=False)] + [
        SimpleNamespace(name=name, code=code, field_type=FieldType.TEXT, required=False, is_computed=True)
        for code, name in [('ma_sale', 'Mã Sale tạo đơn'), ('ma_vd', 'Mã nhân viên Vận đơn'),
                           ('ma_cskh', 'Mã nhân viên CSKH'), ('ma_mkt', 'Mã nhân viên Marketing')]]


def export_queryset(queryset):
    from django.db.models import Prefetch
    return assignment_service.related(queryset).prefetch_related(Prefetch("waybill_items",
        queryset=WaybillItem.objects.filter(deleted_at__isnull=True).select_related("product"),
        to_attr="export_items"))


def export_detail(row):
    return json.dumps([{"product": i.product.code, "quantity": i.quantity,
                        "unit_price": str(i.unit_price), "paid_amount": str(i.paid_amount)}
                       for i in row.export_items], ensure_ascii=False)


def export_values(row):
    order = getattr(row, 'order', None)
    assignment = getattr(row, 'assignment', None)
    return [export_detail(row), order.seller.username if order and order.seller_id else ''] + [
        getattr(assignment, field).username if assignment and getattr(assignment, field + '_id') else ''
        for field in assignment_service.FIELDS]


def row_for(user, pk, *, lock=False):
    rows = DataRecord.objects.filter(table__code=ACTIVE_WAYBILL_TABLE_CODE).select_related("table")
    if lock:
        rows = rows.select_for_update(of=("self",))
    else:
        rows = rows.in_scope(user)
    row = rows.filter(pk=pk).first()
    if row is None or (lock and not DataRecord.objects.in_scope(user).filter(pk=pk).exists()):
        raise OutOfScopeError("Bạn không có quyền xem vận đơn này.")
    return row


def refresh_for_update(row, user, *, include_deleted=False):
    if include_deleted:
        fresh = DataRecord.all_objects.select_for_update().get(pk=row.pk)
    else:
        fresh = row_for(user, row.pk, lock=True)
    if not grant_service.can_edit_record(user, fresh):
        raise OutOfScopeError("Bạn không có quyền sửa vận đơn này.")
    row.data, row.style, row.updated_at = fresh.data, fresh.style, fresh.updated_at
    row.deleted_at, row.deleted_by_id = fresh.deleted_at, fresh.deleted_by_id


def items_for(user, pk):
    row = row_for(user, pk)
    return row, list(WaybillItem.objects.in_scope(user).filter(record=row).select_related("product"))


@transaction.atomic
def update_items(user, pk, raw, version, *, request=None):
    row = row_for(user, pk, lock=True)
    if not grant_service.can_edit_record(user, row):
        raise OutOfScopeError("Bạn không có quyền sửa vận đơn này.")
    if version != row.updated_at.isoformat():
        raise BusinessError("Vận đơn vừa được người khác sửa. Đóng rồi mở lại chi tiết để lấy dữ liệu mới.")
    items = validate_items(raw)
    WaybillItem.objects.in_scope(user).filter(record=row).update(deleted_at=timezone.now(), deleted_by=user)
    after_create(row, {"_items": items})
    row.data.update(totals(items))
    row.save()
    record(AuditAction.UPDATE, actor=user, target=row,
           detail=f"Sửa {len(items)} dòng chi tiết sản phẩm và thanh toán vận đơn", request=request)
    return row


def statistics(records, group="total"):
    # records đã lọc theo phạm vi và các bộ lọc của lưới; không nạp cả bảng.
    items = WaybillItem.objects.for_records(records)
    value = ExpressionWrapper(F("quantity") * F("unit_price"), output_field=DecimalField(max_digits=24, decimal_places=2))
    fields = {"seller": "record__data__nguoi_ban", "market": "record__data__quoc_gia",
              "product": "product__code"}
    grouping = ["record__data__loai_tien"]
    if group in fields:
        grouping.insert(0, fields[group])
    if group == "product":
        grouping.append("product__name")
    return items.order_by().values(*grouping).annotate(
        orders=Count("record_id", distinct=True), quantity_total=Sum("quantity"),
        value=Sum(value), paid=Sum("paid_amount"),
    ).order_by(*grouping), grouping
