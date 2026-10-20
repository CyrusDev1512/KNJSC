from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from core.lien_ket import theo_host_dang_mo
from core.pagination import paginate
from orders.services import waybill_service

from .services import grid_service, statistics_service, statistics_cache


#: Ô ẩn của form Bàn điều hành: nguồn mà bộ lọc lưới đang mang thuộc về (TL-110)
LOC_NGUON = "loc_nguon"

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


def _links_for_host(request, dashboard):
    """Nút sang Báo cáo tổng hợp KN ERP giữ host đang mở (AC-1.10, AC-40.9). Khoá bộ nhớ đệm Thống kê không theo host
    nên số liệu lưu địa chỉ theo cấu hình; đổi ở đây, trên bản riêng của mỗi lần trả lời."""
    if not dashboard:
        return
    items = [dashboard, *dashboard.get("sections", {}).values()]
    for item in items:
        if item.get("open_url"):
            item["open_url"] = theo_host_dang_mo(item["open_url"], request)
        for insight in item.get("insights", []):
            if insight.get("href"):
                insight["href"] = theo_host_dang_mo(insight["href"], request)


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


def _bo_loc_doi_nguon(params):
    """Áp dụng gửi kèm bộ lọc lưới (ô ẩn) và `loc_nguon`. Cùng nguồn thì giữ; đổi nguồn thì bỏ: `f_*`, Tìm, Tôi của bảng
    này vô nghĩa ở bảng kia, giữ lại là lọc lặng lẽ bảng mới (TL-110). Trả truy vấn đã bỏ `loc_nguon` để địa chỉ, khoá
    bộ đệm và link phân trang không mang nó; None khi URL không có `loc_nguon`."""
    if LOC_NGUON not in params:
        return None
    sach = params.copy()
    sach.pop(LOC_NGUON, None)
    if (params.get(LOC_NGUON) or "").strip() != (params.get("nguon") or "").strip():
        for key in [k for k in sach if grid_service.is_grid_param(k)]:
            del sach[key]
    return sach.urlencode()

@login_required
@statistics_cache.snapshot
def overview(request):
    sach = _bo_loc_doi_nguon(request.GET)
    if sach is not None:
        return redirect(f"{request.path}?{sach}" if sach else request.path)
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
        _links_for_host(request, dashboard)

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
    loc = grid_service.grid_params(params) if table is not None else []
    if loc:
        # Áp dụng mang bộ lọc lưới bằng ô ẩn, kèm nguồn chúng thuộc về; cả khi ngày sai để sửa ngày không mất lọc (TL-110)
        context["giu_loc"] = [(LOC_NGUON, source_code), *loc]
        context["bo_loc_luoi"] = grid_service.qs_without(params, {k for k, _ in loc})
    if grid is not None:
        context["luoi"] = grid

        def bo(key):
            chip_params = params.copy()
            chip_params.pop(key, None)
            return "?" + chip_params.urlencode()
        # Tôi, Tìm, Chỉ dòng trùng có nút hay ô riêng trên lưới nên không thành chip ở đó; ở Thống kê phải đọc được
        chips = [(nhan, bo(key), False) for key, nhan, bat in (
            (grid_service.MY_SCOPE_PARAM, "Của tôi", grid.my_scope),
            ("tim", f"Tìm “{grid.search}”", bool(grid.search)),
            ("trung", "Chỉ dòng trùng", grid.duplicates_only)) if bat]
        chips += [(label, bo(key), an) for key, label, an in grid.chips]
        context["chips"] = chips
    return render(request, "crm/statistics.html", context)
