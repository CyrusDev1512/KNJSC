from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from core.pagination import paginate
from orders.services import waybill_service

from .services import grid_service, statistics_service, statistics_cache


GROUPS = (
    ("total", "Tổng hợp"),
    ("seller", "Theo nhân viên"),
    ("product", "Theo sản phẩm"),
    ("market", "Theo thị trường"),
)


def _date_range(params):
    default_from, default_to = timezone.localdate().replace(day=1), timezone.localdate()
    raw_from = params.get("tu")
    raw_to = params.get("den")
    errors = []
    try:
        date_from = date.fromisoformat(raw_from) if raw_from else default_from
    except (TypeError, ValueError):
        date_from = default_from
        errors.append("Ngày bắt đầu không hợp lệ.")
    try:
        date_to = date.fromisoformat(raw_to) if raw_to else default_to
    except (TypeError, ValueError):
        date_to = default_to
        errors.append("Ngày kết thúc không hợp lệ.")
    if not errors and date_from > date_to:
        errors.append("Ngày bắt đầu phải trước hoặc bằng ngày kết thúc.")
    return date_from, date_to, errors


def _legacy_waybill_context(request, table, records, group, dashboard, grouped=None):
    if group == "total":
        rows = dashboard["legacy_totals"]
        grouping = ["record__data__loai_tien"]
    else:
        rows, grouping = grouped if grouped is not None else waybill_service.statistics(records, group)
    page = paginate(request, rows)
    results = [
        {
            **row,
            "label": row[grouping[0]] if group != "total" else "Tổng hợp",
            "currency": row["record__data__loai_tien"],
            "quantity": row["quantity_total"],
        }
        for row in page.object_list
    ]
    if group == "product":
        for row in results:
            row["label"] = f'{row["product__name"]} ({row["product__code"]})'
    new_charts = {chart["title"]: chart for chart in dashboard["charts"]}
    legacy_charts = [
        statistics_service.chart(
            "Trạng thái giao hàng",
            [dict(row) for row in dashboard["delivery_groups"]],
            "donut", "Tỷ trọng theo số đơn",
        ),
        statistics_service.chart(
            "Trạng thái thanh toán",
            [dict(row) for row in dashboard["payment_groups"]],
            "donut", "Tỷ trọng số đơn, không phải tỷ lệ thu tiền",
        ),
    ]
    for title, key, note in (
        ("Đơn theo thị trường", "chart_market", "10 thị trường có nhiều đơn nhất"),
        ("Số lượng theo sản phẩm", "chart_product", "10 sản phẩm có số lượng lớn nhất"),
    ):
        full = [dict(row) for row in new_charts[title]["table_groups"]]
        item = statistics_service.chart(title, [dict(row) for row in full[:10]], "bar", note)
        chart_page = paginate(request, full, param=key)
        item["table_groups"] = list(chart_page.object_list)
        item["page"] = chart_page
        params = request.GET.copy()
        params.pop(key, None)
        item["page_url"] = "?" + params.urlencode() + "&" + key + "="
        legacy_charts.append(item)
    summary = {
        "orders": dashboard["orders"],
        "missing": dashboard["missing_items"],
        "totals": dashboard["legacy_totals"],
        "quantity": next(
            (item["value"] for item in dashboard["metrics"] if item["code"] == "quantity"),
            0,
        ),
    }
    return {
        "bang": table,
        "summary": summary,
        "charts": legacy_charts,
        "results": results,
        "page": page,
        "group": group,
        "groups": GROUPS,
    }


def _paginate_charts(request, dashboard):
    if not dashboard:
        return
    for index, chart in enumerate(dashboard.get("charts", []), start=1):
        key = f"chart_{index}"
        page = paginate(request, chart.get("table_groups", []), param=key)
        chart["page"] = page
        params = request.GET.copy()
        params.pop(key, None)
        base = params.urlencode()
        chart["page_url"] = f"?{base}&{key}=" if base else f"?{key}="


@login_required
@statistics_cache.snapshot
def overview(request):
    request.nav_current = "statistics"
    tables = statistics_service.source_tables(request.user)
    sources = statistics_service.describe_sources(tables)
    date_from, date_to, date_errors = _date_range(request.GET)
    source_code = (request.GET.get("nguon") or "").strip()
    table = (
        statistics_service.resolve_source(request.user, source_code, tables, request)
        if source_code else None
    )
    group = request.GET.get("group", "total")
    if group not in {code for code, _ in GROUPS}:
        return HttpResponse("Cách nhóm thống kê không hợp lệ.", status=400)

    dashboard = None
    context = {}
    grid = None
    updated=timezone.now()
    if not date_errors:
        if table is not None:
            # Cùng bộ lọc với lưới để f_*, tìm kiếm và sản phẩm vẫn đúng.
            grid = grid_service.build_grid(request.user, request.GET, table=table)
        def calculate():
            if table is None:
                return statistics_service.build_overview(request.user,tables,request.GET,date_from,date_to,request),None
            dashboard=statistics_service.build_dashboard(request.user,table,date_from,date_to,records=grid.queryset)
            grouped=None
            if dashboard['profile']=='waybill' and dashboard.get('ok') and group!='total':
                rows,grouping=waybill_service.statistics(grid.queryset.filter(val_date__gte=date_from,val_date__lte=date_to),group)
                grouped=(list(rows),grouping)
            return dashboard,grouped
        cached=statistics_cache.result(request.user,tables,request.GET,date_from,date_to,calculate)
        dashboard,grouped=cached['value'];updated=cached['calculated']
        if table is not None:
            if dashboard["profile"] == "waybill" and dashboard.get("ok"):
                records = grid.queryset.filter(
                    val_date__gte=date_from, val_date__lte=date_to,
                )
                context.update(
                    _legacy_waybill_context(request, table, records, group, dashboard,grouped)
                )
        _paginate_charts(request, dashboard)

    params = request.GET.copy()
    for page_key in ("trang", "chart_market", "chart_product", "lam_moi"):
        params.pop(page_key, None)
    context.update({
        "dashboard": dashboard,
        "sources": sources,
        "source_table": table,
        "selected_source": source_code,
        "date_from": date_from,
        "date_to": date_to,
        "date_errors": date_errors,
        "params": params.urlencode(),
        "filters": [
            (key, value)
            for key, values in params.lists()
            if key not in {"group", "nguon", "tu", "den"}
            for value in values
        ],
        "updated": updated,
        "executive_owner": statistics_service.is_executive_owner(request.user),
        "profile_choices": {
            profile: [source for source in sources if source["profile"] == profile]
            for profile in ("marketing", "sale", "waybill")
        },
    })
    if grid is not None:
        context["luoi"] = grid
        chips = []
        for key, label in grid.chips:
            chip_params = params.copy()
            chip_params.pop(key, None)
            chips.append((label, "?" + chip_params.urlencode()))
        context["chips"] = chips
    return render(request, "crm/statistics.html", context)
