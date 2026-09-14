"""Môi trường xem thử riêng; không dùng cookie hoặc dữ liệu của bản đang chạy."""
import os

if os.environ.get("SOLARPUNK_CRM") == "1":
    from .bangtinh import *  # noqa: F401,F403
else:
    from .dev import *  # noqa: F401,F403

SESSION_COOKIE_NAME = "kn_solarpunk_session"
CSRF_COOKIE_NAME = "kn_solarpunk_csrf"
