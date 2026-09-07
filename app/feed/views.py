"""Màn hình Bảng tin — MVP Nội bộ (ADR-015).

View chỉ nhận yêu cầu, kiểm quyền, gọi tầng dịch vụ, trả kết quả (điều cấm 2).
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def bang_tin(request):
    """Trang Bảng tin — đang dựng, mọi cấp bậc vào được."""
    request.nav_current = "bang_tin"
    return render(request, "feed/bang_tin.html")
