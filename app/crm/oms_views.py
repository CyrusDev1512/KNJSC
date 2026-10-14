"""KN OMS — bản demo dữ liệu giả trong KN CRM, chỉ Admin (ADR-051, chủ dự án 13.10.2026).

Một trang đứng riêng ở `/oms/`: Báo đơn, Kho, Kênh bán & Page cộng Công nợ & đối soát, Khách rủi ro, Lãi theo page.
Mọi số liệu sinh ngay trong trình duyệt (`static/js/oms.js`); view này không đọc, không ghi dữ liệu nghiệp vụ nào.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

from core.permissions import assert_admin


@login_required
@require_GET
def kn_oms(request):
    # Chặn ở máy chủ, không chỉ ẩn mục trên thanh bên: vai khác gọi thẳng đường dẫn nhận 403 và có nhật ký từ chối
    assert_admin(request.user, request)
    return render(request, "crm/kn_oms.html")
