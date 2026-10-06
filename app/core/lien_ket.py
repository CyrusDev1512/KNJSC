"""Địa chỉ sang dịch vụ còn lại (KN ERP ↔ KN CRM) — một chỗ duy nhất, AC-1.10.

Máy local chạy hai dịch vụ ở hai cổng; liên kết mặc định trỏ `localhost`. Người dùng mở bằng `127.0.0.1` mà bị đưa
sang `localhost` là sang host khác: trình duyệt không gửi cookie phiên, trang đăng nhập hiện ra như mất quyền. Nên khi
cả địa chỉ cấu hình lẫn host đang mở đều là máy local, giữ host đang mở và chỉ lấy cổng từ cấu hình. Tên miền thật
(VPS) thì giữ đúng cấu hình.
"""
from urllib.parse import urlsplit, urlunsplit

from django.conf import settings

MAY_LOCAL = {"localhost", "127.0.0.1", "::1"}


def theo_host_dang_mo(url, request):
    if not url or request is None:
        return url
    phan = urlsplit(url)
    try:
        host = request.get_host().rsplit(":", 1)[0].strip("[]")
    except Exception:  # host lạ đã bị Django chặn ở chỗ khác; ở đây giữ nguyên cấu hình
        return url
    if phan.hostname not in MAY_LOCAL or host not in MAY_LOCAL or phan.hostname == host:
        return url
    ten = f"[{host}]" if ":" in host else host
    return urlunsplit(phan._replace(netloc=ten + (f":{phan.port}" if phan.port else "")))


def crm_url(request):
    """Gốc KN CRM; rỗng khi chính đây là KN CRM (`bangtinh` đặt BANGTINH_URL rỗng)."""
    return theo_host_dang_mo(getattr(settings, "BANGTINH_URL", ""), request)


def erp_url(request):
    return theo_host_dang_mo(getattr(settings, "MAIN_APP_URL", ""), request)
