"""Màn hình Công việc — FR-11.1 tới FR-11.5, ADR-015.

View chỉ nhận yêu cầu, kiểm quyền, gọi tầng dịch vụ, trả kết quả (điều cấm 2).
Mọi truy vấn đi qua `objects.in_scope(user)` (quy tắc 11).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.audit import record_denied
from core.exceptions import BusinessError, OutOfScopeError
from core.pagination import PAGE_SIZES, page_size, paginate

from .constants import PRIORITY_CHIP, STATUS_CHIP, TaskPriority, TaskStatus
from .forms import CongViecForm
from .services import task_service


def _phan_trang(request, queryset, ten_don_vi="việc"):
    trang = paginate(request, queryset)
    return {
        "page_obj": trang, "trang": trang,
        "moi_trang": page_size(request), "cac_co_trang": PAGE_SIZES,
        "ten_don_vi": ten_don_vi, "tham_so": "trang", "tham_so_co": "moi_trang",
    }


def _dong(user, task):
    """Bối cảnh của một dòng bảng — dùng cả ở danh sách lẫn mảnh HTMX."""
    return {
        "t": task,
        "lop_tt": STATUS_CHIP.get(task.status, "chip-nhat"),
        "lop_ut": PRIORITY_CHIP.get(task.priority, "chip-nhat"),
        "duoc_doi": task_service.can_change_status(user, task),
        "cac_buoc": task_service.next_statuses(task),
    }


def _viec_trong_pham_vi(request, pk):
    return get_object_or_404(task_service.tasks_of(request.user), pk=pk)


@login_required
def cong_viec(request):
    """Danh sách việc: tab Của tôi / Trong phạm vi, lọc trạng thái, người, ưu tiên — FR-11.3, FR-11.4."""
    request.nav_current = "cong_viec"
    tab = request.GET.get("tab", "cua_toi")
    if tab not in ("cua_toi", "pham_vi"):
        tab = "cua_toi"
    trang_thai = request.GET.get("trang_thai", "")
    uu_tien = request.GET.get("uu_tien", "")
    nguoi = request.GET.get("nguoi", "").strip()

    ds = task_service.tasks_of(request.user)
    if tab == "cua_toi":
        ds = ds.filter(Q(assignee=request.user) | Q(created_by=request.user))
    if trang_thai in TaskStatus.values:
        ds = ds.filter(status=trang_thai)
    else:
        trang_thai = ""
    if uu_tien in TaskPriority.values:
        ds = ds.filter(priority=uu_tien)
    else:
        uu_tien = ""
    if nguoi.isdigit():
        ds = ds.filter(assignee_id=int(nguoi))
    else:
        nguoi = ""
    ds = ds.order_by("-created_at")

    qs_loc = f"&tab={tab}"
    for ten, gia_tri in (("trang_thai", trang_thai), ("uu_tien", uu_tien), ("nguoi", nguoi)):
        if gia_tri:
            qs_loc += f"&{ten}={gia_tri}"

    boi_canh = _phan_trang(request, ds)
    boi_canh.update({
        "tab": tab, "trang_thai": trang_thai, "uu_tien": uu_tien, "nguoi": nguoi,
        "qs_loc": qs_loc,
        "cac_trang_thai": TaskStatus.choices, "cac_uu_tien": TaskPriority.choices,
        "cac_nguoi": task_service.assignable_users(request.user),
        "cac_dong": [_dong(request.user, t) for t in boi_canh["page_obj"]],
    })
    return render(request, "taskboard/cong_viec.html", boi_canh)


@login_required
def cong_viec_moi(request):
    """Tạo việc; không chọn người làm thì tự nhận — FR-11.1."""
    request.nav_current = "cong_viec"
    form = CongViecForm(request.POST or None, nguoi=task_service.assignable_users(request.user))
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        try:
            viec = task_service.create_task(
                title=d["title"], description=d["description"], assignee=d["assignee"],
                priority=d["priority"], due_date=d["due_date"],
                actor=request.user, request=request,
            )
            messages.success(request, f"Đã tạo việc {viec.title}.")
            return redirect("cong_viec")
        except BusinessError as loi:
            messages.error(request, str(loi))
    return render(request, "taskboard/cong_viec_form.html", {
        "form": form, "tieu_de": "Tạo việc", "la_tao_moi": True,
    })


@login_required
def cong_viec_xem(request, pk):
    """Chi tiết một việc trong phạm vi, kèm nút chuyển trạng thái và biểu mẫu sửa."""
    request.nav_current = "cong_viec"
    viec = _viec_trong_pham_vi(request, pk)
    duoc_sua = task_service.can_edit(request.user, viec)
    form = None
    if duoc_sua:
        form = CongViecForm(
            initial={
                "title": viec.title, "description": viec.description,
                "assignee": viec.assignee, "priority": viec.priority, "due_date": viec.due_date,
            },
            nguoi=task_service.assignable_users(request.user),
        )
    boi_canh = _dong(request.user, viec)
    boi_canh.update({
        "form": form, "duoc_sua": duoc_sua,
        "duoc_go": task_service.can_delete(request.user, viec),
    })
    return render(request, "taskboard/cong_viec_xem.html", boi_canh)


@login_required
@require_POST
def cong_viec_sua(request, pk):
    """Sửa việc — người tạo hoặc Leader trở lên trong phạm vi."""
    viec = _viec_trong_pham_vi(request, pk)
    if not task_service.can_edit(request.user, viec):
        record_denied(request.user, request.path, request)
        raise OutOfScopeError("Bạn không có quyền sửa việc này.")
    form = CongViecForm(request.POST, nguoi=task_service.assignable_users(request.user))
    if form.is_valid():
        try:
            task_service.update_task(viec, form.cleaned_data, actor=request.user, request=request)
            messages.success(request, "Đã lưu việc.")
        except BusinessError as loi:
            messages.error(request, str(loi))
    else:
        messages.error(request, "Biểu mẫu chưa hợp lệ: " + "; ".join(
            f"{ten}: {' '.join(loi)}" for ten, loi in form.errors.items()))
    return redirect("cong_viec_xem", pk=pk)


@login_required
@require_POST
def cong_viec_trang_thai(request, pk):
    """Chuyển trạng thái. HTMX thì trả về đúng một dòng bảng; sai bước thì 400 kèm lý do — FR-11.2."""
    viec = _viec_trong_pham_vi(request, pk)
    if not task_service.can_change_status(request.user, viec):
        record_denied(request.user, request.path, request)
        raise OutOfScopeError("Bạn không có quyền đổi trạng thái việc này.")
    try:
        task_service.change_status(
            viec, request.POST.get("trang_thai", ""), actor=request.user, request=request,
        )
    except BusinessError as loi:
        if request.headers.get("HX-Request"):
            return HttpResponse(str(loi), status=400)
        messages.error(request, str(loi))
        return redirect("cong_viec_xem", pk=pk)
    if request.headers.get("HX-Request"):
        return render(request, "taskboard/_dong.html", _dong(request.user, viec))
    messages.success(request, f"Việc chuyển sang {viec.get_status_display()}.")
    return redirect(request.POST.get("ve") or "cong_viec")


@login_required
@require_POST
def cong_viec_go(request, pk):
    """Gỡ việc — người tạo hoặc Manager trở lên (FR-11.5)."""
    viec = _viec_trong_pham_vi(request, pk)
    if not task_service.can_delete(request.user, viec):
        record_denied(request.user, request.path, request)
        raise OutOfScopeError("Bạn không có quyền gỡ việc này.")
    task_service.delete_task(viec, actor=request.user, request=request)
    messages.success(request, f"Đã gỡ việc {viec.title}.")
    return redirect("cong_viec")
