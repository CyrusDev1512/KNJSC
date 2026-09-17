"""Chế độ đọc của nhân viên Vận đơn; không thay phân công hoặc quyền ghi."""
from orders.constants import is_waybill_table
from django.db import transaction
from core.constants import Rank, AuditAction
from core.scope import get_user_scope
from core.exceptions import BusinessError, OutOfScopeError
from core.audit import record
from forms_builder.models import TableDef
from .assignment_service import department


def can_manage(user, table):
    scope = get_user_scope(user)
    return bool(user.is_active and is_waybill_table(table) and (
        scope.is_admin or (scope.rank == Rank.MANAGER and department(user) == 'van-don'
                           and user.profile.department_id == table.department_id)))


@transaction.atomic
def change(user, table, mode, *, request=None):
    if not can_manage(user, table):
        raise OutOfScopeError()
    if mode not in ('assigned', 'all'):
        raise BusinessError('Chọn Chỉ dòng được phân công hoặc Toàn bộ bảng.')
    current = TableDef.objects.select_for_update().get(pk=table.pk)
    if not can_manage(user, current):
        raise OutOfScopeError()
    wanted = mode == 'all'
    if current.delivery_view_all != wanted:
        current.delivery_view_all = wanted
        current.delivery_view_version += 1
        current.save(update_fields=['delivery_view_all', 'delivery_view_version', 'updated_at'])
        record(AuditAction.UPDATE, actor=user, target=current, request=request,
               detail=f'Chế độ xem Vận đơn: {mode}; phiên bản {current.delivery_view_version}')
    return current
