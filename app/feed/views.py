"""Màn hình Bảng tin — FR-10.1 tới FR-10.6, ADR-015.

View chỉ nhận yêu cầu, kiểm quyền, gọi tầng dịch vụ, trả kết quả (điều cấm 2).
Bảng tin là của toàn công ty: ai đăng nhập cũng thấy mọi bài (FR-10.1), nên
không có phạm vi; ai được ghim, được gỡ thì hỏi tầng dịch vụ.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from core.audit import record_denied
from core.exceptions import BusinessError, OutOfScopeError
from core.identity import display_name
from core.pagination import PAGE_SIZES, page_size, paginate

from .constants import BODY_MAX, COMMENT_MAX
from .services import post_service


def _phan_trang(request, queryset, ten_don_vi="bài"):
    trang = paginate(request, queryset)
    return {
        "page_obj": trang, "trang": trang,
        "moi_trang": page_size(request), "cac_co_trang": PAGE_SIZES,
        "ten_don_vi": ten_don_vi, "tham_so": "trang", "tham_so_co": "moi_trang",
    }


def _bai_hoac_404(request, pk):
    bai = post_service.feed_qs(request.user).filter(pk=pk).first()
    if bai is None:
        raise Http404
    return bai


def _la_htmx(request):
    return request.headers.get("HX-Request") == "true"


def _gan_quyen(user, cac_bai):
    """Mỗi bài biết người đang xem có gỡ được nó không — template không tự suy."""
    for bai in cac_bai:
        bai.duoc_go = post_service.can_delete_post(user, bai)
    return cac_bai


def _binh_luan(request, bai, loi=""):
    cac = list(post_service.comments_of(bai))
    for bl in cac:
        bl.duoc_go = post_service.can_delete_comment(request.user, bl)
    return {"bai": bai, "cac_binh_luan": cac, "comment_max": COMMENT_MAX, "loi": loi}


@login_required
def bang_tin(request):
    """Bài mới nhất, ghim đứng đầu, phân trang 25; thanh bên — FR-10.1, FR-10.5."""
    request.nav_current = "bang_tin"
    boi_canh = _phan_trang(request, post_service.feed_qs(request.user))
    trang = boi_canh["trang"]
    trang.object_list = _gan_quyen(request.user, list(trang.object_list))
    boi_canh.update(post_service.sidebar(request.user))
    boi_canh.update({"duoc_ghim": post_service.can_moderate(request.user), "body_max": BODY_MAX})
    return render(request, "feed/bang_tin.html", boi_canh)


@login_required
@require_POST
def bang_tin_dang(request):
    """Đăng bài — FR-10.1."""
    try:
        post_service.create_post(body=request.POST.get("body", ""), actor=request.user, request=request)
        messages.success(request, "Đã đăng lên Bảng tin.")
    except BusinessError as loi:
        messages.error(request, str(loi))
    return redirect("bang_tin")


@login_required
def bang_tin_xem(request, pk):
    """Một bài kèm bình luận."""
    request.nav_current = "bang_tin"
    bai = _bai_hoac_404(request, pk)
    _gan_quyen(request.user, [bai])
    boi_canh = _binh_luan(request, bai)
    boi_canh.update(post_service.sidebar(request.user))
    boi_canh.update({
        "da_thich": bai.da_thich, "so_thich": bai.so_thich, "so_binh_luan": bai.so_binh_luan,
        "duoc_ghim": post_service.can_moderate(request.user),
        "ten_tac_gia": display_name(bai.author) if bai.author_id else "KN JSC",
    })
    return render(request, "feed/bang_tin_xem.html", boi_canh)


@login_required
@require_POST
def bang_tin_thich(request, pk):
    """Thích hoặc bỏ thích — HTMX nhận về đúng nút mới (FR-10.2)."""
    bai = _bai_hoac_404(request, pk)
    da_thich = post_service.toggle_like(bai, actor=request.user, request=request)
    if not _la_htmx(request):
        return redirect("bang_tin_xem", pk=bai.pk)
    return render(request, "feed/_thich.html", {
        "bai": bai, "da_thich": da_thich, "so_thich": post_service.like_count(bai),
    })


@login_required
@require_http_methods(["GET", "POST"])
def bang_tin_binh_luan(request, pk):
    """GET: mảnh bình luận của bài; POST: thêm bình luận rồi trả mảnh (HTMX) hoặc quay về bài — FR-10.2."""
    bai = _bai_hoac_404(request, pk)
    loi = ""
    if request.method == "POST":
        try:
            post_service.add_comment(
                bai, body=request.POST.get("body", ""), actor=request.user, request=request,
            )
        except BusinessError as e:
            loi = str(e)
        if not _la_htmx(request):
            if loi:
                messages.error(request, loi)
            return redirect("bang_tin_xem", pk=bai.pk)
    return render(request, "feed/_binh_luan.html", _binh_luan(request, bai, loi))


@login_required
@require_POST
def bang_tin_ghim(request, pk):
    """Ghim hoặc gỡ ghim — Manager trở lên (FR-10.3)."""
    bai = _bai_hoac_404(request, pk)
    if not post_service.can_moderate(request.user):
        record_denied(request.user, request.path, request)
        raise OutOfScopeError("Chỉ quản lý trở lên ghim được bài.")
    if bai.is_pinned:
        post_service.unpin_post(bai, actor=request.user, request=request)
        messages.success(request, "Đã gỡ ghim.")
    else:
        post_service.pin_post(bai, actor=request.user, request=request)
        messages.success(request, "Đã ghim bài lên đầu Bảng tin.")
    return redirect("bang_tin")


@login_required
@require_POST
def bang_tin_go(request, pk):
    """Gỡ bài — tác giả hoặc Manager trở lên; xoá mềm (FR-10.3)."""
    bai = _bai_hoac_404(request, pk)
    if not post_service.can_delete_post(request.user, bai):
        record_denied(request.user, request.path, request)
        raise OutOfScopeError("Bạn chỉ gỡ được bài của mình.")
    post_service.delete_post(bai, actor=request.user, request=request)
    messages.success(request, "Đã gỡ bài.")
    return redirect("bang_tin")


@login_required
@require_POST
def bang_tin_binh_luan_go(request, pk):
    """Gỡ bình luận — người viết hoặc Manager trở lên."""
    bl = post_service.comment_by_pk(pk)
    if bl is None:
        raise Http404
    if not post_service.can_delete_comment(request.user, bl):
        record_denied(request.user, request.path, request)
        raise OutOfScopeError("Bạn chỉ gỡ được bình luận của mình.")
    post_service.delete_comment(bl, actor=request.user, request=request)
    return redirect("bang_tin_xem", pk=bl.post_id)
