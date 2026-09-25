"""Khóa vòng đời bảng: ghi dùng khóa chia sẻ, xóa/khôi phục dùng độc quyền."""
from functools import wraps
from inspect import signature
from django.db import connection, transaction
from core.audit import record
from core.constants import Rank, AuditAction, JobKind, JobStatus
from core.exceptions import BusinessError, OutOfScopeError
from core.scope import get_user_scope
from core.permissions import assert_business_write
from core.models import BackgroundJob
from forms_builder.models import TableDef, FormDef
from forms_builder import record_policies

LOCK_NAMESPACE = 0x4B4E5442


def available(table):
    if not TableDef.objects.filter(pk=table.pk, is_active=True).exists():
        raise OutOfScopeError('Bảng không còn khả dụng. Hãy tải lại trang.')


def lock(table, *, exclusive=False):
    if not connection.in_atomic_block:
        raise RuntimeError('Khóa vòng đời phải nằm trong giao dịch.')
    function = 'pg_advisory_xact_lock' if exclusive else 'pg_advisory_xact_lock_shared'
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT {function}(%s, %s)', [LOCK_NAMESPACE, table.pk])
    if not exclusive:
        available(table)


def writing(fn):
    """Service nhận bảng/bản ghi (hoặc danh sách ô) ở tham số đầu."""
    first = next(iter(signature(fn).parameters))
    @wraps(fn)
    def wrapped(*args, **kwargs):
        assert_business_write(kwargs.get("actor"))
        subject = args[0] if args else kwargs[first]
        objects = [c[0] for c in subject] if isinstance(subject, (list, tuple)) else [subject]
        tables = {obj.table_id if hasattr(obj,'table_id') else obj.pk:
                  obj.table if hasattr(obj,'table_id') else obj for obj in objects}
        with transaction.atomic():
            for pk in sorted(tables):lock(tables[pk])
            return fn(*args, **kwargs)
    return wrapped


def manageable(user, queryset=None):
    queryset = TableDef.all_objects.all() if queryset is None else queryset
    scope = get_user_scope(user)
    if not user.is_active:return queryset.none()
    if scope.is_admin:return queryset
    if scope.rank == Rank.MANAGER:
        return queryset.filter(department_id=user.profile.department_id)
    return queryset.none()


def can_delete(user, table):
    policy = record_policies.for_table(table)
    scope = get_user_scope(user)
    return user.is_active and not (policy and getattr(policy,'protect_table',False)) and (scope.is_admin or (scope.rank == Rank.MANAGER and table.department_id == user.profile.department_id))


@transaction.atomic
def delete(user, table, name, *, request=None):
    if not can_delete(user, table):raise OutOfScopeError()
    lock(table, exclusive=True)
    current = TableDef.all_objects.get(pk=table.pk)
    if not can_delete(user, current):raise OutOfScopeError()
    if name != current.name:raise BusinessError('Nhập đúng tên bảng để xác nhận xóa.')
    if current.deleted_at:return current
    forms = list(FormDef.objects.filter(table=current, is_active=True).values_list('name',flat=True))
    jobs = list(BackgroundJob.objects.filter(target_type='table',target_id=current.code,
        kind__in=[JobKind.IMPORT,JobKind.RECOMPUTE],status__in=[JobStatus.PENDING,JobStatus.RUNNING])
        .values_list('pk',flat=True))
    if forms or jobs:
        raise BusinessError('Chưa thể xóa: '+('; '.join(['Biểu mẫu: '+', '.join(forms)] if forms else [])+
            ('; ' if forms and jobs else '')+('Tác vụ ghi: '+', '.join(map(str,jobs)) if jobs else '')))
    current.delete(by=user)
    record(AuditAction.DELETE,actor=user,target=current,request=request,detail=f'Xóa mềm bảng {current.code}')
    return current


@transaction.atomic
def restore(user, table, *, request=None):
    if not can_delete(user,table):raise OutOfScopeError()
    lock(table,exclusive=True)
    current=TableDef.all_objects.select_related('folder').get(pk=table.pk)
    if not can_delete(user,current):raise OutOfScopeError()
    if current.deleted_at is None:return current
    current.deleted_at=current.deleted_by=None
    if current.folder and current.folder.deleted_at:current.folder=None
    current.save(update_fields=['deleted_at','deleted_by','folder','updated_at'])
    record(AuditAction.UPDATE,actor=user,target=current,request=request,detail=f'Khôi phục bảng {current.code}')
    return current
