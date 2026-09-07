"""Màn hình Tài liệu — MVP Nội bộ (ADR-015).

View chỉ nhận yêu cầu, kiểm quyền, gọi tầng dịch vụ, trả kết quả (điều cấm 2).
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def tai_lieu(request):
    """Trang Tài liệu — đang dựng, mọi cấp bậc vào được."""
    request.nav_current = "tai_lieu"
    return render(request, "documents/tai_lieu.html")
