"""Màn hình Tổng quan."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .services import dashboard_service


@login_required
def tong_quan(request):
    request.nav_current = "tong_quan"
    boi_canh = dashboard_service.tong_quan(request.user)
    return render(request, "dashboard/tong_quan.html", boi_canh)
