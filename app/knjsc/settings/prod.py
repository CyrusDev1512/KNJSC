"""Cấu hình máy chủ.

Khác dev ở ba chỗ: bắt buộc có khoá bí mật thật, bắt buộc kết nối mã hoá,
và không bao giờ bật chế độ gỡ lỗi.
"""
from .base import *  # noqa: F401,F403
from .base import env, env_list

DEBUG = False
SECRET_KEY = env("DJANGO_SECRET_KEY", bat_buoc=True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")

# Kết nối mã hoá
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")
