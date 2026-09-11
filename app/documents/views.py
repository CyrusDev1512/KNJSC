"""Màn hình Tài liệu — FR-9.1 tới FR-9.5, ADR-017.

View chỉ nhận yêu cầu, kiểm quyền, gọi tầng dịch vụ, trả kết quả (điều cấm 2).
Mọi truy vấn đi qua `objects.in_scope(user)` (quy tắc 11).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.audit import record_denied
from core.constants import Rank
from core.exceptions import BusinessError, OutOfScopeError
from core.permissions import assert_rank
from org.models import Department

from .forms import TaiLenForm
from .models import Document, DocumentCategory
from .services import document_service


@login_required
def tai_lieu(request):
    """Bookmark cũ mở tab tài liệu, giữ bộ lọc và phân trang."""
    from django.urls import reverse
    params = request.GET.copy()
    params['tab'] = 'documents'
    return redirect(reverse('bieu_mau') + '?' + params.urlencode())


@login_required
def tai_lieu_tai_len(request):
    """Tải tệp hoặc thêm liên kết — Manager trở lên (FR-9.2)."""
    request.nav_current = "bieu_mau"
    assert_rank(request.user, Rank.MANAGER, request)
    cac_muc = DocumentCategory.objects.in_scope(request.user).select_related("department")
    form = TaiLenForm(request.POST or None, request.FILES or None, cac_muc=cac_muc)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        try:
            doc = document_service.upload_document(
                title=d["title"], category=d["category"], upload=d.get("file"),
                link=d.get("link", ""), description=d.get("description", ""),
                actor=request.user, request=request,
            )
            messages.success(request, f"Đã thêm tài liệu {doc.title}.")
            return redirect("tai_lieu")
        except BusinessError as loi:
            messages.error(request, str(loi))
    return render(request, "documents/tai_lieu_tai_len.html", {"form": form})


@login_required
@require_POST
def tai_lieu_muc_moi(request):
    """Thêm mục — Manager cho bộ phận mình, Admin cả mục toàn công ty (FR-9.1)."""
    assert_rank(request.user, Rank.MANAGER, request)
    ma_bp = request.POST.get("department", "").strip()
    if ma_bp and not ma_bp.isdigit():
        raise Http404
    bo_phan = get_object_or_404(Department, pk=ma_bp) if ma_bp else None
    try:
        muc = document_service.create_category(
            name=request.POST.get("name", ""), department=bo_phan,
            actor=request.user, request=request,
        )
        messages.success(request, f"Đã thêm mục {muc.name}.")
    except BusinessError as loi:
        messages.error(request, str(loi))
    return redirect("tai_lieu")


@login_required
def tai_lieu_tai(request, pk):
    """Tải về qua view có kiểm quyền; tài liệu chỉ có liên kết thì chuyển tới liên kết — FR-9.3."""
    doc = get_object_or_404(
        Document.objects.in_scope(request.user).select_related("category"), pk=pk,
    )
    if doc.la_lien_ket:
        document_service.log_download(doc, actor=request.user, request=request)
        return redirect(doc.link)
    duong_dan = document_service.absolute_path(doc)
    if duong_dan is None or not duong_dan.exists():
        messages.error(request, "Tệp không còn trên máy chủ. Báo người vận hành kiểm thư mục storage/tai-lieu.")
        return redirect("tai_lieu")
    document_service.log_download(doc, actor=request.user, request=request)
    return FileResponse(open(duong_dan, "rb"), as_attachment=True, filename=doc.file_name)


@login_required
@require_POST
def tai_lieu_go(request, pk):
    """Gỡ tài liệu — người tải, Manager của bộ phận đó, Admin (FR-9.4)."""
    doc = get_object_or_404(
        Document.objects.in_scope(request.user).select_related("category"), pk=pk,
    )
    if not document_service.can_manage_document(request.user, doc):
        record_denied(request.user, request.path, request)
        raise OutOfScopeError("Bạn không có quyền gỡ tài liệu này.")
    document_service.delete_document(doc, actor=request.user, request=request)
    messages.success(request, f"Đã gỡ tài liệu {doc.title}.")
    return redirect("tai_lieu")
