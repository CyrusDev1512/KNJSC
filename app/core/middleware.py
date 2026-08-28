"""Middleware của core.

Ba việc: hết phiên khi không thao tác, buộc đổi mật khẩu lần đầu, và chặn
trình duyệt lưu lại trang có dữ liệu.
"""
import time

from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.cache import add_never_cache_headers

# Những đường dẫn luôn cho qua, nếu không sẽ chuyển hướng vòng tròn
EXEMPT_PREFIXES = ("/dang-nhap", "/dang-xuat", "/doi-mat-khau", "/static", "/media")


def _is_exempt(path):
    return any(path.startswith(p) for p in EXEMPT_PREFIXES)


class SessionTimeoutMiddleware:
    """Phiên hết hạn hoặc mất hiệu lực.

    Hai việc:

    1. Hết phiên sau một khoảng không thao tác.
    2. Nguyên tắc P4 — đổi quyền hoặc khoá tài khoản thì phiên đang mở mất
       hiệu lực **ngay**, không đợi lần đăng nhập sau. Hồ sơ nhân sự giữ một
       số mốc `session_epoch`, tăng lên mỗi lần đổi quyền. Phiên nào mang
       mốc cũ thì bị đẩy ra.
    """

    #: Chỉ ghi lại dấu thời gian khi đã trôi quá ngần này giây. Ghi ở mọi yêu
    #: cầu thì mỗi lần mở trang đều kèm một lệnh UPDATE vào bảng phiên — tốn
    #: vô ích, và làm màn hình danh sách vượt ngưỡng số truy vấn ở AC-10.2.
    GHI_LAI_SAU = 60

    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout = getattr(settings, "SESSION_IDLE_TIMEOUT_SECONDS", 3600)

    def __call__(self, request):
        if request.user.is_authenticated:
            now = int(time.time())
            last = request.session.get("last_seen_at")
            if last and now - last > self.timeout:
                logout(request)
                return redirect(f"{settings.LOGIN_URL}?het_phien=1")

            profile = getattr(request.user, "profile", None)
            if profile is not None:
                moc_phien = request.session.get("auth_epoch")
                if moc_phien is not None and moc_phien != profile.session_epoch:
                    logout(request)
                    return redirect(f"{settings.LOGIN_URL}?doi_quyen=1")

            if last is None or now - last >= self.GHI_LAI_SAU:
                request.session["last_seen_at"] = now
        return self.get_response(request)


class ForcePasswordChangeMiddleware:
    """Buộc đổi mật khẩu trước khi dùng hệ thống (FR-1.3)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and not _is_exempt(request.path):
            profile = getattr(user, "profile", None)
            if profile is not None and getattr(profile, "must_change_password", False):
                return redirect(reverse("doi_mat_khau"))
        return self.get_response(request)


class NoCacheForAuthenticatedMiddleware:
    """Không cho trình duyệt lưu lại trang của người đã đăng nhập.

    Nếu không có, bấm nút Lùi sau khi đăng xuất vẫn thấy dữ liệu cũ.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated and not request.path.startswith("/static"):
            add_never_cache_headers(response)
        return response
