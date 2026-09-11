"""Các profile thống kê trên queryset đã giới hạn quyền."""
from datetime import date, timedelta
from decimal import Decimal
from urllib.parse import urlencode

from django.db import connection
from django.db.models import Count, DateField, DecimalField, F, Sum, TextField, Value
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast, NullIf, TruncMonth, TruncWeek

from core.money import MONEY_DECIMAL_PLACES, MONEY_MAX_DIGITS
from forms_builder.meaning import Meaning
from orders.constants import ACTIVE_WAYBILL_TABLE_CODE
from orders.models import WaybillItem
from orders.services import waybill_service
from reports import marketing

from . import statistics_charts as charts
from . import statistics_insights as insights


MAX_GROUPS = 2_000
ATTENTION_DELIVERY = (
    "Hủy trước giao", "Hủy sau giao", "Hoàn", "Hoàn đơn", "Khách vắng", "Hẹn lại",
)
ATTENTION_PAYMENT = (
    "Chưa thanh toán", "Thanh toán một phần", "Thanh toán 1 phần",
)


def normalized(value):
    return marketing.normalized(value or "")


def column_by_name(columns, *names):
    wanted = {normalized(name) for name in names}
    return next((column for column in columns if normalized(column.name) in wanted), None)


def column_by_meaning(columns, meaning):
    return next((column for column in columns if column.meaning == meaning), None)


def profile_of(table, columns=None):
    """Một bảng chỉ thuộc một profile, theo đúng thứ tự ưu tiên đã chốt."""
    columns = list(columns if columns is not None else table.columns.all())
    if table.code == ACTIVE_WAYBILL_TABLE_CODE:
        return "waybill"
    if marketing.is_marketing(columns):
        return "marketing"
    if table.department.code == "sale":
        has_date = column_by_meaning(columns, Meaning.DATE) or column_by_name(columns, "Ngày")
        has_seller = column_by_meaning(columns, Meaning.SELLER) or column_by_name(columns, "Người bán")
        has_orders = column_by_name(columns, "Số đơn")
        has_revenue = (column_by_meaning(columns, Meaning.REVENUE)
                       or column_by_name(columns, "Doanh số", "Doanh thu"))
        if has_date and has_seller and has_orders and has_revenue:
            return "sale"
    return "generic"


def previous_range(date_from, date_to):
    days = (date_to - date_from).days + 1
    previous_to = date_from - timedelta(days=1)
    return previous_to - timedelta(days=days - 1), previous_to


def period_granularity(date_from, date_to):
    days = (date_to - date_from).days + 1
    return "day" if days <= 45 else "week" if days <= 180 else "month"


def _bucket(granularity):
    if granularity == "week":
        return TruncWeek("val_date", output_field=DateField())
    if granularity == "month":
        return TruncMonth("val_date", output_field=DateField())
    return F("val_date")


def _period_label(value, granularity):
    if value is None:
        return "Chưa có ngày"
    if granularity == "week":
        return "Tuần " + value.strftime("%d/%m")
    if granularity == "month":
        return value.strftime("%m/%Y")
    return value.strftime("%d/%m")


def _decimal_expr(code):
    text = NullIf(
        KeyTextTransform(code, "data"),
        Value("", output_field=TextField()),
    )
    return Cast(
        text,
        DecimalField(
            max_digits=MONEY_MAX_DIGITS,
            decimal_places=MONEY_DECIMAL_PLACES,
        ),
    )


def _sum_json(code):
    return Sum(_decimal_expr(code))


def _records_for(records, has_date, date_from, date_to):
    if has_date:
        return records.filter(val_date__gte=date_from, val_date__lte=date_to)
    return records


def source_url(table, date_column, date_from, date_to, extra=None):
    params = {}
    if date_column is not None:
        params[f"f_{date_column.code}__lon_bang"] = date_from.isoformat()
        params[f"f_{date_column.code}__nho_bang"] = date_to.isoformat()
    params.update(extra or {})
    query = urlencode(params, doseq=True)
    return f"/bang-tinh/{table.code}/" + (f"?{query}" if query else "")


def _period_rows(records, granularity, aggregate):
    rows = (
        records.order_by()
        .values(period=_bucket(granularity))
        .annotate(value=aggregate)
        .order_by("period")
    )
    return [
        {
            "label": _period_label(row["period"], granularity),
            "value": row["value"] or Decimal(0),
        }
        for row in rows
    ]


def _group_rows(records, field, aggregate, *, blank="Chưa có", json_code=None):
    if json_code:
        records = records.annotate(
            group_label=NullIf(
                KeyTextTransform(json_code, "data"),
                Value("", output_field=TextField()),
            )
        )
        field = "group_label"
    rows = (
        records.order_by()
        .values(label=F(field))
        .annotate(value=aggregate)
        .order_by("-value", "label")[:MAX_GROUPS]
    )
    return [
        {"label": row["label"] or blank, "value": row["value"] or Decimal(0)}
        for row in rows
    ]


def metric(code, label, value, previous=None, *, suffix="", currency=""):
    return {
        "code": code,
        "label": label,
        "value": value,
        "previous": previous,
        "suffix": suffix,
        "currency": currency,
    }


def divide(numerator, denominator, multiplier=Decimal(1)):
    value = marketing.divide(numerator, denominator)
    return value * multiplier if value is not None else None


def _currency_column(columns):
    return column_by_name(columns, "Loại tiền") or next(
        (column for column in columns if column.code == "loai_tien"),
        None,
    )


def _marketing_money_rows(
        records, currency_col, cost_code, order_code, revenue_code):
    return list(
        records.annotate(currency=NullIf(
            KeyTextTransform(currency_col.code, "data"),
            Value("", output_field=TextField()),
        ))
        .order_by()
        .values("currency")
        .annotate(
            cost=_sum_json(cost_code), orders=_sum_json(order_code),
            revenue=_sum_json(revenue_code),
        )
        .order_by("currency")
    )


def build_marketing(table, records, columns, date_from, date_to, *, summary=False):
    date_col = column_by_meaning(columns, Meaning.DATE) or column_by_name(columns, "Ngày")
    by_name = {normalized(column.name): column for column in columns}
    mess = by_name[normalized("Số Mess")]
    cost = by_name[normalized("CPQC")]
    orders = by_name[normalized("Số đơn")]
    revenue = by_name[normalized("Doanh số")]
    current = _records_for(records, date_col, date_from, date_to)
    previous_from, previous_to = previous_range(date_from, date_to)
    previous = _records_for(records, date_col, previous_from, previous_to)
    expressions = {
        "messages": _sum_json(mess.code),
        "cost": _sum_json(cost.code),
        "orders": _sum_json(orders.code),
        "revenue": _sum_json(revenue.code),
        "rows": Count("id"),
    }
    total = current.order_by().aggregate(**expressions)
    old = previous.order_by().aggregate(**expressions)
    currency_col = _currency_column(columns)
    profile_metrics = [
        metric("messages", "Số Mess", total["messages"] or 0, old["messages"] or 0),
        metric("orders", "Số đơn", total["orders"] or 0, old["orders"] or 0),
        metric("close_rate", "Tỷ lệ chốt",
               divide(total["orders"], total["messages"], Decimal(100)),
               divide(old["orders"], old["messages"], Decimal(100)), suffix="%"),
    ]
    money = []
    ratios = []
    aov = []
    if currency_col:
        money_rows = _marketing_money_rows(
            current, currency_col, cost.code, orders.code, revenue.code,
        )
        old_money_rows = _marketing_money_rows(
            previous, currency_col, cost.code, orders.code, revenue.code,
        )
        old_by_currency = {row["currency"]: row for row in old_money_rows}
        for row in money_rows:
            currency = row["currency"] or "Chưa có loại tiền"
            old_row = old_by_currency.get(row["currency"], {})
            money.append(metric(
                "revenue", "Doanh số", row["revenue"] or 0,
                old_row.get("revenue") or 0, currency=currency,
            ))
            ratios.append(metric(
                "cpo", "CPO", divide(row["cost"], row["orders"]),
                divide(old_row.get("cost"), old_row.get("orders")), currency=currency,
            ))
            aov.append(metric(
                "aov", "AOV", divide(row["revenue"], row["orders"]),
                divide(old_row.get("revenue"), old_row.get("orders")), currency=currency,
            ))
    else:
        profile_metrics.insert(2, metric(
            "cpo", "CPO", divide(total["cost"], total["orders"]),
            divide(old["cost"], old["orders"]),
        ))
        money = [metric(
            "revenue", "Doanh số", total["revenue"] or 0, old["revenue"] or 0,
            currency="Đơn vị theo bảng",
        )]
        aov = [metric(
            "aov", "AOV", divide(total["revenue"], total["orders"]),
            divide(old["revenue"], old["orders"]), currency="Đơn vị theo bảng",
        )]
    granularity = period_granularity(date_from, date_to)
    rhythm = list(
        current.order_by()
        .values(period=_bucket(granularity))
        .annotate(messages=_sum_json(mess.code), orders=_sum_json(orders.code),
                  cost=_sum_json(cost.code))
        .order_by("period")
    )
    labels = [_period_label(row["period"], granularity) for row in rhythm]
    chart_items = [
        charts.line(
            "Nhịp Mess và đơn",
            labels,
            [
                {"label": "Mess", "values": [row["messages"] or 0 for row in rhythm]},
                {"label": "Đơn", "values": [row["orders"] or 0 for row in rhythm]},
            ],
            "Tổng theo " + {"day": "ngày", "week": "tuần", "month": "tháng"}[granularity],
        )
    ]
    if currency_col:
        cpo_rows = list(
            current.annotate(currency=NullIf(
                KeyTextTransform(currency_col.code, "data"),
                Value("", output_field=TextField()),
            ))
            .annotate(period=_bucket(granularity))
            .order_by()
            .values("period", "currency")
            .annotate(cost=_sum_json(cost.code), orders=_sum_json(orders.code))
            .order_by("period", "currency")
        )
        currencies = sorted({row["currency"] or "Chưa có loại tiền" for row in cpo_rows})
        by_point = {
            (_period_label(row["period"], granularity), row["currency"] or "Chưa có loại tiền"):
            divide(row["cost"], row["orders"]) or 0
            for row in cpo_rows
        }
        cpo_series = [
            {"label": f"CPO · {currency}",
             "values": [by_point.get((label, currency), 0) for label in labels]}
            for currency in currencies[:10]
        ]
    else:
        cpo_series = [{"label": "CPO", "values": [
            divide(row["cost"], row["orders"]) or 0 for row in rhythm
        ]}]
    chart_items.append(charts.line(
        "CPO theo thời gian", labels, cpo_series,
        "CPQC tổng chia tổng số đơn trong từng mốc; không cộng lẫn tiền tệ",
        value_label="CPO",
    ))
    seller_col = column_by_meaning(columns, Meaning.SELLER) or column_by_name(columns, "Marketer")
    if seller_col and not summary:
        chart_items.append(charts.bar(
            "Đóng góp theo Marketer",
            _group_rows(current, "val_seller", _sum_json(orders.code),
                        blank="Chưa có Marketer"),
            "10 nhóm dẫn đầu; bảng đối chiếu giữ toàn bộ nhóm",
            value_label="Số đơn",
        ))
    if column_by_meaning(columns, Meaning.PRODUCT) and not summary:
        chart_items.append(charts.bar(
            "Đóng góp theo sản phẩm",
            _group_rows(current, "val_product", _sum_json(orders.code),
                        blank="Chưa có sản phẩm"),
            "Không cộng lặp với biểu đồ Marketer",
            value_label="Số đơn",
        ))
    open_url = source_url(table, date_col, date_from, date_to)
    if total["rows"]:
        insight_items = [insights.item(
            4,
            "Nhịp tạo đơn đang thay đổi",
            insights.comparison(total["orders"], old["orders"], "Số đơn"),
            table.name,
            open_url,
        )]
    else:
        insight_items = [insights.item(
            5,
            "Chưa có dữ liệu Marketing trong kỳ",
            "Không có dòng nào khớp khoảng ngày đang xem.",
            table.name,
            open_url,
        )]
    cpo_column = column_by_name(columns, "CPO")
    if currency_col:
        for cpo in ratios:
            threshold = insights.threshold(
                cpo_column, cpo["value"], f"{table.name} · {cpo['currency']}", open_url,
            )
            if threshold:
                insight_items.append(threshold)
    else:
        threshold = insights.threshold(
            cpo_column, divide(total["cost"], total["orders"]), table.name, open_url,
        )
        if threshold:
            insight_items.append(threshold)
    return {
        "ok": True,
        "profile": "marketing",
        "title": "Marketing",
        "source_name": table.name,
        "source_code": table.code,
        "missing": [],
        "metrics": profile_metrics,
        "money": money,
        "ratios": ratios,
        "aov": aov,
        "charts": chart_items,
        "insights": insights.top(insight_items),
        "open_url": open_url,
        "orders": total["orders"] or Decimal(0),
        "time_rows": [
            {"label": label, "value": row["orders"] or 0}
            for label, row in zip(labels, rhythm)
        ],
    }


def _money_rows(records, order_code, currency_col):
    if currency_col:
        rows = (
            records.annotate(currency=NullIf(
                KeyTextTransform(currency_col.code, "data"),
                Value("", output_field=TextField()),
            ))
            .order_by()
            .values("currency")
            .annotate(orders=_sum_json(order_code), revenue=Sum("val_revenue"))
            .order_by("currency")
        )
        return [
            {**row, "currency": row["currency"] or "Chưa có loại tiền"}
            for row in rows
        ]
    total = records.order_by().aggregate(
        orders=_sum_json(order_code),
        revenue=Sum("val_revenue"),
    )
    return [{**total, "currency": "Đơn vị theo bảng"}]


def build_sale(table, records, columns, date_from, date_to, *, summary=False):
    date_col = column_by_meaning(columns, Meaning.DATE) or column_by_name(columns, "Ngày")
    order_col = column_by_name(columns, "Số đơn")
    currency_col = _currency_column(columns)
    current = _records_for(records, date_col, date_from, date_to)
    previous_from, previous_to = previous_range(date_from, date_to)
    previous = _records_for(records, date_col, previous_from, previous_to)
    money_rows = _money_rows(current, order_col.code, currency_col)
    old_rows = _money_rows(previous, order_col.code, currency_col)
    old_by_currency = {row["currency"]: row for row in old_rows}
    money = [
        metric(
            "revenue", "Doanh thu", row["revenue"] or 0,
            old_by_currency.get(row["currency"], {}).get("revenue") or 0,
            currency=row["currency"],
        )
        for row in money_rows
    ]
    aov = [
        metric(
            "aov", "AOV", divide(row["revenue"], row["orders"]),
            divide(
                old_by_currency.get(row["currency"], {}).get("revenue"),
                old_by_currency.get(row["currency"], {}).get("orders"),
            ),
            currency=row["currency"],
        )
        for row in money_rows
    ]
    total_orders = sum(
        (row["orders"] or Decimal(0) for row in money_rows), Decimal(0)
    )
    old_orders = sum(
        (row["orders"] or Decimal(0) for row in old_rows), Decimal(0)
    )
    granularity = period_granularity(date_from, date_to)
    trend = _period_rows(current, granularity, _sum_json(order_col.code))
    chart_items = [
        charts.single_series_from_rows(
            "Đơn Sale theo thời gian",
            trend,
            "Tổng số đơn báo cáo theo kỳ",
            value_label="Số đơn",
        ),
        charts.bar(
            "Doanh thu tách theo loại tiền",
            [{"label": row["currency"], "value": row["revenue"] or 0}
             for row in money_rows],
            "Không quy đổi và không cộng lẫn tiền tệ",
            value_label="Doanh thu",
        ),
    ]
    if not summary:
        chart_items.append(charts.bar(
            "Đóng góp theo nhân viên",
            _group_rows(current, "val_seller", _sum_json(order_col.code),
                        blank="Chưa có người bán"),
            "Mô tả trung tính; hệ thống chưa áp KPI cá nhân",
            value_label="Số đơn",
        ))
    if column_by_meaning(columns, Meaning.PRODUCT) and not summary:
        chart_items.append(charts.bar(
            "Đóng góp theo sản phẩm",
            _group_rows(current, "val_product", _sum_json(order_col.code),
                        blank="Chưa có sản phẩm"),
            "10 nhóm dẫn đầu",
            value_label="Số đơn",
        ))
    open_url = source_url(table, date_col, date_from, date_to)
    insight_items = [insights.item(
        4,
        "Nhịp đơn Sale đang thay đổi",
        insights.comparison(total_orders, old_orders, "Số đơn"),
        table.name,
        open_url,
    )]
    threshold = insights.threshold(order_col, total_orders, table.name, open_url)
    if threshold:
        insight_items.append(threshold)
    if not total_orders:
        insight_items.insert(0, insights.item(
            5,
            "Chưa có đơn Sale trong kỳ",
            "Tổng cộng từ bảng Sale bằng 0.",
            table.name,
            open_url,
        ))
    return {
        "ok": True,
        "profile": "sale",
        "title": "Sale",
        "source_name": table.name,
        "source_code": table.code,
        "missing": [],
        "metrics": [metric("orders", "Số đơn", total_orders, old_orders)],
        "money": money,
        "ratios": [],
        "aov": aov,
        "charts": chart_items,
        "insights": insights.top(insight_items),
        "open_url": open_url,
        "orders": total_orders,
        "time_rows": trend,
    }


def _waybill_dimensions(records, granularity, kinds=None):
    """Nhịp, trạng thái, thị trường và tiền tệ trong một lần quét."""
    kinds = tuple(kinds or ("period", "delivery", "payment", "market", "currency"))
    scoped = records.order_by().values("val_date", "data")
    scoped_sql, scoped_params = scoped.query.sql_with_params()
    bucket = {
        "day": "val_date",
        "week": "date_trunc('week', val_date)::date",
        "month": "date_trunc('month', val_date)::date",
    }[granularity]
    expressions = {
        "period": "bucket",
        "delivery": "delivery",
        "payment": "payment",
        "market": "market",
        "currency": "currency",
    }
    labels = {
        "period": "to_char(bucket, 'YYYY-MM-DD')",
        "delivery": "COALESCE(delivery, '')",
        "payment": "COALESCE(payment, '')",
        "market": "COALESCE(market, '')",
        "currency": "COALESCE(currency, '')",
    }
    kind_cases = "\n".join(
        f"WHEN GROUPING({expressions[kind]}) = 0 THEN '{kind}'" for kind in kinds
    )
    label_cases = "\n".join(
        f"WHEN GROUPING({expressions[kind]}) = 0 THEN {labels[kind]}" for kind in kinds
    )
    grouping_sets = ", ".join(f"({expressions[kind]})" for kind in kinds)
    sql = f"""
        WITH dimensions AS (
            SELECT {bucket} AS bucket,
                   NULLIF(data->>'trang_thai_vc', '') AS delivery,
                   NULLIF(data->>'trang_thai_tt', '') AS payment,
                   NULLIF(data->>'quoc_gia', '') AS market,
                   NULLIF(data->>'loai_tien', '') AS currency
            FROM ({scoped_sql}) scoped
        ), grouped AS (
            SELECT CASE {kind_cases} END AS kind,
                   CASE {label_cases} END AS label,
                   COUNT(*) AS value
            FROM dimensions
            GROUP BY GROUPING SETS ({grouping_sets})
        ), ranked AS (
            SELECT kind, label, value,
                   ROW_NUMBER() OVER (
                     PARTITION BY kind ORDER BY value DESC, label
                   ) AS position
            FROM grouped
        )
        SELECT kind, label, value FROM ranked WHERE position <= {MAX_GROUPS}
    """
    values = {kind: [] for kind in kinds}
    with connection.cursor() as cursor:
        cursor.execute(sql, scoped_params)
        for kind, label, value in cursor.fetchall():
            order_label = label
            if kind == "period":
                label = _period_label(date.fromisoformat(label), granularity)
            elif kind in {"delivery", "payment"} and not label:
                label = "Chưa có trạng thái"
            elif kind == "market" and not label:
                label = "Chưa có thị trường"
            elif kind == "currency" and not label:
                label = None
            values[kind].append({"label": label, "value": value, "_order": order_label})
    values["period"].sort(key=lambda row: row["_order"])
    for kind, rows in values.items():
        if kind != "period":
            rows.sort(key=lambda row: (-row["value"], row["_order"]))
        for row in rows:
            row.pop("_order")
    return values


def _status_colors(rows, kind):
    delivery = {
        "Đã nhận hàng": "#0b8170",
        "Đang giao": "#4f6f9f",
        "Đã lên đơn": "#687386",
        "Hẹn lại": "#a36b08",
        "Khách vắng": "#a36b08",
        "Hủy trước giao": "#bb3f3f",
        "Hủy sau giao": "#bb3f3f",
        "Hoàn": "#bb3f3f",
        "Hoàn đơn": "#bb3f3f",
    }
    payment = {
        "Đã thanh toán": "#0b8170",
        "Thanh toán một phần": "#a36b08",
        "Thanh toán 1 phần": "#a36b08",
        "Chưa thanh toán": "#bb3f3f",
    }
    palette = delivery if kind == "delivery" else payment
    return [{**row, "color": palette.get(row["label"], "#687386")} for row in rows]


def build_waybill(table, records, columns, date_from, date_to, *, summary=False):
    date_col = column_by_name(columns, "Ngày") or column_by_meaning(columns, Meaning.DATE)
    current = _records_for(records, date_col, date_from, date_to)
    previous_from, previous_to = previous_range(date_from, date_to)
    previous = _records_for(records, date_col, previous_from, previous_to)
    granularity = period_granularity(date_from, date_to)
    if summary:
        dimensions = _waybill_dimensions(
            current, granularity, kinds=("period", "delivery", "payment"),
        )
        order_count = sum((row["value"] for row in dimensions["period"]), 0)
        totals, products, missing_items = [], [], 0
    else:
        snapshot = waybill_service.executive_snapshot(current, granularity, MAX_GROUPS)
        dimensions = {
            "period": [], "delivery": [], "payment": [], "market": [],
        }
        record_counts = {}
        item_money = {}
        products = []
        for row in snapshot:
            kind = row["kind"]
            label = row["label"]
            if kind == "period":
                dimensions[kind].append({
                    "label": _period_label(date.fromisoformat(label), granularity),
                    "value": row["metric_value"], "_order": label,
                })
            elif kind in {"delivery", "payment"}:
                dimensions[kind].append({
                    "label": label or "Chưa có trạng thái",
                    "value": row["metric_value"],
                })
            elif kind == "market":
                dimensions[kind].append({
                    "label": label or "Chưa có thị trường",
                    "value": row["metric_value"],
                })
            elif kind == "record_currency":
                record_counts[label or None] = int(row["metric_value"])
            elif kind == "item_currency":
                item_money[label or None] = row
            elif kind == "product":
                products.append({"label": label or "Chưa có sản phẩm",
                                 "value": row["quantity_total"]})
        dimensions["period"].sort(key=lambda row: row.pop("_order"))
        for kind in ("delivery", "payment", "market"):
            dimensions[kind].sort(key=lambda row: (-row["value"], row["label"]))
        products.sort(key=lambda row: (-row["value"], row["label"]))
        totals = [
            {
                "record__data__loai_tien": currency,
                "orders": orders,
                "quantity_total": item_money.get(currency, {}).get("quantity_total", 0),
                "value": item_money.get(currency, {}).get("money_value", Decimal(0)),
                "paid": item_money.get(currency, {}).get("paid_value", Decimal(0)),
            }
            for currency, orders in sorted(
                record_counts.items(), key=lambda item: (item[0] is not None, item[0] or ""),
            )
        ]
        order_count = sum(record_counts.values())
        missing_items = waybill_service.missing_item_count(current)
    old_orders = previous.count()
    quantity = sum((row["quantity_total"] for row in totals), 0)
    money = []
    paid = []
    for row in totals:
        currency = row["record__data__loai_tien"] or "Chưa có loại tiền"
        money.append(metric("value", "Giá trị", row["value"] or 0, currency=currency))
        paid.append(metric("paid", "Đã thanh toán", row["paid"] or 0, currency=currency))
    trend = dimensions["period"]
    delivery, payment = dimensions["delivery"], dimensions["payment"]
    delivery = _status_colors(delivery, "delivery")
    payment = _status_colors(payment, "payment")
    markets = dimensions.get("market", [])
    products = products[:MAX_GROUPS]
    chart_items = [] if summary else [
        charts.single_series_from_rows(
            "Đơn Vận đơn theo thời gian", trend,
            "Nhịp dòng đơn trong phạm vi người xem", value_label="Số đơn",
        ),
        charts.bar(
            "Trạng thái giao hàng", delivery, "Số đơn theo trạng thái",
            value_label="Số đơn",
        ),
        charts.bar(
            "Trạng thái thanh toán", payment, "Không phải tỷ lệ thu tiền",
            value_label="Số đơn",
        ),
        charts.bar(
            "Đơn theo thị trường", markets, "10 thị trường dẫn đầu",
            value_label="Số đơn",
        ),
        charts.bar(
            "Số lượng theo sản phẩm", products, "10 nhóm dẫn đầu",
            value_label="Số lượng",
        ),
        charts.bar(
            "Chất lượng dữ liệu",
            [
                {"label": "Đủ chi tiết sản phẩm", "value": max(order_count - missing_items, 0)},
                {"label": "Thiếu chi tiết sản phẩm", "value": missing_items},
            ],
            "Đơn thiếu chi tiết vẫn được tính vào tổng số đơn",
            value_label="Số đơn",
        ),
    ]
    open_url = source_url(table, date_col, date_from, date_to)
    insight_items = []
    if missing_items:
        insight_items.append(insights.item(
            1,
            "Chi tiết sản phẩm chưa đủ",
            f"{missing_items} đơn vẫn được tính vào số đơn nhưng chưa có cơ sở tính số lượng và tiền.",
            table.name,
            open_url,
            "warning",
        ))
    attention_delivery = sum(
        (row["value"] for row in delivery if row["label"] in ATTENTION_DELIVERY),
        Decimal(0),
    )
    attention_payment = sum(
        (row["value"] for row in payment if row["label"] in ATTENTION_PAYMENT),
        Decimal(0),
    )
    if attention_delivery:
        state_filters = [
            row["label"] for row in delivery if row["label"] in ATTENTION_DELIVERY
        ]
        insight_items.append(insights.item(
            3,
            "Giao hàng có trạng thái cần kiểm tra",
            f"{attention_delivery} đơn thuộc nhóm Hủy/Hoàn/Khách vắng/Hẹn lại.",
            table.name,
            source_url(
                table, date_col, date_from, date_to,
                {"f_trang_thai_vc__trong": state_filters},
            ),
            "warning",
        ))
    if attention_payment:
        payment_filters = [
            row["label"] for row in payment if row["label"] in ATTENTION_PAYMENT
        ]
        insight_items.append(insights.item(
            3,
            "Thanh toán cần đối chiếu",
            f"{attention_payment} đơn có trạng thái thanh toán cần theo dõi.",
            table.name,
            source_url(
                table, date_col, date_from, date_to,
                {"f_trang_thai_tt__trong": payment_filters},
            ),
            "warning",
        ))
    insight_items.append(insights.item(
        4,
        "Nhịp Vận đơn đang thay đổi",
        insights.comparison(order_count, old_orders, "Số đơn"),
        table.name,
        open_url,
    ))
    return {
        "ok": True,
        "profile": "waybill",
        "title": "Vận đơn",
        "source_name": table.name,
        "source_code": table.code,
        "missing": [],
        "metrics": [
            metric("orders", "Số đơn", order_count, old_orders),
            metric("quantity", "Sản phẩm", quantity),
        ],
        "money": money,
        "paid": paid,
        "ratios": [],
        "aov": [],
        "charts": chart_items,
        "insights": insights.top(insight_items),
        "open_url": open_url,
        "orders": Decimal(order_count),
        "time_rows": trend,
        "missing_items": missing_items,
        "delivery_groups": delivery,
        "payment_groups": payment,
        "legacy_totals": totals,
    }


def build_generic(table, records, columns, date_from, date_to, *, summary=False):
    date_col = column_by_meaning(columns, Meaning.DATE)
    revenue_col = column_by_meaning(columns, Meaning.REVENUE)
    currency_col = _currency_column(columns)
    missing = [] if date_col else ["Ngày"]
    current = _records_for(records, date_col, date_from, date_to)
    total = current.order_by().aggregate(rows=Count("id"), revenue=Sum("val_revenue"))
    previous_from, previous_to = previous_range(date_from, date_to)
    previous = _records_for(records, date_col, previous_from, previous_to)
    old = previous.order_by().aggregate(rows=Count("id"), revenue=Sum("val_revenue"))
    chart_items = []
    trend = []
    if date_col:
        granularity = period_granularity(date_from, date_to)
        trend = _period_rows(current, granularity, Count("id"))
        chart_items.append(charts.single_series_from_rows(
            "Số dòng theo thời gian", trend, "Nhịp cập nhật của bảng",
            value_label="Số dòng",
        ))
        if revenue_col and currency_col:
            revenue_rows = list(
                current.annotate(
                    period=_bucket(granularity),
                    currency=NullIf(
                        KeyTextTransform(currency_col.code, "data"),
                        Value("", output_field=TextField()),
                    ),
                )
                .order_by()
                .values("period", "currency")
                .annotate(value=Sum("val_revenue"))
                .order_by("period", "currency")
            )
            labels = [row["label"] for row in trend]
            currencies = sorted({
                row["currency"] or "Chưa có loại tiền" for row in revenue_rows
            })
            by_point = {
                (_period_label(row["period"], granularity),
                 row["currency"] or "Chưa có loại tiền"): row["value"] or 0
                for row in revenue_rows
            }
            chart_items.append(charts.line(
                "Doanh thu theo thời gian", labels,
                [{
                    "label": currency,
                    "values": [by_point.get((label, currency), 0) for label in labels],
                } for currency in currencies[:10]],
                "Tách loại tiền; không tự quy đổi",
                value_label=revenue_col.name,
            ))
        elif revenue_col:
            revenue_trend = _period_rows(current, granularity, Sum("val_revenue"))
            chart_items.append(charts.single_series_from_rows(
                "Doanh thu theo thời gian", revenue_trend,
                "Đơn vị theo bảng; không tự quy đổi",
                value_label=revenue_col.name,
            ))
    grouping = (
        (Meaning.SELLER, "val_seller", "Theo người bán"),
        (Meaning.PRODUCT, "val_product", "Theo sản phẩm"),
        (Meaning.STATUS, "val_status", "Theo trạng thái"),
    )
    for meaning, field, title in grouping:
        if column_by_meaning(columns, meaning):
            chart_items.append(charts.bar(
                title,
                _group_rows(current, field, Count("id")),
                "10 nhóm dẫn đầu",
                value_label="Số dòng",
            ))
    open_url = source_url(table, date_col, date_from, date_to)
    insight_items = []
    if missing:
        insight_items.append(insights.item(
            1,
            "Chưa thể lọc theo kỳ",
            "Bảng thiếu nhãn ý nghĩa Ngày; hệ thống không tự đoán cột.",
            table.name,
            open_url,
            "warning",
        ))
    if not total["rows"]:
        insight_items.append(insights.item(
            5, "Bảng chưa có dữ liệu",
            "Không có dòng nào trong phạm vi hiện tại.",
            table.name, open_url,
        ))
    elif date_col:
        insight_items.append(insights.item(
            4, "Số dòng đang thay đổi",
            insights.comparison(total["rows"], old["rows"], "Số dòng"),
            table.name, open_url,
        ))
    money = []
    if revenue_col:
        if currency_col:
            def revenue_by_currency(queryset):
                return list(
                    queryset.annotate(currency=NullIf(
                        KeyTextTransform(currency_col.code, "data"),
                        Value("", output_field=TextField()),
                    ))
                    .order_by()
                    .values("currency")
                    .annotate(revenue=Sum("val_revenue"))
                    .order_by("currency")
                )

            current_money = revenue_by_currency(current)
            old_money = {
                row["currency"]: row["revenue"] for row in revenue_by_currency(previous)
            }
            money.extend(
                metric(
                    "revenue", revenue_col.name, row["revenue"] or 0,
                    old_money.get(row["currency"]) or 0,
                    currency=row["currency"] or "Chưa có loại tiền",
                )
                for row in current_money
            )
        else:
            money.append(metric(
                "revenue", revenue_col.name, total["revenue"] or 0,
                old["revenue"] or 0, currency="Đơn vị theo bảng",
            ))
    return {
        "ok": True,
        "profile": "generic",
        "title": table.name,
        "source_name": table.name,
        "source_code": table.code,
        "missing": missing,
        "metrics": [metric("rows", "Số dòng", total["rows"], old["rows"])],
        "money": money,
        "ratios": [],
        "aov": [],
        "charts": chart_items,
        "insights": insights.top(insight_items),
        "open_url": open_url,
        "orders": None,
        "time_rows": trend,
        "legacy_note": (
            "Nguồn lịch sử; không áp quy tắc riêng của Vận đơn mới."
            if table.code == "van_don" else ""
        ),
    }


BUILDERS = {
    "marketing": build_marketing,
    "sale": build_sale,
    "waybill": build_waybill,
    "generic": build_generic,
}


def build(table, records, date_from, date_to):
    columns = list(table.columns.all())
    profile = profile_of(table, columns)
    return BUILDERS[profile](table, records, columns, date_from, date_to)
