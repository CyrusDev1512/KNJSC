"""Màn hình Tài nguyên — FR-13.1 tới FR-13.4, ADR-015.

View chỉ nhận yêu cầu, kiểm quyền, gọi tầng dịch vụ, trả kết quả (điều cấm 2).
Danh mục là của toàn công ty (Q64): ai đăng nhập cũng xem cả danh sách;
thêm, sửa, gỡ và thêm mục là việc của Manager trở lên.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.constants import Rank
from core.exceptions import BusinessError
from core.pagination import filter_query, pagination_context
from core.permissions import assert_rank
from org.models import Department

from .constants import STATUS_CHIP, ResourceStatus
from .forms import TaiNguyenForm
from .models import Resource, ResourceCategory
from .services import resource_service


def _form(du_lieu=None, nguoi_giu=None, **initial):
    return TaiNguyenForm(
        du_lieu, initial=initial or None,
        cac_muc=ResourceCategory.objects.all(), nguoi=resource_service.holders(include=nguoi_giu),
        bo_phan=Department.objects.order_by("name"),
    )


@login_required
def tai_nguyen(request):
    """Danh sách chung, lọc theo mục, trạng thái, người giữ; tìm theo tên — FR-13.2."""
    request.nav_current = "tai_nguyen"
    cac_muc = list(resource_service.categories())
    ds = resource_service.resources_qs()

    muc_chon = request.GET.get("muc", "").strip()
    trang_thai = request.GET.get("trang_thai", "").strip()
    nguoi = request.GET.get("nguoi", "").strip()
    tim = request.GET.get("tim", "").strip()
    muc_hien = None
    if muc_chon:
        muc_hien = next((m for m in cac_muc if str(m.pk) == muc_chon), None)
        if muc_hien is None:
            raise Http404
        ds = ds.filter(category=muc_hien)
    if trang_thai in ResourceStatus.values:
        ds = ds.filter(status=trang_thai)
    else:
        trang_thai = ""
    cac_nguoi = list(resource_service.holders())
    if nguoi.isdigit():
        if not any(u.pk == int(nguoi) for u in cac_nguoi):
            raise Http404                    # người không có: từ chối, không phải danh sách rỗng (quy tắc 8)
        ds = ds.filter(holder_id=int(nguoi))
    else:
        nguoi = ""
    if tim:
        ds = ds.filter(name__icontains=tim)

    qs_loc = filter_query(
        muc=muc_hien.pk if muc_hien else "", trang_thai=trang_thai, nguoi=nguoi, tim=tim,
    )
    boi_canh = pagination_context(request, ds, "tài nguyên")
    boi_canh.update({
        "cac_muc": cac_muc, "muc_hien": muc_hien, "trang_thai": trang_thai, "nguoi": nguoi,
        "tim": tim, "qs_loc": qs_loc,
        "tong_tai_nguyen": sum(m.so_tai_nguyen for m in cac_muc),
        "cac_trang_thai": ResourceStatus.choices,
        "cac_nguoi": cac_nguoi,
        "duoc_sua": resource_service.can_manage(request.user),
        "cac_dong": [(tn, STATUS_CHIP.get(tn.status, "chip-nhat")) for tn in boi_canh["page_obj"]],
    })
    return render(request, "resources/tai_nguyen.html", boi_canh)


@login_required
def tai_nguyen_moi(request):
    """Thêm tài nguyên — Manager trở lên (FR-13.3)."""
    request.nav_current = "tai_nguyen"
    assert_rank(request.user, Rank.MANAGER, request)
    form = _form(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        try:
            tn = resource_service.create_resource(
                category=d["category"], name=d["name"], status=d["status"],
                holder=d.get("holder"), department=d.get("department"),
                link=d.get("link", ""), note=d.get("note", ""),
                actor=request.user, request=request,
            )
            messages.success(request, f"Đã thêm {tn.name} vào mục {tn.category.name}.")
            return redirect("tai_nguyen")
        except BusinessError as loi:
            messages.error(request, str(loi))
    return render(request, "resources/tai_nguyen_form.html", {"form": form, "tn": None})


@login_required
def tai_nguyen_sua(request, pk):
    """Sửa tài nguyên — Manager trở lên; nhật ký ghi trường đổi (FR-13.3)."""
    request.nav_current = "tai_nguyen"
    assert_rank(request.user, Rank.MANAGER, request)
    tn = get_object_or_404(resource_service.resources_qs(), pk=pk)
    form = _form(
        request.POST or None, nguoi_giu=tn.holder_id,
        category=tn.category_id, name=tn.name, status=tn.status, holder=tn.holder_id,
        department=tn.department_id, link=tn.link, note=tn.note,
    )
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        try:
            resource_service.update_resource(
                tn, actor=request.user, request=request,
                category=d["category"], name=d["name"], status=d["status"],
                holder=d.get("holder"), department=d.get("department"),
                link=d.get("link", ""), note=d.get("note", ""),
            )
            messages.success(request, f"Đã lưu {tn.name}.")
            return redirect("tai_nguyen")
        except BusinessError as loi:
            messages.error(request, str(loi))
    return render(request, "resources/tai_nguyen_form.html", {"form": form, "tn": tn})


@login_required
@require_POST
def tai_nguyen_go(request, pk):
    """Gỡ tài nguyên — Manager trở lên, xoá mềm (FR-13.3)."""
    assert_rank(request.user, Rank.MANAGER, request)
    tn = get_object_or_404(Resource.objects, pk=pk)
    resource_service.delete_resource(tn, actor=request.user, request=request)
    messages.success(request, f"Đã gỡ {tn.name}.")
    return redirect("tai_nguyen")


@login_required
@require_POST
def tai_nguyen_muc_moi(request):
    """Thêm mục — Manager trở lên (FR-13.1)."""
    assert_rank(request.user, Rank.MANAGER, request)
    try:
        muc = resource_service.create_category(
            name=request.POST.get("name", ""), actor=request.user, request=request,
        )
        messages.success(request, f"Đã thêm mục {muc.name}.")
    except BusinessError as loi:
        messages.error(request, str(loi))
    return redirect("tai_nguyen")
