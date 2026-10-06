"""Cấu hình dịch vụ **Bảng tính** — ADR-009.

Cùng mã, cùng cơ sở dữ liệu với dịch vụ chính, chạy trong container riêng
(`bangtinh`, cổng 8021) để lưới làm việc của Vận đơn không chịu tải chung với
cả hệ thống; tương lai đứng sau một subdomain.

Khác dịch vụ chính đúng hai chỗ:

- `GRID_ONLY_TABLES` rỗng — ở đây bảng vận đơn **sửa được**, còn ở dịch vụ
  chính chỉ xem.
- `ROOT_URLCONF` thu hẹp (Giai đoạn 7C) — chỉ đăng nhập và Bảng tính.

Chọn gốc dev hay prod bằng biến `BANGTINH_GOC` (mặc định `dev`). Khi lên máy
chủ (Giai đoạn 8) đặt thêm `SESSION_COOKIE_DOMAIN` và `CSRF_TRUSTED_ORIGINS`
để hai subdomain dùng chung phiên đăng nhập.
"""
import os

from django.core.exceptions import ImproperlyConfigured

_MAY_LOCAL = {"localhost", "127.0.0.1", "0.0.0.0", "web", "bangtinh", "::1", ""}
if "BANGTINH_GOC" not in os.environ and set(
        h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")) - _MAY_LOCAL:
    # Chạy ở tên miền thật mà quên BANGTINH_GOC thì trước đây lặng lẽ lấy cấu hình dev (DEBUG bật, cookie không
    # Secure). Dừng hẳn và nói rõ — AC-1.11
    raise ImproperlyConfigured(
        "Dịch vụ KN CRM chạy ở tên miền thật nhưng thiếu BANGTINH_GOC. Đặt BANGTINH_GOC=prod (máy chủ) "
        "hoặc BANGTINH_GOC=dev (máy local)."
    )
if os.environ.get("BANGTINH_GOC", "dev") == "prod":
    from .prod import *  # noqa: F401,F403
else:
    from .dev import *  # noqa: F401,F403

GRID_ONLY_TABLES = set()
ROOT_URLCONF = "knjsc.urls_bangtinh"
# Ở chính dịch vụ này, mục "Bảng tính" trên thanh bên là liên kết trong
BANGTINH_URL = ""
