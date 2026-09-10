from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from core.pagination import paginate
from orders.constants import ACTIVE_WAYBILL_TABLE_CODE
from orders.services import waybill_service
from .services import master_grid_service, grid_service, sidebar_service, statistics_service


@login_required
def overview(request):
    table = master_grid_service.table_for(request.user, ACTIVE_WAYBILL_TABLE_CODE)
    request.nav_current = 'statistics'
    grid = grid_service.build_grid(request.user, request.GET, table=table)
    group = request.GET.get('group', 'total')
    if group not in {'total', 'seller', 'product', 'market'}:
        return HttpResponse('Cách nhóm thống kê không hợp lệ.', status=400)
    rows, grouping = waybill_service.statistics(grid.queryset, group)
    page = paginate(request, rows)
    results = [{**r, 'label': r[grouping[0]] if group != 'total' else 'Tổng hợp',
                'currency': r['record__data__loai_tien'], 'quantity': r['quantity_total']} for r in page.object_list]
    if group == 'product':
        for r in results:
            r['label'] = f'{r["product__name"]} ({r["product__code"]})'
    summary, charts = statistics_service.build(grid.queryset, request)
    params = request.GET.copy(); params.pop('trang', None)
    grid_params = params.copy()
    for key in ('group', 'chart_market', 'chart_product'):
        grid_params.pop(key, None)
    chips = []
    for key, label in grid.chips:
        p = params.copy(); p.pop(key, None)
        chips.append((label, '?' + p.urlencode()))
    return render(request, 'crm/statistics.html', {
        'bang': table, 'luoi': grid, 'summary': summary, 'charts': charts, 'results': results,
        'page': page, 'group': group, 'params': params.urlencode(), 'qs_giu': grid_params.urlencode(),
        'filters': [(k, v) for k, vs in params.lists() if k != 'group' for v in vs],
        'groups': [('total', 'Tổng hợp'), ('seller', 'Theo nhân viên'), ('product', 'Theo sản phẩm'), ('market', 'Theo thị trường')],
        'ben': sidebar_service.context(request.user, table, grid.columns, grid_params),
        'quick_filters': sidebar_service.quick_filters(grid_params), 'chips': chips, 'updated': timezone.now(),
    })
