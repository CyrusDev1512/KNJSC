"""Điểm vào của bộ lưới JSON dùng chung cho các bảng động."""
from orders.constants import is_waybill_table
from orders.services import dispatch_service, waybill_service
import json
from django.conf import settings
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
        return JsonResponse({'error': str(exc), 'code':exc.code,
            'currency_confirmations': getattr(exc, 'currency_confirmations', {}),
            'conflicts': getattr(exc, 'conflicts', []), 'cell': {'id': getattr(exc, 'pk', None),
            'column': getattr(exc, 'column', None)}}, status=409 if exc.code == 'conflict' else 400)
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'error': 'Dữ liệu gửi lên không hợp lệ.'}, status=400)


@login_required
@require_POST
def clear_details(request, code):
    """Delete trên ô tổng của Vận đơn = bỏ toàn bộ Chi tiết sản phẩm của dòng (chủ dự án 02.10.2026)."""
    from forms_builder.models import DataRecord
    from orders.services import assignment_service
    try:
        table = service.table_for(request.user, code)
        if not is_waybill_table(table):
            raise BusinessError('Bảng này không có Chi tiết sản phẩm.')
        rows = waybill_service.clear_items(request.user, table, json.loads(request.body).get('cells'),
                                           request=request)
        columns = grid_service.display_columns(table)
        for column in columns:
            column.table = table
        fresh = assignment_service.related(DataRecord.objects.in_scope(request.user, table=table)
                                           .filter(pk__in=[r.pk for r in rows]).select_related('table'))
        return JsonResponse({'rows': service.serialize(fresh.order_by('pk'), columns, request.user),
                             'latest': service.latest_stamp(request.user, table)})
    except OutOfScopeError:
        return JsonResponse({'error': 'Bạn không còn quyền sửa các dòng này.'}, status=403)
    except BusinessError as exc:
        return JsonResponse({'error': str(exc)}, status=409 if exc.code == 'conflict' else 400)
    except (ValueError, TypeError, AttributeError, json.JSONDecodeError):
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


@login_required
@require_POST
def sync(request,code):
    from django.db import connection,transaction
    from .services import optimization, row_mutations
    if not optimization.enabled('SYNC'):return JsonResponse({'unsupported':True})
    try:
        table=service.table_for(request.user,code)
        if not is_waybill_table(table):return JsonResponse({'unsupported':True})
        already_atomic=connection.in_atomic_block
        with transaction.atomic():
            if not already_atomic:
                with connection.cursor() as cursor:cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            return JsonResponse(optimization.sync(request.user,table,json.loads(request.body)))
    except OutOfScopeError:return JsonResponse({'error':'Bạn không còn quyền xem bảng.'},status=403)
    except BusinessError as exc:return JsonResponse({'error':str(exc)},status=409 if exc.code=='conflict' else 400)
    except (ValueError,TypeError,AttributeError):return JsonResponse({'error':'Dữ liệu đồng bộ không hợp lệ.'},status=400)


def _query_va_chip(request, grid):
    """Tham số lọc đang áp (bỏ tham số trang) và chip "đang lọc" kèm link bỏ từng chip."""
    qs = request.GET.copy()
    for key in ('trang', 'moi_trang', 'offset', 'version', 'panel'):
        qs.pop(key, None)
    chips = []
    for key, label, an in grid.chips:
        p = qs.copy(); p.pop(key, None)
        chips.append((label, '?' + p.urlencode(), an))
    return qs, chips


def filters(request, table):
    """Chip "đang lọc" và (khi `panel=1`) nội dung panel Bộ lọc của lưới — một mảnh HTML, không có dòng dữ liệu.

    Panel Bộ lọc của bảng Vận đơn đếm số dòng theo sản phẩm, thị trường, marketer trên cả bảng trong phạm vi người
    xem (ba lượt GROUP BY). Trước đây trang lưới tính sẵn mỗi lần mở dù panel đang ẩn, và đổi bộ lọc thì tải lại cả trang
    lưới chỉ để lấy panel và chip. Nay: mở lưới không tính; lưới gọi mảnh này khi người dùng mở panel, và khi đổi bộ
    lọc chỉ lấy chip (cùng panel nếu panel đã mở) — mục a, b của biên bản 07.10.2026."""
    grid = grid_service.build_grid(request.user, request.GET, table=table)
    qs, chips = _query_va_chip(request, grid)
    ctx = {'bang': table, 'luoi': grid, 'chips': chips, 'panel': request.GET.get('panel') == '1', 'config': True}
    if ctx['panel']:
        ctx['ben'] = sidebar_service.context(request.user, table, grid.columns, qs)
        ctx['quick_filters'] = (sidebar_service.quick_filters(qs) if is_waybill_table(table)
                                else {'groups': [], 'keep': grid_service.params_without(qs)})
    # Dựng không qua context processor: mảnh không có khung trang, mà menu khung CRM (`crm_nav`) tốn một lượt hỏi phạm vi
    # bảng (0,4 s ở 385.000 dòng). Mảnh chỉ có form GET nên không cần CSRF
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    response = HttpResponse(render_to_string('crm/_master_filters_manh.html', ctx))
    response.context = ctx      # bài kiểm đọc `context` như với `render`
    return response


def shell(request, table):
    from django.conf import settings
    from .services import optimization, row_mutations
    from forms_builder.services.record_service import PALETTE
    grid = grid_service.build_grid(request.user, request.GET, table=table)
    month = tree_service.month_of_params(request.GET, grid.columns)
    qs, chips = _query_va_chip(request, grid)
    return render(request, 'crm/master_grid.html', {
        'waybill_profile': is_waybill_table(table),
        # Nút Tôi / Toàn bộ: chỉ người có cột phụ trách trong bảng vận đơn (ADR-033)
        'pham_vi_toi': is_waybill_table(table),
        'payment_documents_enabled': getattr(settings, 'PAYMENT_DOCUMENTS_ENABLED', False),
        'grid_root_class':'mg-root mg-waybill-master' if is_waybill_table(table) else 'mg-root',
        'thang_dang_xem':month, 'bang': table, 'luoi': grid, 'qs_giu': qs.urlencode(), 'chips': chips,
        've_url': tree_service.home_url(table.department),
        've_nhan': 'Về Bảng tính — thư mục', 'can_assign': is_waybill_table(table) and can_assign(request.user),
        'duoc_quan_ly_cot':grant_service.can_manage_columns(request.user, table),
        'duoc_nhap': grant_service.can_import(request.user, table),
        # Panel Bộ lọc không tính sẵn: lưới tải nó khi người dùng mở (`filters`)
        'config': {'dataUrl': reverse('master_data', args=[table.code]),
                   # Ẩn cột cho cả công ty — ADR-039. Chỉ quản lý bảng thấy danh
                   # sách cột đang ẩn để bật lại; người khác không biết là có.
                   'canHideColumns': grant_service.can_manage_columns(request.user, table),
                   'hideColumnsUrl': reverse('bang_tinh_an_cot', args=[table.code]),
                   'hiddenColumns': ([{'code': c.code, 'name': c.name}
                                      for c in table.columns.filter(is_hidden=True).order_by('order', 'id')]
                                     if grant_service.can_manage_columns(request.user, table) else []),
                   'productColumns': [c.code for c in grid.columns
                                      if c.code.startswith(dispatch_service.PRODUCT_COLUMN_PREFIX)],
                   'deliveryViewVersion': table.delivery_view_version,
                   'myScope': is_waybill_table(table),
                   'canCreate':row_mutations.can_create(request.user,table),
                   'requestMetrics':getattr(settings,'CRM_REQUEST_METRICS',False),
                   'protocol':2 if is_waybill_table(table) and optimization.enabled('READ') else 1,
                   'compact':optimization.enabled('RECEIPTS'),
                   'renderOptimized':optimization.enabled('RENDER'),
                   'syncUrl':reverse('master_sync',args=[table.code]) if is_waybill_table(table) and optimization.enabled('SYNC') and optimization.enabled('READ') else None,
                   'palette': dict(PALETTE), 'styleClasses': grid_service.STYLE_CLASSES,
                   'saveUrl': reverse('master_save', args=[table.code]),
                   # Delete trên bốn ô tổng hỏi lại rồi bỏ toàn bộ chi tiết (chủ dự án 02.10.2026)
                   'detailColumns': sorted(waybill_service.DETAIL_CELLS) if is_waybill_table(table) else [],
                   'clearDetailsUrl': (reverse('master_clear_details', args=[table.code])
                                       if is_waybill_table(table) else None),
                   'historyUrl': reverse('master_history', args=[table.code]),
                   'scopeUrl': reverse('master_scope', args=[table.code]),
                   'filterUrl': reverse('bang_tinh_xem', args=[table.code]),
                   'filtersUrl': reverse('master_filters', args=[table.code]),
                   'user': request.user.pk, 'table': table.code},
    })
