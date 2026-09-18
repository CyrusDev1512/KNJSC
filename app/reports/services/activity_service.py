"""Báo cáo ERP: nguồn tường minh, quyền chuẩn, dữ liệu và trình bày tách biệt."""
from dataclasses import dataclass, replace
from decimal import Decimal

from django.db.models import Count, Sum, F, Value, CharField, Q
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Coalesce, NullIf, Concat
from django.contrib.postgres.aggregates import StringAgg

from core.constants import Currency
from core.identity import SEPARATOR, code_expression
from core.managers import apply_scope
from core.exceptions import OutOfScopeError, BusinessError
from forms_builder.models import DataRecord, TableDef
from orders.constants import waybill_condition
from orders.models import WaybillItem
from reports.constants import MISSING_FILTER
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
    # Đúng theo nhãn: Hóa đơn ÷ Doanh thu (ADR-038 thay xác nhận K/J 09.09.2026)
    "invoice_revenue": ("Hóa đơn/Doanh thu", ("invoice", "revenue"), "divide"),
    "aov": ("AOV", ("sales", "orders"), "divide"),
}
#: Khoá không lấy từ cột bảng mà suy ra từ nguồn khác (ADR-038): Doanh thu Marketing =
#: tiền đã thu của vận đơn do marketer phụ trách — `marketing_revenue`.
DERIVED = {"mkt": ("revenue",)}
DISPLAY_ORDER = {
    "sale": ("mess", "orders", "sales", "conversion", "revenue"),
    "mkt": ("mess", "cost", "orders", "sales", "revenue", "invoice",
            "cpo", "mess_cost", "cost_sales", "invoice_revenue", "aov"),
}


@dataclass(frozen=True)
class ActivityResult(aggregations.SummaryResult):
    show_team: bool = False
    show_person: bool = False   # cách xem Tổng hợp: cột Nhân sự + Leader sau cột Ngày (ADR-035)
    show_leader: bool = False   # cách xem Theo nhân viên: cột Leader sau cột nhóm (ADR-035)
    currency_label: str = ''
    currency_warning: str = ''


@dataclass(frozen=True)
class DeliveryResult(ActivityResult):
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
    # Kế toán thấy mọi dòng của mọi nguồn (ADR-038) — cùng luật với DailyReport.
    from org.services.org_service import is_accountant
    qs = DataRecord.objects.filter(table=source.table)
    if is_accountant(user):
        return qs
    if source.kind == "delivery":
        return apply_scope(qs, user, owner="assignment__delivery_id",
                           team="assignment__delivery__profile__team_id",
                           department="department_id")
    return apply_scope(qs, user, owner="created_by_id", team="team_id",
                       department="department_id")


def people_paths(source):
    return ('assignment__delivery', 'assignment__delivery__profile__team') if source.kind == 'delivery' else ('created_by', 'team')


def people_choices(user, source):
    """Chỉ đưa ra nhân sự/team có dữ liệu trong phạm vi báo cáo, kể cả người đã nghỉ."""
    owner, team = people_paths(source)
    qs = records(user, source).order_by()
    pairs = qs.values(
        person_id=F(owner+'_id'), code=code_expression(owner),
        full_name=F(owner+'__profile__full_name'),
        option_team_id=F(team+'_id'), team_name=F(team+'__name')).distinct()
    people, teams = {}, {}
    for pair in pairs:
        if pair['person_id'] is not None:
            # Mã trước, tên sau (ADR-037)
            people[pair['person_id']] = pair['code'] + (
                SEPARATOR+pair['full_name'] if pair['full_name'] else '')
        if pair['option_team_id'] is not None:
            teams[pair['option_team_id']] = pair['team_name']
    return tuple([{'id':key, 'label':label} for key, label in sorted(
        choices.items(), key=lambda item: (item[1], item[0]))] for choices in (people, teams))


def filter_people(qs, source, person='', team=''):
    owner_path, team_path = people_paths(source)
    # Kiểm trên phạm vi gốc, không nhầm người hợp lệ nhưng khác bộ lọc thành mất quyền.
    for value, path in ((person, owner_path), (team, team_path)):
        if not value:
            continue
        try:
            number = int(value)
            if number <= 0 or number > 2**63-1:
                raise ValueError
        except (TypeError, ValueError):
            raise BusinessError('Bộ lọc team/nhân sự không hợp lệ.')
        if not qs.filter(**{path+'_id':number}).exists():
            raise OutOfScopeError('Team hoặc nhân sự không thuộc phạm vi nguồn báo cáo của bạn.')
    if person:
        qs = qs.filter(**{owner_path+'_id':int(person)})
    if team:
        qs = qs.filter(**{team_path+'_id':int(team)})
    return qs


def _as_activity(result, **flags):
    if isinstance(result, ActivityResult):
        return replace(result, **flags)
    return ActivityResult(**{**result.__dict__, **flags})


def person_expressions(source):
    """Nhân sự của dòng (người lập báo cáo; Vận đơn: người được phân công) và leader team
    của người đó, tra từ Tổ chức (`Team.leader`) — không đọc tên tự nhập trong ô (ADR-022, 035).
    Cả hai **chỉ là mã nhân sự** (`core.identity.code_expression`; chưa có mã thì tên đăng nhập) —
    ngoại lệ của ADR-037 (bổ sung 18.09): ô bảng hẹp và gộp nhiều người, ô chọn/chip vẫn `MÃ · Họ tên`."""
    owner, team = people_paths(source)
    return {"person_name": Coalesce(code_expression(owner), Value("Chưa phân công"), output_field=CharField()),
            "leader_name": Coalesce(code_expression(team + "__leader"), Value(""), output_field=CharField())}


def with_day_people(rows, source):
    """Cách xem Tổng hợp giữ nguyên mỗi ngày một dòng; hai cột Nhân sự và Leader gộp tên
    (không trùng, theo thứ tự chữ) của những người có dòng trong ngày, theo đúng bộ lọc và
    phạm vi quyền đang áp — lọc một nhân sự thì chỉ còn người đó (ADR-035)."""
    expressions = person_expressions(source)
    return rows.annotate(
        person_name=StringAgg(expressions["person_name"], delimiter=", ", distinct=True, output_field=CharField()),
        leader_name=StringAgg(NullIf(expressions["leader_name"], Value("")), delimiter=", ", distinct=True, output_field=CharField()),
    )


def with_person_team(result, source, group):
    if not result.ok:
        return result
    if group == 'day':
        return _as_activity(result, rows=with_day_people(result.rows, source), show_person=True)
    if group != 'person':
        return result
    _, team = people_paths(source)
    rows = result.rows.annotate(team_name=Coalesce(F(team+'__name'), Value('Chưa có team')),
                                leader_name=person_expressions(source)['leader_name'])
    return _as_activity(result, rows=rows, show_team=True, show_leader=True)


def group_expression(source, group):
    if group == "person":
        prefix = "assignment__delivery" if source.kind == "delivery" else "created_by"
        return (Coalesce(code_expression(prefix), Value("Chưa phân công"), output_field=CharField()),
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
    derived = DERIVED.get(source.kind, ())
    columns, computed = [], []
    for key in DISPLAY_ORDER[source.kind]:
        if key in FORMULAS:
            label, inputs, kind = FORMULAS[key]
            columns.append(aggregations.ReportColumn(key, label, "computed", 4))
            # Khoá suy ra dùng chính tên khoá làm mã trong dict dòng (xem `attach_derived`)
            codes = tuple(k if k in derived else source.columns.get(k, "__missing_" + k) for k in inputs)
            computed.append(Metric(key, codes, kind))
        elif key in derived:
            columns.append(aggregations.ReportColumn(key, INPUT_LABELS[key], "derived", 2))
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


def segment_options(source):
    """Danh sách Tệp khách hàng của nguồn (ADR-038); nguồn không có cột thì None."""
    from forms_builder.services import choice_service
    code = (source.columns or {}).get("segment")
    column = source.table.columns.filter(code=code).first() if code else None
    if column is None:
        return None
    choices = choice_service.options_for(column)
    return list(choices.options()) if choices is not None else []


def filtered_records(user, source, *, start=None, end=None, product="", market="", person="", team="", segment=""):
    """Bộ lọc duy nhất cho bảng, trạng thái, Tổng quan và tệp xuất."""
    if start and end and start > end:
        raise BusinessError("Từ ngày phải trước hoặc bằng Đến ngày.")
    qs = filter_people(records(user, source), source, person, team)
    if start:
        qs = qs.filter(val_date__gte=start)
    if end:
        qs = qs.filter(val_date__lte=end)
    if market:
        code = source.columns["market"]
        qs = qs.annotate(_market=KeyTextTransform(code, "data"))
        if market == MISSING_FILTER:
            qs = qs.filter(Q(_market__isnull=True) | Q(_market=""))
        else:
            qs = qs.filter(_market=market)
    if segment:
        options = segment_options(source)
        if options is None:
            raise BusinessError("Nguồn báo cáo này không có Tệp khách hàng.")
        code = source.columns["segment"]
        if segment == MISSING_FILTER:
            qs = qs.annotate(_segment=KeyTextTransform(code, "data")).filter(Q(_segment__isnull=True) | Q(_segment=""))
        elif segment in options:
            qs = qs.filter(data__contains={code: segment})   # GIN `record_data_gin`
        else:
            raise BusinessError("Tệp khách hàng không có trong danh sách.")
    if product:
        if source.kind == "delivery":
            items = WaybillItem.objects.for_records(qs).filter(product__code=product)
            qs = qs.filter(pk__in=items.values("record_id"))
        else:
            qs = qs.filter(val_product=product)
    return qs


def build(user, source, *, group="day", start=None, end=None, product="", market="", person="", team="", segment=""):
    if group not in dict(GROUPS):
        raise BusinessError("Cách nhóm không hợp lệ.")
    qs = filtered_records(user, source, start=start, end=end, product=product, market=market,
                          person=person, team=team, segment=segment)
    if source.kind == "delivery":
        return with_person_team(delivery(qs, source, group, product), source, group)
    expression, label = group_expression(source, group)
    result = aggregations.summarize(
        source.table, qs, group_key="ngay" if group == "day" else "nhan-vien",
        columns=list(source.table.columns.all()),
        group_expression=expression, group_label=label,
    )
    result = project_metrics(result, source) if result.ok else result
    derived_currencies = set()
    if result.ok and DERIVED.get(source.kind) and not segment:
        # Lọc theo Tệp khách hàng thì Doanh thu để trống: vận đơn không ghi tệp (ADR-038)
        revenue, derived_currencies = marketing_revenue(
            qs, group, expression, start=start, end=end, product=product, market=market)
        result = attach_derived(result, "revenue", revenue)
    if result.ok and source.columns.get('currency'):
        result = currency_safe_result(result, source, qs, derived_currencies)
    return with_person_team(result, source, group)


def marketing_revenue(qs, group, expression, *, start=None, end=None, product="", market=""):
    """Doanh thu suy ra (ADR-038): tổng tiền đã thu (`WaybillItem.paid_amount`, chính là
    `so_tien_tt`) của vận đơn có Phụ trách Marketing là marketer trong phạm vi báo cáo,
    cùng kỳ theo ngày lên đơn, cùng sản phẩm/quốc gia khi lọc — **một truy vấn**, nhóm
    theo cùng khoá với báo cáo. Trả `({giá trị nhóm: Decimal}, {loại tiền gặp})`.
    Đơn chưa phân công Marketing không vào; đơn chưa có loại tiền góp `None` để cảnh báo."""
    items = (WaybillItem.objects.filter(deleted_at__isnull=True, record__deleted_at__isnull=True)
             .filter(waybill_condition("record__table__"))
             .filter(record__assignment__marketing_id__in=qs.order_by().values("created_by_id")))
    if start:
        items = items.filter(record__val_date__gte=start)
    if end:
        items = items.filter(record__val_date__lte=end)
    if product:
        items = items.filter(product__name=product)
    if market == MISSING_FILTER:
        items = items.annotate(_market=KeyTextTransform("quoc_gia", "record__data")).filter(Q(_market__isnull=True) | Q(_market=""))
    elif market:
        items = items.filter(record__data__contains={"quoc_gia": market})
    keys = {
        "day": F("record__val_date"),
        "person": Coalesce(code_expression("record__assignment__marketing"), Value("Chưa phân công"), output_field=CharField()),
        "product": F("product__name"),
        "market": Coalesce(NullIf(KeyTextTransform("quoc_gia", "record__data"), Value("")), Value("Chưa xác định"), output_field=CharField()),
        "department": F("record__assignment__marketing__profile__department__name"),
    }
    rows = (items.order_by().values(nhom=keys[group], currency=KeyTextTransform("loai_tien", "record__data"))
            .annotate(paid=Sum("paid_amount")))
    revenue, currencies = {}, set()
    for row in rows:
        currencies.add(row["currency"] or None)
        revenue[row["nhom"]] = revenue.get(row["nhom"], Decimal(0)) + (row["paid"] or Decimal(0))
    return revenue, currencies


def attach_derived(result, code, values):
    """Gắn giá trị suy ra vào dòng có trong báo cáo; tổng = tổng các dòng đó (AC-5.4).
    Nhóm chỉ có tiền vận đơn mà không có dòng báo cáo thì không hiện — báo cáo là của
    dòng báo cáo, không phải của vận đơn."""
    if not values:
        return result
    keys = set(result.rows.values_list("nhom", flat=True))
    derived = {key: {**result.derived.get(key, {}), code: value} for key, value in values.items() if key in keys}
    if not derived:
        return result
    total = sum((row[code] for row in derived.values()), Decimal(0))
    result = replace(result, derived=derived, derived_totals={**result.derived_totals, code: total})
    return with_totals(result, result.totals)


def currency_safe_result(result, source, qs, derived_currencies=()):
    """Không công bố tổng tiền khi lẫn đơn vị hoặc dữ liệu cũ chưa có đơn vị — kể cả tiền
    vận đơn suy ra (ADR-038)."""
    currencies = list(qs.order_by().values_list('data__'+source.columns['currency'], flat=True).distinct()[:2])
    mixed = set(currencies) | set(derived_currencies)
    if len(mixed) == 1 and currencies and currencies[0] in Currency.values:
        return ActivityResult(**result.__dict__, currency_label=currencies[0])
    if not currencies and not derived_currencies:
        return result
    warning = ('Bộ lọc có nhiều loại tiền hoặc báo cáo cũ chưa xác định loại tiền. '
               'Các chỉ tiêu tiền tạm để trống để tránh cộng sai đơn vị; chọn một thị trường '
               'và bổ sung loại tiền cho báo cáo cũ qua người quản lý.')
    # Số Mess, số đơn và tỉ lệ chốt vẫn có ý nghĩa trên toàn bộ dữ liệu.
    monetary = {source.columns.get(key) for key in ('cost','sales','revenue','invoice')}
    monetary |= set(DERIVED.get(source.kind, ()))
    monetary |= {'cpo','mess_cost','cost_sales','invoice_revenue','aov'}
    metrics = tuple(metric for metric in result.computed_columns if metric.code not in monetary)
    metrics += tuple(Metric(column.code, (), 'missing') for column in result.columns if column.code in monetary)
    result = replace(result, computed_columns=metrics)
    result = with_totals(result, result.totals)
    return ActivityResult(**result.__dict__, currency_warning=warning)


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


def shipping_status(user, source, *, start=None, end=None, product="", market="", person="", team="", **unused):
    qs = filtered_records(user, source, start=start, end=end, product=product, market=market, person=person, team=team)
    return list(qs.order_by().values(label=status_expression())
                .annotate(count=Count("pk")).order_by("label"))
