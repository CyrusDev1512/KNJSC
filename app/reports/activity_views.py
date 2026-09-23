"""HTTP cho báo cáo hoạt động; tính toán và quyền ở service."""
from io import BytesIO
from urllib.parse import parse_qsl, urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from core.audit import record, record_denied
from core.constants import AuditAction
from core.exceptions import BusinessError, OutOfScopeError
from core.pagination import pagination_context
from orders.constants import Market
from orders.models import WaybillItem
from reports import aggregations, excel, layout
from reports.services import activity_service as service, summary_service, threshold_service


def parameters(request):
    start, end = summary_service.default_range()
    group = request.GET.get("nhom", "day")
    aliases = {"tong-hop": "day", "nhan-vien": "person", "san-pham": "product", "thi-truong": "market"}
    return {
        "group": aliases.get(group, group),
        "start": summary_service.parse_day(request.GET.get("tu"), start),
        "end": summary_service.parse_day(request.GET.get("den"), end),
        # Nhiều sản phẩm (ADR-040 đợt 3): `sp` lặp lại; URL cũ `sp=A` vẫn là danh sách một mục
        "product": [p for p in request.GET.getlist("sp") if p],
        "market": request.GET.get("thi_truong", ""),
        "person": request.GET.get("nhan_su", ""),
        "team": request.GET.get("team", ""),
        "segment": request.GET.get("tep", ""),
    }


def _export(request, source, result, params, gop=False):
    if aggregations.row_count(result) > getattr(settings, "EXPORT_MAX_ROWS", 50000):
        raise BusinessError("Thu hẹp bộ lọc để xuất báo cáo.")
    record(AuditAction.EXPORT, actor=request.user, target=source.table,
           detail="Xuất báo cáo hoạt động ERP", request=request)
    subtitle = f"{params['start']} đến {params['end']}"
    if params.get("product"):
        subtitle += " · Sản phẩm: " + ", ".join(params["product"])
    if params.get("segment"):
        subtitle += " · Tệp khách hàng: " + ("chưa có" if params["segment"] == "__missing__" else params["segment"])
    blocks = None
    if getattr(result, "show_person", False):
        # Xuất theo khối như màn hình (ADR-040), trên toàn bộ dòng — không cắt trang
        items = list(result.rows)
        tieu_de = f"Toàn kỳ {params['start']:%d/%m} – {params['end']:%d/%m/%Y} · theo nhân sự"
        khoi_ky = period_block(request, source, result, items if len(items) <= summary_service.MAX_GROUPS else None, items, params, tieu_de)
        if gop:
            blocks = [khoi_ky, layout.days_block(items, layout.days_of(items), result)]
        else:
            blocks = [khoi_ky, *layout.day_blocks(aggregations.finish_rows(items, result), items, items, result)]
    book = excel.build_workbook(source.table.name, result, subtitle=subtitle, blocks=blocks)
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
    gop = request.GET.get("gop") == "1"   # Gộp theo ngày (ADR-040): mỗi ngày một dòng
    # Liên kết phân trang ghép `?trang=N&moi_trang=M` + `qs_loc`: bỏ hai khoá đó khỏi `qs_loc`,
    # không thì giá trị cũ đứng sau thắng và từ trang 2 bấm trang khác vẫn đứng yên (TL-47)
    giu = request.GET.copy()
    for key in ("trang", "moi_trang"):
        giu.pop(key, None)
    ctx = {"sources": choices, "source": source, "groups": service.GROUPS,
           "params": params, "markets": Market.labels, "empty": True,
           "presets": summary_service.date_presets(timezone.localdate(), start=params["start"], end=params["end"]),
           "query": request.GET.urlencode(), "qs_loc": ("&" + giu.urlencode()) if giu else ""}
    if source:
        ctx['people'], ctx['teams'] = service.people_choices(request.user, source)
        ctx['segments'] = service.segment_options(source)   # None: nguồn không có Tệp khách hàng
        ctx['products'] = product_options(request.user, source)
        try:
            result = service.build(request.user, source, **params)
        except BusinessError as error:
            return render(request, "reports/activity.html", {**ctx, "error": str(error)}, status=400)
        ctx["unavailable"] = not result.ok
        if result.ok:
            if export:
                try:
                    return _export(request, source, result, params, gop)
                except BusinessError as error:
                    return render(request, "reports/activity.html", {**ctx, "error": str(error)}, status=400)
            ctx.update(blocks_context(request, source, result, params, gop))
            if source.kind == "delivery":
                ctx["shipping"] = result.shipping
            if threshold_service.can_set(request.user, source):
                # Form Ngưỡng màu chỉ cho quản lý bộ phận sở hữu nguồn; mở sẵn sau khi lưu lỗi (`?nguong=1`)
                ctx["nguong"] = {"rows": threshold_service.rows(source, {c.code: c.label for c in result.columns}),
                                 "mo": request.GET.get("nguong") == "1"}
    if source:
        ctx.update(filter_chips(request, params, ctx))
        if source and ctx.get("result") is not None and getattr(ctx["result"], "show_person", False):
            ctx.update(gop=gop, gop_url=_with(request, gop="1"), khong_gop_url=_with(request, gop=None))
    return render(request, "reports/activity.html", ctx)


def product_options(user, source):
    """Danh sách tick Sản phẩm: chỉ sản phẩm có thật trong phạm vi quyền (Leader không thấy hàng
    team khác). Nguồn báo cáo: tên sản phẩm (`val_product`); vận đơn: mã kèm tên từ chi tiết đơn."""
    records = service.records(user, source)
    if source.kind == "delivery":
        cap = (WaybillItem.objects.for_records(records).order_by("product__code")
               .values_list("product__code", "product__name").distinct())
        return [{"value": code, "label": f"{code} — {name}"} for code, name in cap]
    return [{"value": name, "label": name} for name in summary_service.product_choices(records, source.table)]


@login_required
@require_POST
def thresholds(request):
    """Manager bộ phận sở hữu nguồn (hoặc Admin) đặt ngưỡng màu ba bậc (ADR-040 đợt 3): sai thứ tự,
    thiếu một mốc, không phải số → báo lỗi, không lưu; người khác 403 có nhật ký."""
    code = request.POST.get("nguon", "")
    if not code:
        return HttpResponseBadRequest("Thiếu nguồn báo cáo.")
    source = service.select_source(request.user, code)      # ngoài phạm vi → 403
    if not threshold_service.can_set(request.user, source):
        record_denied(request.user, request.path, request)
        raise OutOfScopeError("Chỉ quản lý của bộ phận sở hữu nguồn mới đặt được ngưỡng màu.")
    next_url = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = reverse("bao_cao_tong_hop") + "?nguon=" + code
    # Bỏ `nguong=1` cũ trước khi thêm lại khi lỗi: lưu hụt hai lần liên tiếp không nối đuôi `&nguong=1`
    duong, _, hoi = next_url.partition("?")
    giu = [(k, v) for k, v in parse_qsl(hoi, keep_blank_values=True) if k != "nguong"]
    next_url = duong + ("?" + urlencode(giu) if giu else "")
    try:
        data = threshold_service.parse(request.POST)
    except BusinessError as error:
        messages.error(request, str(error))
        return redirect(next_url + ("&" if giu else "?") + "nguong=1")
    threshold_service.update(source, data, actor=request.user, request=request)
    messages.success(request, "Đã lưu ngưỡng màu.")
    return redirect(next_url)


def _with(request, **doi):
    """URL hiện tại với vài tham số đổi/bỏ (giá trị None là bỏ), về trang 1."""
    query = request.GET.copy()
    for key in ("trang",):
        query.pop(key, None)
    for key, value in doi.items():
        query.pop(key, None)
        if value is not None:
            query[key] = value
    return "?" + query.urlencode()


def blocks_context(request, source, result, params, gop):
    """Bố cục khối như ảnh mẫu (ADR-040 đợt 2). Cách xem Tổng hợp: khối toàn kỳ theo nhân sự
    (cộng trong bộ nhớ, không truy vấn thêm) rồi mỗi ngày một khối có TỔNG CỘNG riêng và STT;
    Gộp thì một khối mỗi ngày một dòng. Cách xem khác: một khối như cũ. `rows` phẳng, `label_span`,
    `identity_columns` giữ cho Tổng quan và bài kiểm."""
    show_team, show_person, show_leader = (getattr(result, flag, False) for flag in ("show_team", "show_person", "show_leader"))
    # Giới hạn nhóm như báo cáo hiện có; dòng đã ở bộ nhớ khi ≤ MAX_GROUPS (`summarize_in_memory`).
    items = list(result.rows[:summary_service.MAX_GROUPS + 1])
    ca_bo = items if len(items) <= summary_service.MAX_GROUPS else None
    ctx = {"result": result, "totals": aggregations.total_cells(result), "empty": not result.totals["so_dong"]}
    tieu_de_ky = f"Toàn kỳ {params['start']:%d/%m} – {params['end']:%d/%m/%Y} · theo nhân sự"
    if show_person and gop:
        # Gộp: mỗi ngày một dòng — phân trang trên danh sách ngày
        nguon = ca_bo if ca_bo is not None else items
        ngay = layout.days_of(nguon)
        ctx.update(pagination_context(request, ngay, "ngày", default_size=100))
        blocks = [period_block(request, source, result, ca_bo, items, params, tieu_de_ky),
                  layout.days_block(nguon, list(ctx["trang"]), result)]
    else:
        # 100 nhóm mỗi trang (ADR-035): bảng theo ngày × nhân sự nhiều dòng hơn bản theo ngày.
        page_source = items if ca_bo is not None else result.rows
        ctx.update(pagination_context(request, page_source, "nhóm", default_size=100))
        page_items = list(ctx["trang"])
        rows = aggregations.finish_rows(page_items, result)
        if show_person:
            all_items = ca_bo if ca_bo is not None else page_items
            blocks = [period_block(request, source, result, ca_bo, items, params, tieu_de_ky),
                      *layout.day_blocks(rows, page_items, all_items, result)]
        else:
            for row, raw in zip(rows, page_items):
                row["kind"] = "row"
                if show_team:
                    row["team"] = raw["team_name"]
                if show_leader:
                    row["leader"] = raw["leader_name"] or "—"
            blocks = [layout.single_block(single_kinds(result, show_team, show_leader), rows, ctx["totals"])]
    ctx["blocks"] = blocks
    ctx["rows"] = layout.flat_rows(blocks) if show_person else blocks[0]["rows"]
    # Khối cuối là khối đang phân trang; cột danh tính của nó là thứ template cũ và bài kiểm đọc
    dai_dien = blocks[-1]
    ctx.update(label_span=dai_dien["label_span"], identity_columns=dai_dien["identity_columns"],
               identity_style=dai_dien["identity_style"])
    return ctx


def period_block(request, source, result, ca_bo, items, params, title):
    """Khối toàn kỳ theo nhân sự: từ dòng trong bộ nhớ khi ≤ MAX_GROUPS; chạm trần thì dùng kết
    quả cách xem Theo nhân viên (thêm truy vấn, hiếm)."""
    if ca_bo is not None:
        return layout.period_block(ca_bo, result, title)
    ky = {k: v for k, v in params.items() if k != "group"}
    nguoi = service.build(request.user, source, group="person", **ky)
    dong = list(nguoi.rows)
    return layout.period_block_from_rows(aggregations.finish_rows(dong, nguoi), dong, nguoi, title)


def single_kinds(result, show_team, show_leader):
    """Cột định danh của cách xem không theo ngày (bản vẽ 18.09): Team · nhóm · Leader."""
    kinds = []
    if show_team:
        kinds.append(("team", "Team", "team"))
    kinds.append(("nhom", result.group_label, "ngay" if result.group_is_date else "nhom"))
    if show_leader:
        kinds.append(("leader", "Leader", "leader"))
    return kinds


def filter_chips(request, params, ctx):
    """Hàng chip bộ lọc đang áp, render từ `params`; × của mỗi chip là link cùng URL bỏ đúng tham số
    (Kỳ bỏ cả `tu` và `den` để về mặc định; bỏ Team thì bỏ luôn Nhân sự). Không có chip Nguồn;
    Cách xem không bỏ được."""
    def without(*keys):
        query = request.GET.copy()
        for key in keys:
            query.pop(key, None)
        return "?" + query.urlencode()
    # Form luôn gửi `tu`/`den`, nên "đang lọc kỳ" là kỳ KHÁC mặc định — không phải "có tham số"
    # (trước đây chip Kỳ có × ngay sau lần Áp dụng đầu tiên, TL-46)
    dang_loc_ky = (params["start"], params["end"]) != summary_service.default_range()
    chips = [{"label": "Kỳ", "value": f"{params['start']:%d/%m} – {params['end']:%d/%m/%Y}",
              "url": without("tu", "den") if dang_loc_ky else ""}]
    chips.append({"label": "Cách xem", "value": dict(service.GROUPS).get(params["group"], params["group"]), "url": ""})
    if request.GET.get("gop") == "1":
        chips.append({"label": "Gộp", "value": "mỗi ngày một dòng", "url": without("gop")})
    if params["product"]:
        sp = params["product"]
        chips.append({"label": "Sản phẩm", "value": ", ".join(sp) if len(sp) <= 2 else f"{len(sp)} sản phẩm", "url": without("sp")})
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
