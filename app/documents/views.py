"""Màn hình Tài liệu — FR-9.1 tới FR-9.5, ADR-015.

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
from core.pagination import PAGE_SIZES, filter_query, page_size, paginate
from core.permissions import assert_rank, has_rank, is_admin
from org.models import Department

from .forms import TaiLenForm
from .models import Document, DocumentCategory
from .services import document_service


def _phan_trang(request, queryset, ten_don_vi="tài liệu"):
    trang = paginate(request, queryset)
    return {
        "page_obj": trang, "trang": trang,
        "moi_trang": page_size(request), "cac_co_trang": PAGE_SIZES,
        "ten_don_vi": ten_don_vi, "tham_so": "trang", "tham_so_co": "moi_trang",
    }


def _bo_phan_tao_muc(user):
    """Bộ phận mà người này được tạo mục: Admin mọi bộ phận, Manager bộ phận mình."""
    if is_admin(user):
        return Department.objects.all()
    ho_so = getattr(user, "profile", None)
    if ho_so is None or ho_so.department_id is None:
        return Department.objects.none()
    return Department.objects.filter(pk=ho_so.department_id)


@login_required
def tai_lieu(request):
    """Danh sách tài liệu trong phạm vi, lọc theo mục và tiêu đề — FR-9.1, FR-9.3."""
    request.nav_current = "tai_lieu"
    cac_muc = list(document_service.categories_of(request.user))
    ds = document_service.documents_of(request.user)

    muc_chon = request.GET.get("muc", "").strip()
    tim = request.GET.get("tim", "").strip()
    muc_hien = None
    if muc_chon:
        # Mục ngoài phạm vi thì 404, không phải danh sách rỗng (quy tắc 8)
        muc_hien = next((m for m in cac_muc if str(m.pk) == muc_chon), None)
        if muc_hien is None:
            raise Http404
        ds = ds.filter(category=muc_hien)
    if tim:
        ds = ds.filter(title__icontains=tim)

    qs_loc = filter_query(muc=muc_hien.pk if muc_hien else "", tim=tim)

    boi_canh = _phan_trang(request, ds)
    boi_canh.update({
        "cac_muc": cac_muc, "muc_hien": muc_hien, "tim": tim, "qs_loc": qs_loc,
        "tong_tai_lieu": sum(m.so_tai_lieu for m in cac_muc),
        "duoc_tai_len": has_rank(request.user, Rank.MANAGER),
        "cac_bo_phan_muc": _bo_phan_tao_muc(request.user) if has_rank(request.user, Rank.MANAGER) else [],
        "la_admin": is_admin(request.user),
        "cac_dong": [
            (doc, document_service.can_manage_document(request.user, doc))
            for doc in boi_canh["page_obj"]
        ],
    })
    return render(request, "documents/tai_lieu.html", boi_canh)


@login_required
def tai_lieu_tai_len(request):
    """Tải tệp hoặc thêm liên kết — Manager trở lên (FR-9.2)."""
    request.nav_current = "tai_lieu"
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
        return redirect(doc.link)
    duong_dan = document_service.absolute_path(doc)
    if duong_dan is None or not duong_dan.exists():
        messages.error(request, "Tệp không còn trên máy chủ. Báo người vận hành kiểm thư mục storage/tai-lieu.")
        return redirect("tai_lieu")
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
