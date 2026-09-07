"""Màn hình Tài nguyên — MVP Nội bộ (ADR-015).

View chỉ nhận yêu cầu, kiểm quyền, gọi tầng dịch vụ, trả kết quả (điều cấm 2).
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def tai_nguyen(request):
    """Trang Tài nguyên — đang dựng, mọi cấp bậc vào được."""
    request.nav_current = "tai_nguyen"
    return render(request, "resources/tai_nguyen.html")
