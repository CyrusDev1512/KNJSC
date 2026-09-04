"""View của core.

View chỉ nhận yêu cầu, kiểm quyền, gọi tầng dịch vụ, trả kết quả. Quy tắc
nghiệp vụ nằm ở services/, không nằm ở đây (điều cấm 2).
"""
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from .constants import JOB_FINISHED, AuditAction, JobStatus, Rank, rank_level
from .forms import LoginForm
from .models import AuditLog, BackgroundJob
from .navigation import NAVIGATION
from .pagination import PAGE_SIZES, page_size, paginate
from .permissions import assert_rank
from .services import auth_service


class LoginView(auth_views.LoginView):
    template_name = "registration/login.html"
    form_class = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        auth_service.note_successful_login(self.request.user, self.request)
        # Ghi mốc phiên để middleware phát hiện được khi quyền bị đổi (P4)
        profile = getattr(self.request.user, "profile", None)
        if profile is not None:
            self.request.session["auth_epoch"] = profile.session_epoch
        return response

    def form_invalid(self, form):
        auth_service.note_failed_login(form.data.get("username", ""), self.request)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["het_phien"] = self.request.GET.get("het_phien") == "1"
        ctx["doi_quyen"] = self.request.GET.get("doi_quyen") == "1"
        return ctx


class LogoutView(auth_views.LogoutView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            auth_service.note_logout(request.user, request)
        return super().dispatch(request, *args, **kwargs)


class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = "registration/password_change.html"
    success_url = reverse_lazy("tong_quan")

    def form_valid(self, form):
        response = super().form_valid(form)
        profile = getattr(self.request.user, "profile", None)
        if profile is not None and profile.must_change_password:
            profile.must_change_password = False
            profile.save(update_fields=["must_change_password"])
        return response


@login_required
def nhat_ky(request):
    """Nhật ký hoạt động.

    Chỉ đọc, không có nút sửa và nút xoá (BR-6). Mỗi người chỉ xem được
    hoạt động của những người nằm trong phạm vi của mình.
    """
    request.nav_current = "nhat_ky"
    assert_rank(request.user, Rank.MANAGER, request)

    ds = AuditLog.objects.in_scope(request.user).select_related("actor")

    hanh_dong = request.GET.get("hanh_dong", "")
    if hanh_dong:
        ds = ds.filter(action=hanh_dong)
    tim = request.GET.get("tim", "").strip()
    if tim:
        ds = ds.filter(
            Q(actor_label__icontains=tim) | Q(target_id__icontains=tim)
        )

    trang = paginate(request, ds)
    return render(request, "core/nhat_ky.html", {
        "page_obj": trang, "trang": trang,
        "moi_trang": page_size(request), "cac_co_trang": PAGE_SIZES,
        "ten_don_vi": "bản ghi",
        "hanh_dong": hanh_dong, "tim": tim,
        "cac_hanh_dong": AuditAction.choices,
    })


@login_required
def ma_tran_quyen(request):
    """Bảng tra "ai xem được gì", chỉ đọc.

    Sinh thẳng từ `navigation.NAVIGATION` và `constants.RANK_LEVEL` nên không
    bao giờ lệch với mã thật — sửa quyền ở một chỗ là bảng này đổi theo.
    """
    request.nav_current = "ma_tran_quyen"
    assert_rank(request.user, Rank.MANAGER, request)

    cac_cap = list(Rank.choices)
    cac_hang = []
    for nhom in NAVIGATION:
        cac_hang.append({"la_nhom": True, "nhan": nhom.label})
        for muc in nhom.items:
            can = rank_level(muc.min_rank)
            cac_hang.append({
                "la_nhom": False, "nhan": muc.label, "duong_dan": muc.url_name,
                "cac_o": [rank_level(ma) >= can for ma, _ in cac_cap],
            })

    return render(request, "core/ma_tran_quyen.html", {
        "cac_cap": cac_cap, "cac_hang": cac_hang,
    })


# ══ TÁC VỤ NỀN — Giai đoạn 7 ═══════════════════════════════════════

def _tac_vu_cua_toi(request, pk):
    """Tác vụ trong phạm vi người xem. Của người khác → 404, không phải rỗng."""
    return get_object_or_404(
        BackgroundJob.objects.in_scope(request.user).select_related("created_by"), pk=pk,
    )


@login_required
def tac_vu(request):
    """Danh sách tác vụ nền của mình; Admin thấy hết để biết hàng đợi có kẹt không."""
    request.nav_current = "tac_vu"
    ds = BackgroundJob.objects.in_scope(request.user).select_related("created_by")
    trang_thai = request.GET.get("trang_thai", "")
    if trang_thai:
        ds = ds.filter(status=trang_thai)
    trang = paginate(request, ds)
    return render(request, "core/tac_vu.html", {
        "page_obj": trang, "trang": trang,
        "moi_trang": page_size(request), "cac_co_trang": PAGE_SIZES,
        "ten_don_vi": "tác vụ", "trang_thai": trang_thai,
        "cac_trang_thai": JobStatus.choices,
        "so_ket": BackgroundJob.objects.in_scope(request.user).filter(status=JobStatus.STALE).count(),
    })


@login_required
def tac_vu_xem(request, pk):
    """Một tác vụ: tiến độ, kết quả, danh sách dòng lỗi, nút tải tệp."""
    request.nav_current = "tac_vu"
    job = _tac_vu_cua_toi(request, pk)
    return render(request, "core/tac_vu_xem.html", {"job": job, "da_xong": job.is_finished})


@login_required
def tac_vu_tien_do(request, pk):
    """Mảnh HTML cho HTMX hỏi lại mỗi 2 giây. Xong thì mảnh không còn
    `hx-trigger` nên trình duyệt tự ngừng hỏi."""
    job = _tac_vu_cua_toi(request, pk)
    return render(request, "core/_tac_vu_tien_do.html", {"job": job, "da_xong": job.is_finished})


@login_required
def tac_vu_tai(request, pk):
    """Tải tệp kết quả. Tệp đã bị dọn sau 24 giờ thì nói rõ, không trả 500."""
    job = _tac_vu_cua_toi(request, pk)
    duong_dan = Path(settings.STORAGE_DIR) / job.result_path if job.result_path else None
    if job.status != JobStatus.DONE or duong_dan is None or not duong_dan.exists():
        messages.error(request, "Tệp đã quá 24 giờ và được dọn, hoặc tác vụ chưa xong. Hãy xuất lại.")
        return redirect("tac_vu_xem", pk=pk)
    ten = job.summary.get("file_name") or duong_dan.name
    return FileResponse(open(duong_dan, "rb"), as_attachment=True, filename=ten)
