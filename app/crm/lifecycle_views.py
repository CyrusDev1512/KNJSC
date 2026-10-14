from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST, require_http_methods
from core.audit import record_denied
from core.exceptions import BusinessError, OutOfScopeError
from django.http import Http404
from forms_builder.models import TableDef
from forms_builder.services import lifecycle_service as service
from core.pagination import paginate


@login_required
def deleted(request):
    return render(request,'crm/deleted_tables.html',{'page_obj':paginate(request,
        service.manageable(request.user).filter(deleted_at__isnull=False).select_related('department').order_by('-deleted_at'))})


def _tu_choi(request):
    """403 có dòng Từ chối (FR-3.5, AC-3.7)."""
    record_denied(request.user, request.path, request)
    raise PermissionDenied


@login_required
@require_http_methods(['GET','POST'])
def delete(request, code):
    table=service.manageable(request.user).filter(code=code).first()
    if table is None:
        # Thấy bảng mà không quản lý được (Giám đốc, Kế toán, Staff…) thì từ chối có nhật ký; không thấy thì 404, không lộ
        # bảng có tồn tại (P0-2)
        if TableDef.objects.in_scope(request.user).filter(code=code).exists():
            _tu_choi(request)
        raise Http404
    if not service.can_delete(request.user,table):_tu_choi(request)
    error=''
    if request.method=='POST':
        try:
            service.delete(request.user,table,request.POST.get('name'),request=request)
            messages.success(request,'Đã xóa bảng. Có thể khôi phục trong Đã xóa.')
            return redirect('deleted_tables')
        except BusinessError as exc:error=str(exc)
        except OutOfScopeError:_tu_choi(request)
    return render(request,'crm/delete_table.html',{'bang':table,'error':error},status=400 if error else 200)


@login_required
@require_POST
def restore(request, code):
    table=get_object_or_404(service.manageable(request.user),code=code,deleted_at__isnull=False)
    try:service.restore(request.user,table,request=request)
    except OutOfScopeError:_tu_choi(request)
    messages.success(request,'Đã khôi phục bảng.')
    return redirect('thu_muc')
