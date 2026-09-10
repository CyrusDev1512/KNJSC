"""Điểm vào riêng của lưới JSON; bảng cũ tiếp tục dùng view/HTMX hiện có."""
import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from core.exceptions import BusinessError, OutOfScopeError
from forms_builder.services import grant_service
from orders.services.assignment_service import can_assign
from .services import master_grid_service as service, grid_service, sidebar_service, tree_service


@login_required
@require_GET
def data(request, code):
    try:
        table = service.table_for(request.user, code)
        if 'check_ids' in request.GET:
            from forms_builder.models import DataRecord
            try:
                ids = {int(pk) for pk in request.GET['check_ids'].split(',')}
                if len(ids) > 4000:
                    raise ValueError
            except ValueError:
                raise BusinessError('Danh sách dòng không hợp lệ.')
            return JsonResponse({'visible': list(DataRecord.objects.in_scope(request.user).filter(
                table=table, pk__in=ids).values_list('pk', flat=True))})
        if 'check_id' in request.GET:
            from forms_builder.models import DataRecord
            try:
                pk = int(request.GET['check_id'])
            except (ValueError, TypeError):
                raise BusinessError('Định danh dòng không hợp lệ.')
            if not DataRecord.objects.in_scope(request.user, table=table).filter(pk=pk).exists():
                raise OutOfScopeError()
            return JsonResponse({'visible': True})
        return JsonResponse(service.block(request.user, table, request.GET))
    except BusinessError as exc:
        return JsonResponse({'error': str(exc)}, status=409 if exc.code == 'conflict' else 400)
    except OutOfScopeError:
        return JsonResponse({'error': 'Bạn không còn quyền xem dữ liệu này.'}, status=403)


@login_required
@require_POST
def save(request, code):
    try:
        table = service.table_for(request.user, code)
        return JsonResponse(service.save(request.user, table, json.loads(request.body), request=request))
    except OutOfScopeError:
        return JsonResponse({'error': 'Bạn không còn quyền sửa các dòng này.'}, status=403)
    except BusinessError as exc:
        return JsonResponse({'error': str(exc), 'conflicts': getattr(exc, 'conflicts', []), 'cell': {'id': getattr(exc, 'pk', None),
            'column': getattr(exc, 'column', None)}}, status=409 if exc.code == 'conflict' else 400)
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'error': 'Dữ liệu gửi lên không hợp lệ.'}, status=400)


@login_required
@require_GET
def history(request, code):
    try:
        return JsonResponse(service.history(request.user, service.table_for(request.user, code), request.GET))
    except OutOfScopeError:
        return JsonResponse({'error': 'Bạn không còn quyền xem lịch sử dòng này.'}, status=403)
    except BusinessError as exc:
        return JsonResponse({'error': str(exc)}, status=400)


@login_required
@require_POST
def scope(request, code):
    """Đọc quyền theo ID bằng POST để không vượt giới hạn URL khi cache lớn."""
    from forms_builder.models import DataRecord
    try:
        table = service.table_for(request.user, code)
        ids = json.loads(request.body).get('ids')
        if not isinstance(ids, list) or len(ids)>4000 or any(type(pk) is not int or pk<1 for pk in ids):
            raise ValueError
        return JsonResponse({'visible': list(DataRecord.objects.in_scope(request.user, table=table).filter(pk__in=ids).values_list('pk',flat=True))})
    except OutOfScopeError:
        return JsonResponse({'error':'Bạn không còn quyền xem bảng.'},status=403)
    except (ValueError, TypeError, AttributeError):
        return JsonResponse({'error':'Danh sách dòng không hợp lệ.'},status=400)


def shell(request, table):
    from forms_builder.services.record_service import PALETTE
    grid = grid_service.build_grid(request.user, request.GET, table=table)
    month = tree_service.month_of_params(request.GET, grid.columns)
    qs = request.GET.copy()
    for key in ('trang', 'moi_trang', 'offset', 'version'):
        qs.pop(key, None)
    chips = []
    for key, label in grid.chips:
        p = qs.copy(); p.pop(key, None)
        chips.append((label, '?' + p.urlencode()))
    return render(request, 'crm/master_grid.html', {
        'bang': table, 'luoi': grid, 'qs_giu': qs.urlencode(), 'chips': chips,
        've_url': tree_service.home_url(table.department, month=month) if month else tree_service.home_url(table.department, all_tables=True),
        've_nhan': 'Về Bảng tính — thư mục', 'can_assign': can_assign(request.user),
        'duoc_nhap': grant_service.can_import(request.user, table),
        'ben': sidebar_service.context(request.user, table, grid.columns, qs),
        'quick_filters': sidebar_service.quick_filters(qs),
        'config': {'dataUrl': reverse('master_data', args=[table.code]),
                   'palette': dict(PALETTE), 'styleClasses': grid_service.STYLE_CLASSES,
                   'saveUrl': reverse('master_save', args=[table.code]),
                   'historyUrl': reverse('master_history', args=[table.code]),
                   'scopeUrl': reverse('master_scope', args=[table.code]),
                   'filterUrl': reverse('bang_tinh_xem', args=[table.code]),
                   'user': request.user.pk, 'table': table.code},
    })
