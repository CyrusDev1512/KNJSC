from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST, require_http_methods
from core.exceptions import BusinessError, OutOfScopeError
from forms_builder.services import lifecycle_service as service
from core.pagination import paginate


@login_required
def deleted(request):
    return render(request,'crm/deleted_tables.html',{'page_obj':paginate(request,
        service.manageable(request.user).filter(deleted_at__isnull=False).select_related('department').order_by('-deleted_at'))})


@login_required
@require_http_methods(['GET','POST'])
def delete(request, code):
    table=get_object_or_404(service.manageable(request.user),code=code)
    if not service.can_delete(request.user,table):raise PermissionDenied
    error=''
    if request.method=='POST':
        try:
            service.delete(request.user,table,request.POST.get('name'),request=request)
            messages.success(request,'Đã xóa bảng. Có thể khôi phục trong Đã xóa.')
            return redirect('deleted_tables')
        except BusinessError as exc:error=str(exc)
        except OutOfScopeError:raise PermissionDenied
    return render(request,'crm/delete_table.html',{'bang':table,'error':error},status=400 if error else 200)


@login_required
@require_POST
def restore(request, code):
    table=get_object_or_404(service.manageable(request.user),code=code,deleted_at__isnull=False)
    try:service.restore(request.user,table,request=request)
    except OutOfScopeError:raise PermissionDenied
    messages.success(request,'Đã khôi phục bảng.')
    return redirect('thu_muc')
