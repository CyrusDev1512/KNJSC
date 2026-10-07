"""Kiểm cấu hình lúc phát hành (`manage.py check --deploy`) — AC-1.11.

ERP và CRM ở hai tên miền thì cookie phiên phải đặt cho tên miền cha chung, không thì sang tên miền kia là phải đăng
nhập lại: người dùng thấy như "đổi URL là mất quyền". Lỗi cấu hình này không có bài kiểm nào bắt được ở máy local (một
host, hai cổng), nên chặn ngay lúc phát hành.
"""
from urllib.parse import urlsplit

from django.conf import settings
from django.core.checks import Error, Tags, register


def _ten_mien(url):
    return (urlsplit(url).hostname or "").lower() if url else ""


def _phu(ten_mien_cha, host):
    goc = (ten_mien_cha or "").lower().lstrip(".")
    return bool(goc) and (host == goc or host.endswith("." + goc))


@register(Tags.security, deploy=True)
def kiem_phien_chung(app_configs, **kwargs):
    if settings.DEBUG:
        return []
    cac_host = {_ten_mien(u) for u in [getattr(settings, "MAIN_APP_URL", ""), getattr(settings, "BANGTINH_URL", ""),
                                        *getattr(settings, "CSRF_TRUSTED_ORIGINS", [])]} - {""}
    if len(cac_host) < 2:
        return []
    thieu = [ten for ten in ("SESSION_COOKIE_DOMAIN", "CSRF_COOKIE_DOMAIN")
             if not all(_phu(getattr(settings, ten, None), h) for h in cac_host)]
    if not thieu:
        return []
    return [Error(
        f"KN ERP và KN CRM ở nhiều tên miền ({', '.join(sorted(cac_host))}) nhưng {' và '.join(thieu)} chưa là tên miền "
        "cha chung: sang dịch vụ kia sẽ phải đăng nhập lại.",
        hint="Đặt SESSION_COOKIE_DOMAIN và CSRF_COOKIE_DOMAIN trong .env của VPS là tên miền cha, ví dụ .ten-mien.vn.",
        id="core.E001",
    )]
