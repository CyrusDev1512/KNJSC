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
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from .constants import AuditAction, JobStatus, Rank, rank_level
from .forms import LoginForm
from .models import AuditLog, BackgroundJob
from .navigation import NAVIGATION
from .pagination import PAGE_SIZES, page_size, paginate
from .permissions import assert_admin, assert_django_admin
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
        auth_service.note_failed_login(form.data.get("username", ""), self.request, locked_user=form.locked_user)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["het_phien"] = self.request.GET.get("het_phien") == "1"
        ctx["doi_quyen"] = self.request.GET.get("doi_quyen") == "1"
        return ctx


class LogoutView(auth_views.LogoutView):
    def post(self, request, *args, **kwargs):
        # Ghi ở post(), không ở dispatch(): GET trả 405 mà không đăng xuất, không được để lại dòng đăng xuất giả
        # trong nhật ký không sửa được (BR-6, TL-93)
        if request.user.is_authenticated:
            auth_service.note_logout(request.user, request)
        return super().post(request, *args, **kwargs)


def quan_tri_dang_nhap(request):
    """`/quan-tri/login/` — trang quản trị Django dùng chung cửa đăng nhập của hệ thống (TL-93): không có form,
    không bao giờ kiểm mật khẩu, nên khoá tạm 5 lần sai, nhật ký và mốc phiên (P4) của `/dang-nhap/` áp cho cả
    quản trị viên. Người đã đăng nhập mà không phải quản trị viên nhận 403 có nhật ký — chuyển về `/dang-nhap/`
    thì LoginView (redirect_authenticated_user) đẩy lại đây, thành vòng chuyển hướng."""
    from django.contrib import admin
    from django.contrib.auth import REDIRECT_FIELD_NAME
    from django.contrib.auth.views import redirect_to_login
    from django.urls import reverse

    if not request.user.is_authenticated:
        return redirect_to_login(request.GET.get(REDIRECT_FIELD_NAME) or reverse("admin:index"))
    assert_django_admin(request.user, request)
    return redirect("admin:index")


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

    Chỉ Admin mở được; chỉ đọc, không sửa hoặc xoá (BR-6, quyết định 25.09).
    """
    request.nav_current = "nhat_ky"
    assert_admin(request.user, request)

    ds = AuditLog.objects.in_scope(request.user).select_related("actor", "actor__profile")

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
    assert_admin(request.user, request)

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
    """Danh sách vận hành hệ thống chỉ dành cho Admin."""
    request.nav_current = "tac_vu"
    assert_admin(request.user, request)
    ds = BackgroundJob.objects.in_scope(request.user).select_related("created_by", "created_by__profile")
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
    from forms_builder.services.export_service import check_download
    from core.exceptions import BusinessError
    try:
        check_download(job, request.user)
    except BusinessError as exc:
        messages.error(request, str(exc))
        return redirect('tac_vu_xem', pk=pk)
    duong_dan = Path(settings.STORAGE_DIR) / job.result_path if job.result_path else None
    if job.status != JobStatus.DONE or duong_dan is None or not duong_dan.exists():
        messages.error(request, "Tệp đã quá 24 giờ và được dọn, hoặc tác vụ chưa xong. Hãy xuất lại.")
        return redirect("tac_vu_xem", pk=pk)
    ten = job.summary.get("file_name") or duong_dan.name
    return FileResponse(open(duong_dan, "rb"), as_attachment=True, filename=ten)


def _wants_json(request):
    """Người gọi đợi JSON: fetch và htmx của hai khung KN CRM mang mã người mở trang (het-phien.js gắn X-KNJSC-User), hoặc
    thân gửi lên là JSON. Một luật cho lỗi mã bảo mật (ADR-053) và lỗi chưa gán bộ phận (TL-106); header chỉ để chọn
    dạng trả lời, không phải kiểm quyền."""
    from .middleware import HEADER_NGUOI_MO_TRANG

    return request.headers.get(HEADER_NGUOI_MO_TRANG) is not None or request.content_type == "application/json"


def csrf_failure(request, reason=""):
    """CSRF_FAILURE_VIEW. Yêu cầu từ trang KN CRM (fetch và htmx đều mang mã người mở trang) hay thân JSON nhận 403 JSON
    `code: "csrf"` để trang giữ nháp và báo đúng thay vì coi là mất quyền; trang đó lấy mã mới lúc gửi nên bấm Thử lại là
    được. Form HTML thường và htmx của KN ERP (không lấy mã mới, Thử lại vô ích) vẫn nhận trang 403 của Django như ADR-030
    (ADR-053)."""
    from django.views.csrf import csrf_failure as trang_mac_dinh

    from .middleware import PHIEN_CSRF

    if _wants_json(request):
        return JsonResponse({"error": PHIEN_CSRF, "code": "csrf"}, status=403)
    return trang_mac_dinh(request, reason=reason)


def permission_denied(request, exception=None):
    """handler403 của cả hai URLconf (knjsc/urls.py, knjsc/urls_bangtinh.py) — TL-106.

    Mọi lần từ chối khác đã tự ghi Từ chối ngay chỗ kiểm (core.permissions.assert_*, record_denied ở view); ghi lại ở
    đây là ghi đôi, mà bài quét POST đòi đúng một dòng. Riêng NoProfileError (Manager mất bộ phận, tài khoản chưa có hồ
    sơ — P0-9) nổ từ core.scope ở bất kỳ truy vấn có phạm vi nào và không chỗ nào ghi trước khi ném, nên ghi đúng một
    dòng ở đây, sau khi giao dịch của view đã huỷ. Người gọi đợi JSON (lưới KN CRM) nhận {error, code} để báo đúng lời;
    mở trang thường nhận trang 403 như cũ."""
    from django.views import defaults

    from .audit import record_denied
    from .exceptions import NoProfileError

    if isinstance(exception, NoProfileError):
        record_denied(getattr(request, "user", None), request.path, request)
        if _wants_json(request):
            return JsonResponse({"error": exception.message, "code": exception.code}, status=403)
    return defaults.permission_denied(request, exception)
