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

if os.environ.get("BANGTINH_GOC", "dev") == "prod":
    from .prod import *  # noqa: F401,F403
else:
    from .dev import *  # noqa: F401,F403

GRID_ONLY_TABLES = set()
