"""Vận đơn theo CRM Tân: chi tiết, tổng và quyền dùng một nguồn — ADR-018."""
import json
import sys
from decimal import Decimal, InvalidOperation
from types import SimpleNamespace

from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.db.models import (
    Count, Sum, F, Value, TextField, DecimalField, ExpressionWrapper,
    Exists, OuterRef,
)
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import NullIf
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
from orders.units import resolve_unit
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


def validate_items(raw, *, previous=None, strict_units=False):
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
    for index, d in enumerate(raw):
        product = products.get(d["product"])
        if product is None:
            raise BusinessError("Mã sản phẩm trong chi tiết không có trong danh mục.")
        try:
            qty = Decimal(str(d.get("quantity", "")))
            if not qty.is_finite() or qty <= 0 or qty != qty.to_integral_value():
                raise ValueError
            prior = previous[index] if previous and index < len(previous) else None
            old_unit = prior.unit if prior and prior.product_id == product.pk else None
            if old_unit is None and previous and "unit" not in d:
                known = {item.unit for item in previous if item.product_id == product.pk}
                if len(known) > 1:
                    raise BusinessError("Mở lại chi tiết và chọn đơn vị cho sản phẩm bị đổi vị trí.")
                old_unit = next(iter(known), None)
            item = WaybillItem(product=product, quantity=int(qty),
                               unit=resolve_unit(product, d.get("unit"), previous=old_unit, allow_custom=not strict_units),
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
    return json.dumps([{"product": i.product.code, "quantity": i.quantity, "unit": i.unit,
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
    previous = list(WaybillItem.objects.filter(record=row, deleted_at__isnull=True))
    items = validate_items(raw, previous=previous)
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


def statistics_totals(records):
    """Tổng theo tiền tệ từ cả dòng cha, nên đơn thiếu chi tiết vẫn giữ nhóm."""
    return statistics_breakdown(records)[0]


def statistics_breakdown(records, record_counts=None):
    """Tính tổng tiền tệ và sản phẩm trong cùng một lần quét chi tiết.

    Đây là công thức dùng chung cho Bàn điều hành và lớp tương thích thống kê;
    mặt hàng đã xoá mềm không đóng góp vào số lượng hoặc tiền.
    """
    value = ExpressionWrapper(
        F("quantity") * F("unit_price"),
        output_field=DecimalField(max_digits=24, decimal_places=2),
    )
    if record_counts is None:
        record_counts = {
            row["currency"]: row["orders"]
            for row in (
                records.annotate(currency=NullIf(
                    KeyTextTransform("loai_tien", "data"),
                    Value("", output_field=TextField()),
                ))
                .order_by()
                .values("currency")
                .annotate(orders=Count("id"))
            )
        }
    item_rows = list(
        WaybillItem.objects.for_records(records)
        .annotate(currency=KeyTextTransform("loai_tien", "record__data"))
        .order_by()
        .values("currency", "product__name")
        .annotate(
            quantity_total=Sum("quantity"),
            value=Sum(value),
            paid=Sum("paid_amount"),
        )
    )
    money = {}
    products = {}
    for row in item_rows:
        currency = row["currency"] or None
        total = money.setdefault(currency, {
            "quantity_total": 0, "value": Decimal(0), "paid": Decimal(0),
        })
        total["quantity_total"] += row["quantity_total"] or 0
        total["value"] += row["value"] or Decimal(0)
        total["paid"] += row["paid"] or Decimal(0)
        product = row["product__name"] or "Chưa có sản phẩm"
        products[product] = products.get(product, 0) + (row["quantity_total"] or 0)
    totals = [
        {
            "record__data__loai_tien": currency,
            "orders": orders,
            "quantity_total": money.get(currency, {}).get("quantity_total", 0),
            "value": money.get(currency, {}).get("value", Decimal(0)),
            "paid": money.get(currency, {}).get("paid", Decimal(0)),
        }
        for currency, orders in sorted(
            record_counts.items(), key=lambda item: (item[0] is not None, item[0] or ""),
        )
    ]
    product_rows = [
        {"label": label, "value": quantity}
        for label, quantity in sorted(
            products.items(), key=lambda item: (-item[1], item[0]),
        )
    ]
    return totals, product_rows


def executive_snapshot(records, granularity, max_groups=2_000):
    """Gom các chiều điều hành và chi tiết tiền hàng trong một lần đọc phạm vi.

    Queryset ``records`` đã mang đủ điều kiện quyền/bộ lọc. CTE chỉ giữ các cột
    cần cho thống kê, nên PostgreSQL không phải đọc lại JSON và dòng cha cho từng
    biểu đồ; mọi nhóm vẫn bị chặn trước khi trả về Python.
    """
    scoped = records.order_by().values("id", "val_date", "data")
    scoped_sql, scoped_params = scoped.query.sql_with_params()
    bucket = {
        "day": "val_date",
        "week": "date_trunc('week', val_date)::date",
        "month": "date_trunc('month', val_date)::date",
    }[granularity]
    sql = f"""
        WITH scoped AS MATERIALIZED (
            SELECT id, val_date,
                   NULLIF(data->>'trang_thai_vc', '') AS delivery,
                   NULLIF(data->>'trang_thai_tt', '') AS payment,
                   NULLIF(data->>'quoc_gia', '') AS market,
                   NULLIF(data->>'loai_tien', '') AS currency
            FROM ({scoped_sql}) source
        ), record_groups AS (
            SELECT CASE
                     WHEN GROUPING({bucket}) = 0 THEN 'period'
                     WHEN GROUPING(delivery) = 0 THEN 'delivery'
                     WHEN GROUPING(payment) = 0 THEN 'payment'
                     WHEN GROUPING(market) = 0 THEN 'market'
                     ELSE 'record_currency'
                   END AS kind,
                   CASE
                     WHEN GROUPING({bucket}) = 0 THEN to_char({bucket}, 'YYYY-MM-DD')
                     WHEN GROUPING(delivery) = 0 THEN COALESCE(delivery, '')
                     WHEN GROUPING(payment) = 0 THEN COALESCE(payment, '')
                     WHEN GROUPING(market) = 0 THEN COALESCE(market, '')
                     ELSE COALESCE(currency, '')
                   END AS label,
                   COUNT(*)::numeric AS metric_value,
                   0::bigint AS orders_with_items,
                   0::numeric AS quantity_total,
                   0::numeric AS money_value,
                   0::numeric AS paid_value,
                   NULL::bigint AS product_id
            FROM scoped
            GROUP BY GROUPING SETS (
                ({bucket}), (delivery), (payment), (market), (currency)
            )
        ), item_groups AS (
            SELECT CASE WHEN GROUPING(s.currency) = 0
                        THEN 'item_currency' ELSE 'product' END AS kind,
                   CASE WHEN GROUPING(s.currency) = 0
                        THEN COALESCE(s.currency, '')
                        ELSE i.product_id::text END AS label,
                   0::numeric AS metric_value,
                   0::bigint AS orders_with_items,
                   COALESCE(SUM(i.quantity), 0)::numeric AS quantity_total,
                   COALESCE(SUM(i.quantity * i.unit_price), 0)::numeric AS money_value,
                   COALESCE(SUM(i.paid_amount), 0)::numeric AS paid_value,
                   CASE WHEN GROUPING(s.currency) = 0
                        THEN NULL ELSE i.product_id END AS product_id
            FROM scoped s
            JOIN orders_waybillitem i
              ON i.record_id = s.id AND i.deleted_at IS NULL
            GROUP BY GROUPING SETS ((s.currency), (i.product_id))
        ), all_groups AS (
            SELECT * FROM record_groups
            UNION ALL
            SELECT * FROM item_groups
        ), ranked AS (
            SELECT *, ROW_NUMBER() OVER (
                PARTITION BY kind
                ORDER BY CASE WHEN kind = 'product' THEN quantity_total
                              ELSE metric_value END DESC, label
            ) AS position
            FROM all_groups
        )
        SELECT ranked.kind,
               CASE WHEN ranked.kind = 'product'
                    THEN COALESCE(product.name, '') ELSE ranked.label END AS label,
               metric_value, orders_with_items,
               quantity_total, money_value, paid_value
        FROM ranked
        LEFT JOIN orders_product product ON product.id = ranked.product_id
        WHERE position <= {int(max_groups)}
    """
    with transaction.atomic(), connection.cursor() as cursor:
        # CTE có trần bộ nhớ cố định: đủ giữ các chiều của 300k dòng, không đổi
        # work_mem toàn hệ thống và tự hoàn nguyên ngay sau snapshot.
        cursor.execute("SET LOCAL work_mem = '64MB'")
        cursor.execute("SET LOCAL jit = off")
        cursor.execute(sql, scoped_params)
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def missing_item_count(records):
    """Đếm dòng cha chưa có chi tiết bằng EXISTS trên chỉ mục record_id."""
    active_item = WaybillItem.objects.filter(
        record_id=OuterRef("pk"), deleted_at__isnull=True,
    )
    return records.annotate(
        _has_waybill_item=Exists(active_item),
    ).filter(_has_waybill_item=False).count()
