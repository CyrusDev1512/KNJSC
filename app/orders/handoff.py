"""Chuyển bookmark đọc sang CRM, tuyệt đối không chuyển tiếp POST."""
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_GET
from core.navigation import SALES_ONLY
from core.permissions import assert_departments
from .services.order_service import orders_of

@login_required
@require_GET
def handoff(request, destination, code=None):
    if code:
        get_object_or_404(orders_of(request.user), code=code)
    else:
        assert_departments(request.user, SALES_ONLY, request)
    base = settings.BANGTINH_URL.rstrip('/')
    if not base:
        return HttpResponse("Chưa cấu hình địa chỉ KN CRM.", status=503)
    target = reverse(destination, kwargs={"code": code} if code else None,
                     urlconf="knjsc.urls_bangtinh")
    return redirect(base + target)
