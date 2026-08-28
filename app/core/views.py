"""View của core.

View chỉ nhận yêu cầu, kiểm quyền, gọi tầng dịch vụ, trả kết quả. Quy tắc
nghiệp vụ nằm ở services/, không nằm ở đây (điều cấm 2).
"""
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse_lazy

from .constants import AuditAction, Rank
from .forms import LoginForm
from .models import AuditLog
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
