import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from core.exceptions import BusinessError, OutOfScopeError
from forms_builder.models import DataRecord
from orders.constants import ACTIVE_WAYBILL_TABLE_CODE
from orders.services import assignment_service as service


@login_required
@require_http_methods(['GET', 'POST'])
def assignment(request):
    if not service.can_assign(request.user):
        raise OutOfScopeError()
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            if not isinstance(data, dict):
                raise BusinessError('Dữ liệu phân công không hợp lệ.')
            result = service.assign(request.user, data.get('versions'), data.get('changes'), request=request)
            return JsonResponse({'versions': result, 'message': f'Đã phân công {len(result)} dòng.'})
        ids = {service.integer(v) for v in request.GET.getlist('row')}
        if not ids:
            return JsonResponse({'rows': [], 'fields': [], 'message': 'Chọn ít nhất một dòng có dữ liệu.'})
        rows = list(service.related(DataRecord.objects.in_scope(request.user).filter(
            table__code=ACTIVE_WAYBILL_TABLE_CODE, pk__in=ids)).order_by('pk'))
        if len(rows) != len(ids):
            raise OutOfScopeError()
        return JsonResponse({
            'rows': [{'id': r.pk, 'version': getattr(getattr(r, 'assignment', None), 'version', 0),
                      'current': {field: service.label(getattr(getattr(r, 'assignment', None), field, None))
                                  for field in service.FIELDS}} for r in rows],
            'fields': [{'key': field, 'label': service.LABELS[field],
                        'choices': [{'id': u.pk, 'label': service.label(u)} for u in service.candidates(field)]}
                       for field in service.FIELDS]})
    except BusinessError as exc:
        return JsonResponse({'error': str(exc)}, status=409 if exc.code == 'conflict' else 400)
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'error': 'Dữ liệu phân công không hợp lệ.'}, status=400)
