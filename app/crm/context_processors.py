"""Sidebar KN CRM đưa vào mọi template — chỉ khi đang chạy dịch vụ 8021.

Đăng ký chung ở `settings/base.py` để bộ kiểm (đổi `ROOT_URLCONF` bằng
override) cũng có; ở KN ERP hàm trả rỗng, không tốn truy vấn nào.
"""
from django.conf import settings


def khung_crm(request):
    if settings.ROOT_URLCONF != "knjsc.urls_bangtinh" or not request.user.is_authenticated:
        return {}
    from .navigation import build

    return {"crm_nav": build(request.user, getattr(request, "nav_current", ""))}
