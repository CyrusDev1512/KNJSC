"""Cấu hình khi chạy kiểm thử.

Khác dev ở ba chỗ: bật thêm app chứa model thử phạm vi, chạy tác vụ nền
ngay tại chỗ, và băm mật khẩu bằng thuật toán nhanh cho đỡ mất thời gian.
"""
from .dev import *  # noqa: F401,F403
from .dev import INSTALLED_APPS

INSTALLED_APPS = INSTALLED_APPS + ["core.tests.apps.CoreTestsConfig"]

CELERY_TASK_ALWAYS_EAGER = True
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Giữ đúng ngưỡng thật để bài kiểm AC-1.4 có nghĩa
SESSION_IDLE_TIMEOUT_SECONDS = 3600
