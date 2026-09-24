"""Vận đơn theo CRM Tân: chi tiết, tổng và quyền dùng một nguồn — ADR-018."""
from orders.constants import waybill_condition
import json
import sys
from decimal import Decimal, InvalidOperation
from types import SimpleNamespace

from django.conf import settings
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
from core.identity import employee_code
from core.money import parse_money
from forms_builder import record_policies
from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, DataRecord, TableDef, Grant
from forms_builder.services import grant_service, record_service
from orders.constants import WAYBILL_TABLE_CODE, PaymentStatus, ShippingStatus, Market, LEGACY_PAYMENT_LABELS
from orders.models import Product, WaybillItem
from orders.units import resolve_unit
from . import assignment_service
from . import currency_service
from orders.constants import ACTIVE_PAYMENT_LABELS

DETAIL_CODE = "chi_tiet_sp"
PROTECTED = frozenset({"san_pham", "so_luong", "gia_tien", "so_tien_tt"})
DETAIL_CELLS = PROTECTED
COLUMNS = [
    # Ngày (lên đơn) đứng đầu theo lệnh chủ dự án 24.09.2026 — trả lại vị trí
    # của tệp thật trước ADR-036; Ngày thanh toán vẫn ở nhóm thanh toán phía sau
    ("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
    ("Mã đơn", "ma_don", FieldType.TEXT, ""),
    ("Tên khách", "ten_khach", FieldType.TEXT, Meaning.CUSTOMER),
    ("Số điện thoại", "so_dien_thoai", FieldType.TEXT, Meaning.PHONE),
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
    "quoc_gia": Market.labels, "pttt": ACTIVE_PAYMENT_LABELS,
    "pttt_thuc_te": ACTIVE_PAYMENT_LABELS, "loai_tien": Currency.values,
    "trang_thai_vc": ShippingStatus.labels, "trang_thai_tt": PaymentStatus.labels,
}


protect_table = True


def register():
    # Một bảng duy nhất (ADR-036): đăng ký theo mã `van_don` và theo workflow.
    record_policies.register(WAYBILL_TABLE_CODE, sys.modules[__name__])
    record_policies.register_workflow("waybill", sys.modules[__name__])


def upgrade_schema(table, *, actor=None, request=None):
    """Bổ sung cấu trúc chuẩn Vận đơn cho bảng đang có (ADR-034 → ADR-036): tạo cột còn
    thiếu theo `COLUMNS` (xếp cuối), đổi cột chữ tự do thành danh sách chọn khi chuẩn yêu
    cầu, thêm lựa chọn chuẩn còn thiếu, gắn nhãn ý nghĩa còn trống. Không xoá, không đổi tên
    cột, không sửa dữ liệu: giá trị cũ ngoài danh sách vẫn hiện "(giá trị cũ)" trên lưới.
    Trả về danh sách việc đã làm."""
    from forms_builder.services import table_service
    columns = {c.code: c for c in table.columns.all()}
    taken_meanings = {c.meaning for c in columns.values() if c.meaning}
    order = max((c.order for c in columns.values()), default=-1)
    done = []
    for label, code, kind, meaning in COLUMNS:
        options = list(OPTIONS.get(code) or [])
        column = columns.get(code)
        if column is None:
            order += 1
            table_service.add_column(table, actor=actor, request=request, name=label, code=code, field_type=kind,
                                     order=order, meaning=meaning if meaning not in taken_meanings else '',
                                     options=options)
            if meaning:
                taken_meanings.add(meaning)
            done.append(f'thêm cột {code}')
            continue
        if column.is_computed:
            continue                      # cột tính sẵn: không tự phá công thức
        fields = []
        if column.field_type != kind and kind == FieldType.CHOICE and column.field_type == FieldType.TEXT:
            column.field_type = FieldType.CHOICE
            fields.append('field_type')
        if column.meaning != meaning and meaning and meaning not in taken_meanings:
            column.meaning = meaning
            taken_meanings.add(meaning)
            fields.append('meaning')
        if options and not set(options).issubset(column.options or []):
            column.options = list(column.options or []) + [o for o in options if o not in (column.options or [])]
            fields.append('options')
        if fields:
            column.save(update_fields=fields + ['updated_at'])
            done.append(f'sửa cột {code}: {", ".join(fields)}')
    if done:
        record(AuditAction.UPDATE, actor=actor, target=table, request=request,
               detail='Bổ sung cấu trúc chuẩn Vận đơn: ' + '; '.join(done))
    return done


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


def _payment_label(raw):
    """Nhãn trạng thái thanh toán từ tệp: nhận nhãn cũ (`LEGACY_PAYMENT_LABELS`) và
    khác hoa thường ("Đã Thanh Toán"), trả về nhãn chuẩn; lạ thì trả nguyên để báo lỗi."""
    text = raw.strip()
    text = LEGACY_PAYMENT_LABELS.get(text, text)
    by_fold = {label.casefold(): label for label in PaymentStatus.labels}
    return by_fold.get(text.casefold(), text)


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
    # ADR-036 (chủ dự án chốt 18.09): dòng không có Chi tiết sản phẩm vẫn tạo được — nhập
    # tệp cũ, thêm dòng tay. Có chi tiết thì tổng phải khớp như cũ; Thống kê đếm dòng không
    # chi tiết là "đơn thiếu chi tiết".
    raw_items = values.get(DETAIL_CODE)
    has_items = raw_items not in (None, '', [])
    items = validate_items(raw_items) if has_items else []
    computed = totals(items) if has_items else {}
    if 'trang_thai_tt' in values:
        status = values['trang_thai_tt']
        if isinstance(status, str):
            status = _payment_label(status)   # tệp cũ: "Chờ thanh toán", "Đã Thanh Toán"…
        if status not in ('', None, *PaymentStatus.labels):
            raise BusinessError('Trạng thái thanh toán không hợp lệ.')
        computed['trang_thai_tt'] = status
    for code in ("so_luong", "gia_tien", "so_tien_tt"):
        if values.get(code) in (None, ""):
            continue
        if has_items and money(values[code]) != Decimal(str(computed[code])):
            raise BusinessError("Tổng số lượng hoặc tiền không khớp chi tiết sản phẩm. Hãy sửa tệp trước khi nhập.")
        if not has_items and code != "so_luong":
            money(values[code])   # vẫn kiểm định dạng tiền
    currency = currency_service.for_label(values.get('quoc_gia'), allow_empty=True)
    if currency and values.get('loai_tien') not in (None, '', currency):
        raise BusinessError('Loại tiền phải theo quốc gia; sửa tệp trước khi nhập, không tự quy đổi.')
    if not currency:
        # Quốc gia trống (tệp cũ, dòng tay): giữ loại tiền tự khai nếu hợp lệ, không thì trống.
        currency = values.get('loai_tien') if values.get('loai_tien') in Currency.values else ''

    result = {**values, **computed, "_items": items, 'loai_tien': currency}
    result.setdefault("trang_thai_vc", ShippingStatus.DA_LEN_DON.label)
    return result


def after_create(row, values):
    items = values.get("_items") or []
    for item in items:
        item.record = row
    if items:
        WaybillItem.objects.bulk_create(items)


def assert_editable(code):
    if code == 'loai_tien':
        raise BusinessError('Loại tiền tự theo quốc gia, không sửa độc lập.')
    if code in assignment_service.COLUMNS:
        raise BusinessError('Cột này chỉ được sửa bằng hộp Phân công.')
    if code in PROTECTED:
        raise BusinessError("Bill sửa tại Chứng từ thanh toán; các tổng sửa tại Chi tiết sản phẩm.")


def choice_source(column):
    from forms_builder.choice_registry import ChoiceList
    if column.code in ('pttt', 'pttt_thuc_te'):
        return ChoiceList(options=lambda: list(ACTIVE_PAYMENT_LABELS))
    return None


def derived_values(row, column, value, *, confirmations=None):
    return currency_service.change(row, value, confirmations) if column.code == 'quoc_gia' else {}


def derived_grid_cells(changes, confirmations):
    """Kiểm cả lô trước ghi, gom một lần xác nhận cho dán nhiều quốc gia."""
    missing, derived = {}, []
    for row, code, raw in changes:
        if code != 'quoc_gia' or raw == row.data.get(code):
            continue
        # Cùng chuẩn hóa nhãn với record_service, không đoán quốc gia từ chuỗi.
        label = next((m.label for m in Market if m.label.casefold() == str(raw).strip().casefold()), raw)
        try:
            values = currency_service.change(row, label, confirmations)
        except currency_service.CurrencyConfirmation as exc:
            missing.update(exc.currency_confirmations)
            continue
        for field, value in values.items():
            if value != row.data.get(field):
                derived.append({'id': row.pk, 'column': field, 'old': row.data.get(field), 'value': value})
    if missing:
        raise currency_service.CurrencyConfirmation(missing)
    return derived


def assert_column_change(column, changes=None):
    if column.code not in {c[1] for c in COLUMNS}:
        return
    structural = {"code", "field_type", "meaning", "is_computed", "required", "is_key", "options"}
    if changes is None or any(k in changes and changes[k] != getattr(column, k) for k in structural):
        raise BusinessError("Cột chuẩn của Vận đơn được giữ để lên đơn và thống kê đúng. Có thể đổi nhãn, màu, độ rộng.")


def extra_columns(table):
    # ADR-036: chi tiết sản phẩm không bắt buộc khi nhập tệp; có thì kiểm tổng khớp.
    return [SimpleNamespace(name="Chi tiết sản phẩm (JSON)", code=DETAIL_CODE,
                            field_type=FieldType.LONG_TEXT, required=False, is_computed=False)] + [
        SimpleNamespace(name=name, code=code, field_type=FieldType.TEXT, required=False, is_computed=True)
        for code, name in [('ma_sale', 'Mã Sale tạo đơn'), ('ma_vd', 'Mã nhân viên Vận đơn'),
                           ('ma_cskh', 'Mã nhân viên CSKH'), ('ma_mkt', 'Mã nhân viên Marketing')]]


def export_queryset(queryset):
    from django.db.models import Prefetch
    prefetches = [Prefetch("waybill_items",
        queryset=WaybillItem.objects.filter(deleted_at__isnull=True).select_related("product"),
        to_attr="export_items")]
    if getattr(settings, 'PAYMENT_DOCUMENTS_ENABLED', False):
        from orders.models import PaymentDocument
        from .payment_service import ordered
        prefetches.append(Prefetch('payment_documents',
            queryset=ordered(PaymentDocument.objects.filter(deleted_at__isnull=True)),
            to_attr='export_payments'))
    return assignment_service.related(queryset).prefetch_related(*prefetches)


def export_detail(row):
    return json.dumps([{"product": i.product.code, "quantity": i.quantity, "unit": i.unit,
                        "unit_price": str(i.unit_price), "paid_amount": str(i.paid_amount)}
                       for i in row.export_items], ensure_ascii=False)


def export_values(row):
    order = getattr(row, 'order', None)
    assignment = getattr(row, 'assignment', None)
    return [export_detail(row), employee_code(order.seller) if order and order.seller_id else ''] + [
        employee_code(getattr(assignment, field)) if assignment and getattr(assignment, field + '_id') else ''
        for field in assignment_service.FIELDS]


def row_for(user, pk, *, lock=False):
    rows = DataRecord.objects.filter(waybill_condition()).select_related("table")
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
    computed = totals(items)
    computed.pop('trang_thai_tt')
    row.data.update(computed)
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


def grid_column(column):
    """Khả năng hiển thị của bảng vận đơn (một bảng duy nhất, ADR-036)."""
    payment_documents = getattr(settings, 'PAYMENT_DOCUMENTS_ENABLED', False)
    is_bill = column.code == 'bill'
    return {'detail':column.code in DETAIL_CELLS, 'assignment':column.code in assignment_service.COLUMNS,
        'protected':column.is_computed or column.code in PROTECTED or column.code == 'loai_tien' or column.code in assignment_service.COLUMNS
            or (is_bill and payment_documents),
        'renderer':'bill' if is_bill and payment_documents else ('url' if is_bill else 'value'),
        'frozen':column.code in ('ngay', 'ma_don', 'ten_khach', 'so_dien_thoai')}


def grid_value(row, column):
    return assignment_service.display(row, column.code) if column.code in assignment_service.COLUMNS else row.data.get(column.code)


def grid_extras(rows, columns):
    from django.urls import reverse
    if not getattr(settings, 'PAYMENT_DOCUMENTS_ENABLED', False):
        return {row.pk: {'detail_url': reverse('waybill_detail', args=[row.pk])} for row in rows}
    from .payment_service import metadata
    bills = metadata([row.pk for row in rows]) if rows and any(c.code == 'bill' for c in columns) else {}
    return {row.pk:{'detail_url':reverse('waybill_detail', args=[row.pk]),
        'cells':{'bill':{'payments':bills.get(row.pk, {'count':0, 'links':[]})}}} for row in rows}
