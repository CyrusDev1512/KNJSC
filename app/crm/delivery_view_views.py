"""Cấu hình phạm vi xem chung, quản lý được từ cấp quyền hoặc lưới."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from core.exceptions import BusinessError, OutOfScopeError
from orders.services import delivery_view_service
from .services.master_grid_service import table_for


@login_required
@require_http_methods(['GET', 'POST'])
def configure(request, code):
    try:
        table = table_for(request.user, code)
        if not delivery_view_service.can_manage(request.user, table):
            raise OutOfScopeError()
        if request.method == 'POST':
            try:
                delivery_view_service.change(request.user, table, request.POST.get('mode'), request=request)
            except BusinessError as exc:
                return render(request, 'crm/delivery_view_mode.html', {'bang': table, 'error': str(exc)}, status=400)
            messages.success(request, 'Đã lưu chế độ xem. Các trang bảng đang mở sẽ tải lại trong khoảng 8 giây.')
            return redirect('delivery_view_mode', code=code)
        return render(request, 'crm/delivery_view_mode.html', {'bang': table})
    except OutOfScopeError:
        raise PermissionDenied
