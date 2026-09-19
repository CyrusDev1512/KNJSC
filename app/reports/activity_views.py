"""HTTP cho báo cáo hoạt động; tính toán và quyền ở service."""
from io import BytesIO

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone

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
        "segment": request.GET.get("tep", ""),
    }


def _export(request, source, result, params):
    if result.rows.count() > getattr(settings, "EXPORT_MAX_ROWS", 50000):
        raise BusinessError("Thu hẹp bộ lọc để xuất báo cáo.")
    record(AuditAction.EXPORT, actor=request.user, target=source.table,
           detail="Xuất báo cáo hoạt động ERP", request=request)
    subtitle = f"{params['start']} đến {params['end']}"
    if params.get("segment"):
        subtitle += " · Tệp khách hàng: " + ("chưa có" if params["segment"] == "__missing__" else params["segment"])
    book = excel.build_workbook(source.table.name, result, subtitle=subtitle)
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
           "presets": summary_service.date_presets(timezone.localdate(), start=params["start"], end=params["end"]),
           "query": request.GET.urlencode(), "qs_loc": "&" + request.GET.urlencode()}
    if source:
        ctx['people'], ctx['teams'] = service.people_choices(request.user, source)
        ctx['segments'] = service.segment_options(source)   # None: nguồn không có Tệp khách hàng
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
            # 100 nhóm mỗi trang (ADR-035): bảng theo ngày × nhân sự nhiều dòng hơn bản theo ngày.
            ctx.update(pagination_context(request, page_source, "nhóm", default_size=100))
            ctx.update(result=result, rows=aggregations.finish_rows(ctx["trang"], result),
                       totals=aggregations.total_cells(result), empty=not result.totals["so_dong"])
            show_team, show_person, show_leader = (getattr(result, flag, False) for flag in ("show_team", "show_person", "show_leader"))
            # Mỗi dòng là một người (Tổng hợp nhóm theo ngày × nhân sự) nên ô danh tính
            # chỉ có một nhãn.
            for row, raw in zip(ctx['rows'], ctx['trang']):
                if show_team:
                    row['team'] = raw['team_name']
                if show_person:
                    row['person'] = raw['person_name']
                if show_person or show_leader:
                    row['leader'] = raw['leader_name'] or '—'
            # Dòng "Tổng trong bộ lọc" ôm cột nhóm và các cột danh tính.
            ctx["label_span"] = 1 + show_team + 2 * show_person + show_leader
            ctx.update(identity_layout(result, show_team, show_person, show_leader))
            if source.kind == "delivery":
                ctx["shipping"] = result.shipping
    if source:
        ctx.update(filter_chips(request, params, ctx))
    return render(request, "reports/activity.html", ctx)


#: Chiều rộng cột định danh theo loại (biến CSS khai ở `.report-view`, thu nhỏ theo màn hình).
IDENTITY_WIDTH = {"team": "--w-team", "ngay": "--w-ngay", "nhom": "--w-nhom", "person": "--w-nhan-su", "leader": "--w-leader"}
IDENTITY_CLASS = {"team": "id-team", "ngay": "id-ngay", "nhom": "id-nhom", "person": "id-nhan-su", "leader": "id-leader"}


def identity_layout(result, show_team, show_person, show_leader):
    """Cột định danh ghim trái (bản vẽ 18.09): thứ tự Team · nhóm · Nhân sự · Leader theo cách xem;
    `left` của cột thứ 2–4 là tổng chiều rộng các cột trước, đặt bằng biến CSS trên `<table>`."""
    kinds = []
    if show_team:
        kinds.append(("team", "Team", "team"))
    kinds.append(("nhom", result.group_label, "ngay" if result.group_is_date else "nhom"))
    if show_person:
        kinds.append(("person", "Nhân sự", "person"))
    if show_person or show_leader:
        kinds.append(("leader", "Leader", "leader"))
    columns, style, widths = [], [], []
    for pos, (code, label, width) in enumerate(kinds, start=1):
        columns.append({"code": code, "label": label, "kind": IDENTITY_CLASS[width], "pos": pos, "edge": pos == len(kinds)})
        if pos >= 2:
            style.append(f"--id-left-{pos}:calc({' + '.join(f'var({w})' for w in widths)})")
        widths.append(IDENTITY_WIDTH[width])
    return {"identity_columns": columns, "identity_style": ";".join(style)}


def filter_chips(request, params, ctx):
    """Hàng chip bộ lọc đang áp, render từ `params`; × của mỗi chip là link cùng URL bỏ đúng tham số
    (Kỳ bỏ cả `tu` và `den` để về mặc định; bỏ Team thì bỏ luôn Nhân sự). Không có chip Nguồn;
    Cách xem không bỏ được."""
    def without(*keys):
        query = request.GET.copy()
        for key in keys:
            query.pop(key, None)
        return "?" + query.urlencode()
    chips = [{"label": "Kỳ", "value": f"{params['start']:%d/%m} – {params['end']:%d/%m/%Y}",
              "url": without("tu", "den") if request.GET.get("tu") or request.GET.get("den") else ""}]
    chips.append({"label": "Cách xem", "value": dict(service.GROUPS).get(params["group"], params["group"]), "url": ""})
    if params["product"]:
        chips.append({"label": "Sản phẩm", "value": params["product"], "url": without("sp")})
    if params["market"]:
        chips.append({"label": "Thị trường", "value": "Chưa xác định" if params["market"] == "__missing__" else params["market"], "url": without("thi_truong")})
    if params.get("segment"):
        chips.append({"label": "Tệp", "value": "Chưa có" if params["segment"] == "__missing__" else params["segment"], "url": without("tep")})
    for key, param, query_key, label in (("teams", "team", "team", "Team"), ("people", "person", "nhan_su", "Nhân sự")):
        value = params[param]
        if value:
            name = next((item["label"] for item in ctx.get(key, ()) if str(item["id"]) == str(value)), value)
            chips.append({"label": label, "value": name, "url": without(query_key, *(("nhan_su",) if param == "team" else ()))})
    keep = request.GET.copy()
    for key in list(keep.keys()):
        if key != "nguon":
            keep.pop(key)
    return {"chips": chips, "filters_active": sum(1 for chip in chips if chip["url"]), "clear_url": "?" + keep.urlencode()}


@login_required
def legacy_redirect(request, export=False):
    """Giữ bookmark cũ và toàn bộ bộ lọc; quyền kiểm tại trang đích."""
    route = "bao_cao_tong_hop_xuat" if export else "bao_cao_tong_hop"
    query = request.GET.urlencode()
    return redirect(reverse(route) + ("?" + query if query else ""))
