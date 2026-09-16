"""HTTP cho báo cáo hoạt động; tính toán và quyền ở service."""
from io import BytesIO

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from core.audit import record
from core.constants import AuditAction
from core.exceptions import BusinessError
from core.pagination import pagination_context
from orders.constants import Market
from reports import aggregations, excel
from reports.services import activity_service as service, summary_service


def parameters(request):
    start, end = summary_service.default_range()
    group = request.GET.get("nhom", "day")
    aliases = {"tong-hop": "day", "nhan-vien": "person", "san-pham": "product", "thi-truong": "market"}
    return {
        "group": aliases.get(group, group),
        "start": summary_service.parse_day(request.GET.get("tu"), start),
        "end": summary_service.parse_day(request.GET.get("den"), end),
        "product": request.GET.get("sp", ""),
        "market": request.GET.get("thi_truong", ""),
        "person": request.GET.get("nhan_su", ""),
        "team": request.GET.get("team", ""),
    }


def _export(request, source, result, params):
    if result.rows.count() > getattr(settings, "EXPORT_MAX_ROWS", 50000):
        raise BusinessError("Thu hẹp bộ lọc để xuất báo cáo.")
    record(AuditAction.EXPORT, actor=request.user, target=source.table,
           detail="Xuất báo cáo hoạt động ERP", request=request)
    book = excel.build_workbook(source.table.name, result,
                                subtitle=f"{params['start']} đến {params['end']}")
    if source.kind == "delivery":
        sheet = book.create_sheet("Trạng thái giao hàng")
        sheet.append(["Trạng thái", "Số đơn"])
        for item in result.shipping:
            sheet.append([item["label"], item["count"]])
    data = BytesIO()
    book.save(data)
    response = HttpResponse(data.getvalue(),
                            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="bao-cao-tong-hop.xlsx"'
    return response


@login_required
def report(request, export=False, choices=None):
    request.nav_current = "bao_cao_tong_hop"
    choices = list(service.sources(request.user)) if choices is None else choices
    source = service.select_source(request.user, request.GET.get("nguon", ""), choices)
    params = parameters(request)
    ctx = {"sources": choices, "source": source, "groups": service.GROUPS,
           "params": params, "markets": Market.labels, "empty": True,
           "query": request.GET.urlencode(), "qs_loc": "&" + request.GET.urlencode()}
    if source:
        ctx['people'], ctx['teams'] = service.people_choices(request.user, source)
        try:
            result = service.build(request.user, source, **params)
        except BusinessError as error:
            return render(request, "reports/activity.html", {**ctx, "error": str(error)}, status=400)
        ctx["unavailable"] = not result.ok
        if result.ok:
            if export:
                try:
                    return _export(request, source, result, params)
                except BusinessError as error:
                    return render(request, "reports/activity.html", {**ctx, "error": str(error)}, status=400)
            # Giới hạn nhóm như báo cáo hiện có; tránh COUNT riêng khi ít nhóm.
            items = list(result.rows[:summary_service.MAX_GROUPS + 1])
            page_source = items if len(items) <= summary_service.MAX_GROUPS else result.rows
            ctx.update(pagination_context(request, page_source, "nhóm"))
            ctx.update(result=result, rows=aggregations.finish_rows(ctx["trang"], result),
                       totals=aggregations.total_cells(result), empty=not result.totals["so_dong"])
            if getattr(result, 'show_team', False):
                for row, raw in zip(ctx['rows'], ctx['trang']):
                    row['team'] = raw['team_name']
            if source.kind == "delivery":
                ctx["shipping"] = result.shipping
    return render(request, "reports/activity.html", ctx)


@login_required
def legacy_redirect(request, export=False):
    """Giữ bookmark cũ và toàn bộ bộ lọc; quyền kiểm tại trang đích."""
    route = "bao_cao_tong_hop_xuat" if export else "bao_cao_tong_hop"
    query = request.GET.urlencode()
    return redirect(reverse(route) + ("?" + query if query else ""))
