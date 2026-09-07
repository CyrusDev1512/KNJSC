"""Màn hình Ghi nhận văn hoá — MVP Nội bộ (ADR-015).

View chỉ nhận yêu cầu, kiểm quyền, gọi tầng dịch vụ, trả kết quả (điều cấm 2).
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def van_hoa(request):
    """Trang Văn hoá — đang dựng, mọi cấp bậc vào được."""
    request.nav_current = "van_hoa"
    return render(request, "culture/van_hoa.html")
