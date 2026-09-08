"""Màn hình Bảng tin — FR-10.1 tới FR-10.6, ADR-017.

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
from core.htmx import is_htmx
from core.identity import display_name
from core.pagination import pagination_context

from .constants import BODY_MAX, COMMENT_MAX
from .services import post_service


def _bai_hoac_404(request, pk):
    bai = post_service.feed_qs(request.user).filter(pk=pk).first()
    if bai is None:
        raise Http404
    return bai


def _gan_quyen(user, cac_bai):
    """Mỗi bài biết người đang xem có gỡ được nó không — template không tự suy."""
    for bai in cac_bai:
        bai.duoc_go = post_service.can_delete_post(user, bai)
    return cac_bai


def _binh_luan(request, bai, loi="", truoc=None, oob=False):
    """Bối cảnh mảnh bình luận. `oob=True` khi trả lời HTMX: kèm hai phần tử
    thay tại chỗ (số bình luận ở đầu bài và ở thẻ) để trang không lệch số."""
    cac, con_cu = post_service.comments_of(bai, truoc=truoc)
    for bl in cac:
        bl.duoc_go = post_service.can_delete_comment(request.user, bl)
    return {
        "bai": bai, "cac_binh_luan": cac, "con_cu": con_cu,
        "so_binh_luan": post_service.comment_count(bai),
        "comment_max": COMMENT_MAX, "loi": loi, "oob": oob,
    }


def _trang_bang_tin(request, body_cu=""):
    """Trang Bảng tin; `body_cu` giữ lại bài đang gõ khi đăng lỗi."""
    boi_canh = pagination_context(request, post_service.feed_qs(request.user), "bài")
    trang = boi_canh["trang"]
    trang.object_list = _gan_quyen(request.user, list(trang.object_list))
    boi_canh.update(post_service.sidebar(request.user))
    boi_canh.update({
        "duoc_ghim": post_service.can_moderate(request.user), "body_max": BODY_MAX,
        "body_cu": body_cu,
    })
    return render(request, "feed/bang_tin.html", boi_canh)


@login_required
def bang_tin(request):
    """Bài mới nhất, ghim đứng đầu, phân trang 25; thanh bên — FR-10.1, FR-10.5."""
    request.nav_current = "bang_tin"
    return _trang_bang_tin(request)


@login_required
@require_POST
def bang_tin_dang(request):
    """Đăng bài — FR-10.1. Lỗi thì hiện lại trang với bài đang gõ, không mất chữ."""
    request.nav_current = "bang_tin"
    body = request.POST.get("body", "")
    try:
        post_service.create_post(body=body, actor=request.user, request=request)
        messages.success(request, "Đã đăng lên Bảng tin.")
    except BusinessError as loi:
        messages.error(request, str(loi))
        return _trang_bang_tin(request, body_cu=body)
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
    if not is_htmx(request):
        return redirect("bang_tin_xem", pk=bai.pk)
    return render(request, "feed/_thich.html", {
        "bai": bai, "da_thich": da_thich, "so_thich": post_service.like_count(bai),
    })


@login_required
@require_http_methods(["GET", "POST"])
def bang_tin_binh_luan(request, pk):
    """GET: mảnh bình luận của bài (`truoc=<mã>` lấy trang cũ hơn); POST: thêm bình luận rồi trả mảnh (HTMX) hoặc quay về bài — FR-10.2."""
    bai = _bai_hoac_404(request, pk)
    loi = ""
    if request.method == "GET" and request.GET.get("truoc", "").isdigit():
        return render(request, "feed/_binh_luan_cu.html",
                      _binh_luan(request, bai, truoc=int(request.GET["truoc"])))
    if request.method == "POST":
        try:
            post_service.add_comment(
                bai, body=request.POST.get("body", ""), actor=request.user, request=request,
            )
        except BusinessError as e:
            loi = str(e)
        if not is_htmx(request):
            if loi:
                messages.error(request, loi)
            return redirect("bang_tin_xem", pk=bai.pk)
        return render(request, "feed/_binh_luan.html", _binh_luan(request, bai, loi, oob=True))
    return render(request, "feed/_binh_luan.html", _binh_luan(request, bai, loi))


@login_required
@require_POST
def bang_tin_ghim(request, pk):
    """Ghim hoặc gỡ ghim — Manager trở lên (FR-10.3)."""
    bai = _bai_hoac_404(request, pk)
    if not post_service.can_moderate(request.user):
        record_denied(request.user, request.path, request)
        raise OutOfScopeError("Chỉ quản lý trở lên ghim được bài.")
    # Form gửi rõ ý muốn (ghim=1 hay 0) để hai quản lý bấm trên trang cũ không
    # làm ngược ý nhau; không gửi thì đảo trạng thái như trước
    muon = request.POST.get("ghim")
    muon_ghim = (not bai.is_pinned) if muon is None else muon == "1"
    if muon_ghim == bai.is_pinned:
        messages.info(request, "Bài đã ở đúng trạng thái đó rồi.")
    elif muon_ghim:
        post_service.pin_post(bai, actor=request.user, request=request)
        messages.success(request, "Đã ghim bài lên đầu Bảng tin.")
    else:
        post_service.unpin_post(bai, actor=request.user, request=request)
        messages.success(request, "Đã gỡ ghim.")
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
