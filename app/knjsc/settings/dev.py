"""Cấu hình máy cá nhân."""
from .base import *  # noqa: F401,F403
from .base import env_list

DEBUG = True
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0,web")
INTERNAL_IPS = ["127.0.0.1"]

# Máy cá nhân không cần kết nối mã hoá
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
