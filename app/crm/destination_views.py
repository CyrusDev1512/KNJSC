"""Cấu hình bảng nhận đơn, chỉ Admin; không di chuyển đơn đã có."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from core.constants import Rank
from core.permissions import assert_rank
from core.exceptions import BusinessError
from orders.services import destination_service


@login_required
@require_http_methods(['GET', 'POST'])
def configure(request):
    assert_rank(request.user, Rank.ADMIN, request)
    request.nav_current = 'order_destination'
    error = ''
    if request.method == 'POST':
        try:
            table_id = int(request.POST.get('table', ''))
            destination_service.configure(request.user, table_id, request=request)
        except (ValueError, TypeError):
            error = 'Chọn một bảng nhận đơn hợp lệ.'
        except BusinessError as exc:
            error = str(exc)
        else:
            messages.success(request, 'Đã đổi bảng nhận đơn mới. Đơn cũ giữ nguyên bảng và liên kết.')
            return redirect('order_destination')
    try:
        current = destination_service.current()
    except BusinessError:
        current = None
    return render(request, 'crm/order_destination.html', {
        'choices': destination_service.candidates(), 'destination': current, 'error': error,
    }, status=400 if error else 200)
