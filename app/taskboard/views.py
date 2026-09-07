"""Màn hình Công việc — FR-11.1 tới FR-11.5, ADR-015.

View chỉ nhận yêu cầu, kiểm quyền, gọi tầng dịch vụ, trả kết quả (điều cấm 2).
Mọi truy vấn đi qua `objects.in_scope(user)` (quy tắc 11).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from core.audit import record_denied
from core.exceptions import BusinessError, OutOfScopeError
from core.htmx import is_htmx
from core.pagination import filter_query, pagination_context

from .constants import OPEN_STATUSES, PRIORITY_CHIP, STATUS_CHIP, TaskPriority, TaskStatus
from .forms import CongViecForm
from .services import task_service


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
    qua_han = request.GET.get("qua_han") == "1"
    sap = request.GET.get("sap", "")

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
    if qua_han:
        ds = ds.filter(due_date__lt=timezone.localdate(), status__in=OPEN_STATUSES)
    if sap == "han":
        ds = ds.order_by(F("due_date").asc(nulls_last=True), "-created_at")   # chỉ mục due_date có việc
    else:
        sap = ""
        ds = ds.order_by("-created_at")

    qs_loc = filter_query(
        tab=tab, trang_thai=trang_thai, uu_tien=uu_tien, nguoi=nguoi,
        qua_han="1" if qua_han else "", sap=sap,
    )

    boi_canh = pagination_context(request, ds, "việc")
    boi_canh.update({
        "tab": tab, "trang_thai": trang_thai, "uu_tien": uu_tien, "nguoi": nguoi,
        "qua_han": qua_han, "sap": sap, "qs_loc": qs_loc,
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


def _trang_xem(request, viec, form=None):
    """Trang chi tiết; `form` đã điền (kể cả lỗi) thì hiện đúng trạng thái đó."""
    duoc_sua = task_service.can_edit(request.user, viec)
    if duoc_sua and form is None:
        form = CongViecForm(
            initial={
                "title": viec.title, "description": viec.description,
                "assignee": viec.assignee, "priority": viec.priority, "due_date": viec.due_date,
            },
            nguoi=task_service.assignable_users(request.user), sua=True,
        )
    boi_canh = _dong(request.user, viec)
    boi_canh.update({
        "form": form if duoc_sua else None, "duoc_sua": duoc_sua,
        "duoc_go": task_service.can_delete(request.user, viec),
    })
    return render(request, "taskboard/cong_viec_xem.html", boi_canh)


@login_required
def cong_viec_xem(request, pk):
    """Chi tiết một việc trong phạm vi, kèm nút chuyển trạng thái và biểu mẫu sửa."""
    request.nav_current = "cong_viec"
    return _trang_xem(request, _viec_trong_pham_vi(request, pk))


@login_required
@require_POST
def cong_viec_sua(request, pk):
    """Sửa việc — người tạo hoặc Leader trở lên trong phạm vi."""
    viec = _viec_trong_pham_vi(request, pk)
    if not task_service.can_edit(request.user, viec):
        record_denied(request.user, request.path, request)
        raise OutOfScopeError("Bạn không có quyền sửa việc này.")
    request.nav_current = "cong_viec"
    form = CongViecForm(request.POST, nguoi=task_service.assignable_users(request.user), sua=True)
    if form.is_valid():
        try:
            task_service.update_task(viec, form.cleaned_data, actor=request.user, request=request)
            messages.success(request, "Đã lưu việc.")
            return redirect("cong_viec_xem", pk=pk)
        except BusinessError as loi:
            messages.error(request, str(loi))
    else:
        messages.error(request, "Biểu mẫu chưa hợp lệ — xem lỗi ở từng ô.")
    # Lỗi thì hiện lại trang với những gì đã gõ, lỗi ngay dưới ô
    return _trang_xem(request, viec, form=form)


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
        if is_htmx(request):
            # Chữ thường, không phải HTML: base.html hiện nguyên văn trong hộp báo lỗi
            return HttpResponse(str(loi), status=400, content_type="text/plain; charset=utf-8")
        messages.error(request, str(loi))
        return redirect("cong_viec_xem", pk=pk)
    if is_htmx(request):
        return render(request, "taskboard/_dong.html", _dong(request.user, viec))
    messages.success(request, f"Việc chuyển sang {viec.get_status_display()}.")
    ve = request.POST.get("ve", "")
    if not url_has_allowed_host_and_scheme(ve, allowed_hosts={request.get_host()}):
        ve = reverse("cong_viec")             # chỉ quay về trong hệ thống, không chuyển ra ngoài
    return redirect(ve)


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
