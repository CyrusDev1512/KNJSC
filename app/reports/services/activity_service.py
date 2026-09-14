"""Báo cáo ERP: nguồn tường minh, quyền chuẩn, dữ liệu và trình bày tách biệt."""
from dataclasses import dataclass, replace

from django.db.models import Count, Sum, F, Value, CharField, Q
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Coalesce, NullIf, Concat

from core.managers import apply_scope
from core.exceptions import OutOfScopeError, BusinessError
from forms_builder.models import DataRecord, TableDef
from orders.models import WaybillItem
from reports.models import ReportSource
from reports import aggregations
from reports.marketing import Metric, with_totals

GROUPS = (
    ("day", "Tổng hợp"), ("person", "Theo nhân viên"),
    ("product", "Theo sản phẩm"), ("market", "Theo thị trường"),
    ("department", "Hiệu suất theo phòng ban"),
)
PERSON_LABELS = {"sale": "Sale", "mkt": "Marketer", "delivery": "Người phụ trách Vận đơn"}
INPUT_LABELS = {
    "mess": "Số Mess", "orders": "Số đơn", "sales": "Doanh số",
    "revenue": "Doanh thu", "cost": "CPQC", "invoice": "Hóa đơn",
}
FORMULAS = {
    "conversion": ("Tỉ lệ chốt", ("orders", "mess"), "divide"),
    "cpo": ("CPO", ("cost", "orders"), "divide"),
    "mess_cost": ("Giá Mess", ("cost", "mess"), "divide"),
    "cost_sales": ("CPQC/Doanh số", ("cost", "sales"), "divide"),
    # BC MKT M5 = K5/J5; không suy ra phép chia hai trường cùng tên.
    "invoice_revenue": ("Hóa đơn/Doanh thu", ("cost", "mess", "orders"), "k_over_j"),
    "aov": ("AOV", ("sales", "orders"), "divide"),
}
DISPLAY_ORDER = {
    "sale": ("mess", "orders", "sales", "conversion", "revenue"),
    "mkt": ("mess", "cost", "orders", "sales", "revenue", "invoice",
            "cpo", "mess_cost", "cost_sales", "invoice_revenue", "aov"),
}


@dataclass(frozen=True)
class DeliveryResult(aggregations.SummaryResult):
    """Trạng thái là phần bổ sung của cùng kết quả đã lọc quyền."""
    shipping: tuple = ()


def status_expression():
    return Coalesce(NullIf(KeyTextTransform("trang_thai_vc", "data"), Value("")),
                    Value("Chưa xác định"), output_field=CharField())


def sources(user):
    return (ReportSource.objects
            .filter(table__in=TableDef.objects.in_scope(user), table__is_active=True)
            .select_related("table", "table__department")
            .prefetch_related("table__columns").order_by("table__name", "pk"))


def select_source(user, code, choices=None):
    choices = list(sources(user)) if choices is None else choices
    if not code:
        return choices[0] if choices else None
    result = next((s for s in choices if s.table.code == code), None)
    if result is None:
        raise OutOfScopeError("Nguồn báo cáo không thuộc phạm vi của bạn.")
    return result


def records(user, source):
    # Quyền báo cáo không dùng ngoại lệ cấp quyền sửa lưới/phân công CRM.
    qs = DataRecord.objects.filter(table=source.table)
    if source.kind == "delivery":
        return apply_scope(qs, user, owner="assignment__delivery_id",
                           team="assignment__delivery__profile__team_id",
                           department="department_id")
    return apply_scope(qs, user, owner="created_by_id", team="team_id",
                       department="department_id")


def group_expression(source, group):
    if group == "person":
        prefix = "assignment__delivery" if source.kind == "delivery" else "created_by"
        identity = Concat(F(prefix + "__username"), Value(" — "),
                          F(prefix + "__profile__full_name"))
        return (Coalesce(NullIf(identity, Value(" — ")), Value("Chưa phân công")),
                PERSON_LABELS[source.kind])
    if group == "department":
        return F("department__name"), "Phòng ban"
    if group == "market":
        return (Coalesce(NullIf(KeyTextTransform(source.columns["market"], "data"), Value("")),
                         Value("Chưa xác định"), output_field=CharField()), "Thị trường")
    if group == "product":
        return F("val_product"), "Sản phẩm"
    return None, "Ngày"


def project_metrics(result, source):
    """Tên, thứ tự và công thức BC SALE/BC MKT dùng chung cho mọi cách xem."""
    summed = {c.code: c for c in result.columns if c.kind == "sum"}
    columns, computed = [], []
    for key in DISPLAY_ORDER[source.kind]:
        if key in FORMULAS:
            label, inputs, kind = FORMULAS[key]
            columns.append(aggregations.ReportColumn(key, label, "computed", 4))
            codes = tuple(source.columns.get(k, "__missing_" + k) for k in inputs)
            computed.append(Metric(key, codes, kind))
        else:
            code = source.columns.get(key, "__missing_" + key)
            label = INPUT_LABELS[key]
            if code in summed:
                columns.append(replace(summed[code], label=label))
            else:
                columns.append(aggregations.ReportColumn(code, label, "computed", 2))
                computed.append(Metric(code, (), "missing"))
    result = replace(result, columns=tuple(columns), computed_columns=tuple(computed))
    return with_totals(result, result.totals)


def filtered_records(user, source, *, start=None, end=None, product="", market=""):
    """Bộ lọc duy nhất cho bảng, trạng thái, Tổng quan và tệp xuất."""
    if start and end and start > end:
        raise BusinessError("Từ ngày phải trước hoặc bằng Đến ngày.")
    qs = records(user, source)
    if start:
        qs = qs.filter(val_date__gte=start)
    if end:
        qs = qs.filter(val_date__lte=end)
    if market:
        code = source.columns["market"]
        qs = qs.annotate(_market=KeyTextTransform(code, "data"))
        if market == "__missing__":
            qs = qs.filter(Q(_market__isnull=True) | Q(_market=""))
        else:
            qs = qs.filter(_market=market)
    if product:
        if source.kind == "delivery":
            items = WaybillItem.objects.for_records(qs).filter(product__code=product)
            qs = qs.filter(pk__in=items.values("record_id"))
        else:
            qs = qs.filter(val_product=product)
    return qs


def build(user, source, *, group="day", start=None, end=None, product="", market=""):
    if group not in dict(GROUPS):
        raise BusinessError("Cách nhóm không hợp lệ.")
    qs = filtered_records(user, source, start=start, end=end, product=product, market=market)
    if source.kind == "delivery":
        return delivery(qs, source, group, product)
    expression, label = group_expression(source, group)
    result = aggregations.summarize(
        source.table, qs, group_key="ngay" if group == "day" else "nhan-vien",
        columns=list(source.table.columns.all()),
        group_expression=expression, group_label=label,
    )
    return project_metrics(result, source) if result.ok else result


def delivery(qs, source, group, product):
    items = WaybillItem.objects.for_records(qs)
    if product:
        items = items.filter(product__code=product)
    item_filter = Q(waybill_items__deleted_at__isnull=True)
    if product:
        item_filter &= Q(waybill_items__product__code=product)
    quantity = Sum("waybill_items__quantity", filter=item_filter)
    # Mỗi đơn thuộc đúng một trạng thái; tổng các nhóm này chính là tổng
    # trong bộ lọc. Tái sử dụng cho màn hình/Excel, tránh một lượt SUM riêng.
    shipping = tuple(qs.order_by().values(label=status_expression())
                     .annotate(count=Count("pk", distinct=True), quantity=quantity).order_by("label"))
    count = sum(row["count"] for row in shipping)
    quantities = [row["quantity"] for row in shipping if row["quantity"] is not None]
    totals = {"so_dong": count, "c_orders": count,
              "c_quantity": sum(quantities) if quantities else None}
    columns = (aggregations.ReportColumn("orders", "Số đơn", "sum"),
               aggregations.ReportColumn("quantity", "Số lượng sản phẩm", "sum"))
    if group == "product":
        rows = (items.order_by()
                .values(nhom=Concat(F("product__code"), Value(" — "), F("product__name")))
                .annotate(so_dong=Count("record_id", distinct=True),
                          c_orders=Count("record_id", distinct=True), c_quantity=Sum("quantity"))
                .order_by("nhom"))
    else:
        expression, label = group_expression(source, group)
        rows = qs.order_by().values(
            nhom=F("val_date") if expression is None else expression
        ).annotate(so_dong=Count("pk", distinct=True),
                   c_orders=Count("pk", distinct=True), c_quantity=quantity).order_by("nhom")
    label = "Sản phẩm" if group == "product" else group_expression(source, group)[1]
    return DeliveryResult(
        shipping=shipping, ok=True, group_label=label, group_is_date=group == "day", unit="nhóm",
        columns=columns, rows=rows, totals=totals,
    )


def shipping_status(user, source, *, start=None, end=None, product="", market="", **unused):
    qs = filtered_records(user, source, start=start, end=end, product=product, market=market)
    return list(qs.order_by().values(label=status_expression())
                .annotate(count=Count("pk")).order_by("label"))
