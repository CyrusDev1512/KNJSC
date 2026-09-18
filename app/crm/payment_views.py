"""HTTP riêng của chứng từ; service kiểm quyền cho cả đường ảnh trực tiếp."""
from orders.constants import waybill_condition
from functools import wraps
from datetime import date
import uuid

from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import Http404
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import FileResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from core.exceptions import BusinessError, OutOfScopeError
from forms_builder.models import DataRecord
from orders.services import payment_service as service


def documents_enabled(view):
    """Ẩn tuyệt đối kho chứng từ khi cờ tính năng đang tắt."""
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not getattr(settings, 'PAYMENT_DOCUMENTS_ENABLED', False):
            raise Http404
        return view(request, *args, **kwargs)
    return wrapped


def errors(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        try:
            response = view(request, *args, **kwargs)
            response['Cache-Control'] = 'private, no-store'
            return response
        except OutOfScopeError:
            return JsonResponse({'error': 'Bạn không còn quyền truy cập chứng từ này.'}, status=403)
        except BusinessError as exc:
            return JsonResponse({'error': str(exc)}, status=409 if exc.code == 'conflict' else 400)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Dữ liệu gửi lên không hợp lệ.'}, status=400)
    return wrapped


def summary(document):
    return {'id': document.pk, 'reference': document.reference, 'version': document.version,
            'record': document.record_id, 'deleted': document.deleted_at is not None}


@documents_enabled
@login_required
@require_GET
@errors
def library(request):
    request.nav_current = 'payments'
    documents = service.documents_for(request.user, include_deleted=request.GET.get('deleted') == '1')
    if request.GET.get('record'):
        service.waybill_service.row_for(request.user, int(request.GET['record']))
        documents = documents.filter(record_id=request.GET['record'])
    if text := request.GET.get('q', '').strip():
        documents = documents.filter(Q(reference__icontains=text) | Q(record__data__ma_don__icontains=text))
    for parameter, field in [('uploaded_from', 'created_at__date__gte'), ('uploaded_to', 'created_at__date__lte'),
                             ('transfer_from', 'transfer_date__gte'), ('transfer_to', 'transfer_date__lte'),
                             ('uploader', 'created_by__profile__staff_code__icontains'), ('status', 'record__data__trang_thai_tt')]:
        if value := request.GET.get(parameter):
            if parameter.endswith(('_from', '_to')):
                value = date.fromisoformat(value)
            documents = documents.filter(**{field: value})
    documents = documents.select_related('record', 'created_by', 'created_by__profile').annotate(
        image_count=Count('images', filter=Q(images__deleted_at__isnull=True))).order_by('-created_at', '-id')
    page = Paginator(documents, 50).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    if request.GET.get('json') == '1':
        return JsonResponse({'documents': [summary(d) for d in page], 'pages': page.paginator.num_pages})
    return render(request, 'crm/payments.html', {'page': page, 'params': params.urlencode(),
        'can_create': service.can_create(request.user), 'can_manage': service.can_manage(request.user),
        'operation': str(uuid.uuid4()), 'query': request.GET})


@documents_enabled
@login_required
@require_GET
@errors
def rows(request):
    if not service.can_create(request.user):
        raise OutOfScopeError()
    records = DataRecord.objects.in_scope(request.user).filter(waybill_condition())
    text = request.GET.get('q', '').strip()
    if text:
        records = records.filter(Q(data__ma_don__icontains=text) | Q(data__ten_khach__icontains=text))
    return JsonResponse({'rows': [{'id': row.pk, 'label': f"{row.data.get('ma_don', '')} — {row.data.get('ten_khach', '')}"}
                                 for row in records.order_by('-id')[:50]]})


@documents_enabled
@login_required
@require_POST
@errors
def create(request):
    document = service.create(request.user, int(request.POST.get('record', '')), request.POST.get('reference', ''),
        request.POST.get('transfer_date', ''), request.POST.get('note', ''), request.FILES.getlist('images'),
        request.POST.get('operation', ''))
    return JsonResponse(summary(document))


@documents_enabled
@login_required
@require_GET
@errors
def detail(request, pk):
    document = service.document_for(request.user, pk, include_deleted=True)
    data = summary(document)
    data.update(note=document.note, transfer_date=document.transfer_date, can_manage=service.can_manage(request.user),
        images=[{'id': image.pk, 'url': reverse('payment_image', args=[image.pk])}
                for image in document.images.filter(deleted_at__isnull=True)])
    return JsonResponse(data)


@documents_enabled
@login_required
@require_POST
@errors
def update(request, pk):
    document = service.update(request.user, pk, request.POST.get('version'), request.POST.get('action'),
        reference=request.POST.get('reference', ''), transfer_date=request.POST.get('transfer_date', ''),
        note=request.POST.get('note', ''), uploads=request.FILES.getlist('images'), remove=request.POST.getlist('remove'))
    return JsonResponse(summary(document))


@documents_enabled
@login_required
@require_GET
@errors
def image(request, pk):
    image, path = service.image_for(request.user, pk)
    response = FileResponse(path.open('rb'), content_type='image/png' if image.file_kind == 'png' else 'image/jpeg',
        as_attachment=request.GET.get('download') == '1', filename=f'chung-tu-{image.pk}.{image.file_kind}')
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
