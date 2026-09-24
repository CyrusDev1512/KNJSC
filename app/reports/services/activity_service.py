"""Báo cáo ERP: nguồn tường minh, quyền chuẩn, dữ liệu và trình bày tách biệt."""
from dataclasses import dataclass, replace
from decimal import Decimal

from django.db.models import Count, Sum, F, Value, CharField, Q
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Coalesce, NullIf, Concat

from core.identity import SEPARATOR, code_expression
from core.managers import apply_scope
from core.exceptions import OutOfScopeError, BusinessError
from core.money import rates_label, to_vnd, vnd_rate
from forms_builder.models import DataRecord, TableDef
from orders.constants import waybill_condition
from orders.models import WaybillItem
from reports.constants import MISSING_FILTER
from reports.models import ReportSource
from reports import aggregations
from reports.marketing import Metric, with_totals
from reports.services.summary_service import MAX_GROUPS

GROUPS = (
    ("day", "Tổng hợp"), ("person", "Theo nhân viên"),
    ("product", "Theo sản phẩm"), ("market", "Theo thị trường"),
    ("department", "Hiệu suất theo phòng ban"),
)
PERSON_LABELS = {"sale": "Sale", "mkt": "Marketer", "delivery": "Người phụ trách Vận đơn"}
INPUT_LABELS = {
    "mess": "Số Mess", "orders": "Số đơn", "orders_tt": "Số đơn (TT)", "sales": "Doanh số",
    "revenue": "Doanh thu", "cost": "CPQC", "invoice": "Hóa đơn",
}
#: Nhãn riêng của BC MKT theo ảnh mẫu (ADR-042): số marketer tự khai là "DS Chốt", số đối
#: soát từ vận đơn là "(TT)". Sale giữ "Doanh số"/"Doanh thu" (Doanh thu của Sale là cột nhập).
LABEL_OVERRIDES = {"mkt": {"sales": "DS Chốt", "revenue": "DS Chốt (TT)"}}
FORMULA_LABEL_OVERRIDES = {"mkt": {"cost_sales": "CPQC/DS Chốt", "invoice_revenue": "Hóa đơn/DS Chốt (TT)"}}
#: (nhãn, hai vế, phép): "divide" là tỉ số thuần; "percent" nhân 100 để hiện 6,18 % như ảnh
FORMULAS = {
    "conversion": ("Tỉ lệ chốt", ("orders", "mess"), "percent"),
    "conversion_tt": ("Tỉ lệ chốt (TT)", ("orders_tt", "mess"), "percent"),
    "cpo": ("CPO", ("cost", "orders"), "divide"),
    "mess_cost": ("Giá Mess", ("cost", "mess"), "divide"),
    "cost_sales": ("CPQC/Doanh số", ("cost", "sales"), "divide"),
    # Đúng theo nhãn: Hóa đơn ÷ Doanh thu (ADR-038 thay xác nhận K/J 09.09.2026)
    "invoice_revenue": ("Hóa đơn/Doanh thu", ("invoice", "revenue"), "divide"),
    "aov": ("AOV", ("sales", "orders"), "divide"),
}
#: Khoá không lấy từ cột bảng mà đối soát từ vận đơn do marketer phụ trách (ADR-038, ADR-042,
#: `marketing_actuals`): tiền đã thu là tiền, số đơn là số đếm — tách để quy ₫ và định dạng đúng.
DERIVED_MONEY = {"mkt": ("revenue",)}
DERIVED_COUNT = {"mkt": ("orders_tt",)}
DERIVED = {kind: DERIVED_MONEY.get(kind, ()) + DERIVED_COUNT.get(kind, ()) for kind in ("sale", "mkt", "delivery")}
#: Công thức tiền ÷ số đếm: kết quả vẫn là tiền (₫ khi đã quy đổi)
MONEY_FORMULAS = ("cpo", "mess_cost", "aov")
DISPLAY_ORDER = {
    "sale": ("mess", "orders", "sales", "conversion", "revenue"),
    "mkt": ("mess", "cost", "orders", "orders_tt", "sales", "revenue", "conversion", "conversion_tt",
            "mess_cost", "cpo", "cost_sales", "aov", "invoice", "invoice_revenue"),
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


def team_expressions(source):
    """Team và leader của người trong dòng — cột nhóm thêm cho cách xem Theo nhân viên."""
    _, team = people_paths(source)
    return {"team_name": Coalesce(F(team + "__name"), Value("Chưa có team")),
            "leader_name": person_expressions(source)["leader_name"]}


def with_person_team(result, source, group):
    if not result.ok:
        return result
    if group == 'day':
        # Dòng đã mang sẵn `person_name`, `leader_name` vì nhóm theo ngày × nhân sự
        return _as_activity(result, show_person=True)
    if group != 'person':
        return result
    if isinstance(result.rows, list):
        # Dòng đã lấy về bộ nhớ và đã nhóm kèm team/leader (`team_expressions` trong `build`)
        return _as_activity(result, show_team=True, show_leader=True)
    rows = result.rows.annotate(**team_expressions(source))
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


def _formula_format(key, kind, vnd):
    """(số lẻ, hậu tố) của cột công thức: tỉ lệ hiện % hai số lẻ; tiền ÷ số đếm là tiền —
    ₫ không lẻ khi đã quy đổi; tỉ số tiền/tiền bốn số lẻ."""
    if kind == "percent":
        return 2, "%"
    if key in MONEY_FORMULAS and vnd:
        return 0, " ₫"
    return 4, ""


def project_metrics(result, source):
    """Tên, thứ tự và công thức BC SALE/BC MKT dùng chung cho mọi cách xem."""
    summed = {c.code: c for c in result.columns if c.kind == "sum"}
    derived = DERIVED.get(source.kind, ())
    labels = {**INPUT_LABELS, **LABEL_OVERRIDES.get(source.kind, {})}
    formula_labels = FORMULA_LABEL_OVERRIDES.get(source.kind, {})
    vnd = result.converted
    columns, computed = [], []
    for key in DISPLAY_ORDER[source.kind]:
        if key in FORMULAS:
            label, inputs, kind = FORMULAS[key]
            so_le, hau_to = _formula_format(key, kind, vnd)
            columns.append(aggregations.ReportColumn(key, formula_labels.get(key, label), "computed", so_le, hau_to))
            # Khoá suy ra dùng chính tên khoá làm mã trong dict dòng (xem `attach_derived`)
            codes = tuple(k if k in derived else source.columns.get(k, "__missing_" + k) for k in inputs)
            computed.append(Metric(key, codes, kind))
        elif key in derived:
            if key in DERIVED_MONEY.get(source.kind, ()):
                so_le, hau_to = (0, " ₫") if vnd else (2, "")
            else:
                so_le, hau_to = 0, ""
            columns.append(aggregations.ReportColumn(key, labels[key], "derived", so_le, hau_to))
        else:
            code = source.columns.get(key, "__missing_" + key)
            label = labels[key]
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
    # Cột đã prefetch cùng nguồn (`sources`): tra trong bộ nhớ, không thêm truy vấn
    column = next((c for c in source.table.columns.all() if c.code == code), None) if code else None
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
    products = _products(product)
    if products:
        if source.kind == "delivery":
            items = WaybillItem.objects.for_records(qs).filter(product__code__in=products)
            qs = qs.filter(pk__in=items.values("record_id"))
        else:
            qs = qs.filter(val_product__in=products)
    return qs


def _products(product):
    """Sản phẩm đang lọc: một chuỗi (URL cũ, Tổng quan) hay danh sách nhiều mục (ADR-042)."""
    if not product:
        return []
    return [product] if isinstance(product, str) else [p for p in product if p]


def build(user, source, *, group="day", start=None, end=None, product="", market="", person="", team="", segment="",
          detail=False):
    if group not in dict(GROUPS):
        raise BusinessError("Cách nhóm không hợp lệ.")
    qs = filtered_records(user, source, start=start, end=end, product=product, market=market,
                          person=person, team=team, segment=segment)
    if source.kind == "delivery":
        return with_person_team(delivery(qs, source, group, product), source, group)
    expression, label = group_expression(source, group)
    # Tổng hợp = ngày × nhân sự: mỗi người một dòng riêng trong ngày (chủ dự án 19.09,
    # bổ sung ADR-035 — thay quyết định 1 "mỗi ngày một dòng"). Doanh thu suy ra tra theo
    # cặp (ngày, nhân sự) nên không gán nhầm tiền cả ngày cho từng người.
    extra = None
    if group == "day":
        # Ngày × nhân sự, kèm Team để khối theo ngày có cột Team như ảnh (ADR-042)
        extra = {**person_expressions(source), "team_name": team_expressions(source)["team_name"]}
        if detail:
            # Bảng dữ liệu (ADR-042 đợt 4): mỗi lần nộp một dòng — nộp nhiều lần/ngày (ADR-032) vẫn tách
            extra["record_id"] = F("id")
    if group == "person":
        extra = team_expressions(source)   # Team · Leader đi cùng người, không annotate sau
    # Toàn bộ dòng nhóm vào bộ nhớ khi ≤ MAX_GROUPS: tổng, khoá đối soát, tổng ngày và phân
    # trang dùng chung một danh sách — không thêm truy vấn (ADR-042)
    result = aggregations.summarize_in_memory(
        source.table, qs, limit=MAX_GROUPS, group_key="ngay" if group == "day" else "nhan-vien",
        columns=list(source.table.columns.all()),
        group_expression=expression, group_label=label,
        extra_groups=extra, derived_key=("nhom", "person_name") if group == "day" else ("nhom",),
        currency_code=source.columns.get("currency"),   # quy ₫ ngay trong truy vấn (ADR-042)
    )
    result = project_metrics(result, source) if result.ok else result
    if result.ok:
        result = replace(result, thresholds=source.thresholds or {})   # ngưỡng màu Manager đặt (ADR-042)
    thieu_ti_gia = 0
    if result.ok and DERIVED.get(source.kind) and not segment:
        # Lọc theo Tệp khách hàng thì phần đối soát để trống: vận đơn không ghi tệp (ADR-038)
        actual, thieu_ti_gia = marketing_actuals(
            qs, group, expression, start=start, end=end, product=product, market=market)
        result = attach_derived(result, actual, zero=DERIVED_COUNT.get(source.kind, ()))
    if detail and result.ok and result.derived and isinstance(result.rows, list):
        # Một người nộp nhiều lần trong ngày: (TT) khoá theo (ngày, người) không chia được cho từng
        # lần nộp → các dòng đó để trống, TỔNG CỘNG ngày vẫn cộng một lần (G6)
        dem = {}
        for item in result.rows:
            khoa = aggregations.derived_key_of(item, result)
            dem[khoa] = dem.get(khoa, 0) + 1
        result = replace(result, derived_shared=frozenset(k for k, n in dem.items() if n > 1))
    if result.ok and source.columns.get('currency'):
        result = currency_note(result, source, qs, thieu_ti_gia)
    return with_person_team(result, source, group)


def marketing_actuals(qs, group, expression, *, start=None, end=None, product="", market=""):
    """Đối soát từ vận đơn (ADR-038, ADR-042), nhóm theo cùng khoá với báo cáo:
    **Số đơn (TT)** = số vận đơn có Phụ trách Marketing là marketer trong phạm vi báo cáo,
    theo ngày lên đơn, cùng sản phẩm/quốc gia khi lọc; **DS Chốt (TT)** = tổng tiền đã thu
    (`WaybillItem.paid_amount`, chính là `so_tien_tt`) của các đơn đó, **quy ₫** theo loại tiền
    từng đơn. **Một truy vấn trên `DataRecord` vận đơn** — đếm trên đơn chứ không trên chi tiết,
    vì đơn không có chi tiết sản phẩm (ADR-036) vẫn là một đơn; nó chỉ không góp tiền.
    Trả `({khoá: {"orders_tt": n, "revenue": Decimal ₫}}, số đơn thiếu tỉ giá)`; đơn chưa
    phân công Marketing không vào."""
    orders = (DataRecord.objects.filter(waybill_condition("table__"))
              .filter(assignment__marketing_id__in=qs.order_by().values("created_by_id")))
    if start:
        orders = orders.filter(val_date__gte=start)
    if end:
        orders = orders.filter(val_date__lte=end)
    item_filter = Q(waybill_items__deleted_at__isnull=True)
    products = _products(product)
    if products:
        # Lọc TRƯỚC `annotate` để join chỉ còn chi tiết của sản phẩm đã chọn: đơn không có sản
        # phẩm đó rời khỏi kết quả và `Sum` chỉ cộng đúng các chi tiết ấy
        orders = orders.filter(waybill_items__product__name__in=products, waybill_items__deleted_at__isnull=True)
        item_filter &= Q(waybill_items__product__name__in=products)
    if market == MISSING_FILTER:
        orders = orders.annotate(_market=KeyTextTransform("quoc_gia", "data")).filter(Q(_market__isnull=True) | Q(_market=""))
    elif market:
        orders = orders.filter(data__contains={"quoc_gia": market})
    keys = {
        "day": F("val_date"),
        "person": Coalesce(code_expression("assignment__marketing"), Value("Chưa phân công"), output_field=CharField()),
        "product": F("waybill_items__product__name"),
        "market": Coalesce(NullIf(KeyTextTransform("quoc_gia", "data"), Value("")), Value("Chưa xác định"), output_field=CharField()),
        "department": F("assignment__marketing__profile__department__name"),
    }
    cot = {"nhom": keys[group], "currency": KeyTextTransform("loai_tien", "data")}
    if group == "day":
        # Báo cáo nhóm theo ngày × nhân sự nên số đối soát cũng tách theo marketer,
        # không thì mỗi người trong ngày nhận trọn số của cả ngày.
        cot["nguoi"] = keys["person"]
    rows = (orders.order_by().values(**cot)
            .annotate(orders=Count("id", distinct=True), paid=Sum("waybill_items__paid_amount", filter=item_filter)))
    actual, thieu = {}, 0
    for row in rows:
        khoa = (row["nhom"], row["nguoi"]) if group == "day" else row["nhom"]
        muc = actual.setdefault(khoa, {"orders_tt": 0, "revenue": Decimal(0)})
        muc["orders_tt"] += row["orders"]
        if row["paid"]:
            if vnd_rate(row["currency"]) is None:
                thieu += row["orders"]
            else:
                muc["revenue"] += to_vnd(row["paid"], row["currency"])
    return actual, thieu


def attach_derived(result, values, *, zero=()):
    """Gắn giá trị đối soát vào dòng có trong báo cáo; tổng = tổng các dòng đó (AC-5.4).
    Nhóm chỉ có vận đơn mà không có dòng báo cáo thì không hiện — báo cáo là của dòng báo
    cáo, không phải của vận đơn. `values` là `{khoá: {mã: giá trị}}`; mã trong `zero` (số
    đếm) mặc định 0 ở mọi dòng để "không có đơn" hiện 0 chứ không trống."""
    if not values and not zero:
        return result
    khoa = result.derived_key
    if isinstance(result.rows, list):
        keys = {aggregations.derived_key_of(item, result) for item in result.rows}
    else:
        keys = set(result.rows.values_list(khoa[0], flat=True)) if len(khoa) == 1 else set(result.rows.values_list(*khoa))
    derived = {}
    for key in keys:
        muc = {**result.derived.get(key, {}), **{code: Decimal(0) for code in zero}, **values.get(key, {})}
        if muc:
            derived[key] = muc
    if not derived:
        return result
    codes = {code for muc in derived.values() for code in muc}
    totals = {code: sum((muc.get(code) or Decimal(0) for muc in derived.values()), Decimal(0)) for code in codes}
    result = replace(result, derived=derived, derived_totals={**result.derived_totals, **totals})
    return with_totals(result, result.totals)


def currency_note(result, source, qs, thieu_ti_gia=0):
    """Mọi tiền đã quy ₫ ngay trong truy vấn (ADR-042) nên chỉ còn công bố đơn vị và tỉ giá;
    chỉ cảnh báo khi có dòng không quy đổi được (KRW chưa có tỉ giá, báo cáo cũ trống loại
    tiền, vận đơn thiếu tỉ giá): tiền của các dòng đó không vào tổng, cột đếm vẫn tính đủ.
    Đường bình thường không tốn truy vấn; chỉ khi cảnh báo mới tra danh sách loại tiền thiếu."""
    label = "VND (₫), quy đổi theo tỉ giá cố định: " + rates_label()
    thieu = (result.unconverted or 0) + thieu_ti_gia
    if not thieu:
        return ActivityResult(**result.__dict__, currency_label=label)
    ma_thieu = sorted({c or "trống" for c in qs.order_by()
                       .values_list("data__" + source.columns["currency"], flat=True).distinct()
                       if vnd_rate(c) is None})
    warning = (f"{thieu} dòng chưa quy đổi được (loại tiền: {', '.join(ma_thieu) or 'của vận đơn'}): tiền của "
               "các dòng đó không vào tổng, các cột đếm vẫn tính đủ. Bổ sung tỉ giá trong EXCHANGE_RATES_VND "
               "hoặc loại tiền cho báo cáo cũ qua người quản lý.")
    return ActivityResult(**result.__dict__, currency_label=label, currency_warning=warning)


def delivery(qs, source, group, product):
    items = WaybillItem.objects.for_records(qs)
    products = _products(product)
    if products:
        items = items.filter(product__code__in=products)
    item_filter = Q(waybill_items__deleted_at__isnull=True)
    if products:
        item_filter &= Q(waybill_items__product__code__in=products)
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
        # Cách xem Tổng hợp của Vận đơn cũng nhóm theo ngày × người phụ trách (AC-22.14)
        khoa = {"nhom": F("val_date") if expression is None else expression}
        them = []
        if group == "day":
            khoa.update(person_expressions(source))
            khoa["team_name"] = team_expressions(source)["team_name"]
            them = ["person_name", "leader_name", "team_name"]
        rows = qs.order_by().values(**khoa).annotate(
            so_dong=Count("pk", distinct=True),
            c_orders=Count("pk", distinct=True), c_quantity=quantity).order_by("nhom", *them)
    label = "Sản phẩm" if group == "product" else group_expression(source, group)[1]
    return DeliveryResult(
        shipping=shipping, ok=True, group_label=label, group_is_date=group == "day", unit="nhóm",
        columns=columns, rows=rows, totals=totals,
    )


def shipping_status(user, source, *, start=None, end=None, product="", market="", person="", team="", **unused):
    qs = filtered_records(user, source, start=start, end=end, product=product, market=market, person=person, team=team)
    return list(qs.order_by().values(label=status_expression())
                .annotate(count=Count("pk")).order_by("label"))
