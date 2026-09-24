"""HTTP cho báo cáo hoạt động; tính toán và quyền ở service, bối cảnh màn hình ở `reports.screen`
(dùng chung với Bảng dữ liệu dạng báo cáo, ADR-042 đợt 4)."""
from urllib.parse import parse_qsl, urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from core.audit import record_denied
from core.exceptions import BusinessError, OutOfScopeError
from orders.constants import Market
from reports.screen import blocks_context, export_response as _export, filter_chips, parameters, product_options, with_query as _with
from reports.services import activity_service as service, summary_service, threshold_service


@login_required
def report(request, export=False, choices=None):
    request.nav_current = "bao_cao_tong_hop"
    choices = list(service.sources(request.user)) if choices is None else choices
    source = service.select_source(request.user, request.GET.get("nguon", ""), choices)
    params = parameters(request)
    gop = request.GET.get("gop") == "1"   # Gộp theo ngày (ADR-042): mỗi ngày một dòng
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


@login_required
@require_POST
def thresholds(request):
    """Manager bộ phận sở hữu nguồn (hoặc Admin) đặt ngưỡng màu ba bậc (ADR-042 đợt 3): sai thứ tự,
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


@login_required
def legacy_redirect(request, export=False):
    """Giữ bookmark cũ và toàn bộ bộ lọc; quyền kiểm tại trang đích."""
    route = "bao_cao_tong_hop_xuat" if export else "bao_cao_tong_hop"
    query = request.GET.urlencode()
    return redirect(reverse(route) + ("?" + query if query else ""))
