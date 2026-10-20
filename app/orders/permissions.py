"""Phạm vi đọc riêng của đơn hàng; không cấp quyền ghi hay quản trị."""
from core.constants import Rank
from core.scope import get_user_scope


def can_view_company_orders(user):
    """Chốt 19.10.2026: Manager đọc mọi đơn/vận đơn, các dữ liệu khác giữ phạm vi cũ."""
    scope = get_user_scope(user)
    return scope.all_departments or scope.rank == Rank.MANAGER
