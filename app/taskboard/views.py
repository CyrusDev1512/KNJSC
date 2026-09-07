"""Màn hình Công việc — MVP Nội bộ (ADR-015).

View chỉ nhận yêu cầu, kiểm quyền, gọi tầng dịch vụ, trả kết quả (điều cấm 2).
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def cong_viec(request):
    """Trang Công việc — đang dựng, mọi cấp bậc vào được."""
    request.nav_current = "cong_viec"
    return render(request, "taskboard/cong_viec.html")
