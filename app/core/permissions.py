"""Kiểm quyền theo cấp bậc và bộ phận.

Nguyên tắc P1: quyền kiểm ở máy chủ, không chỉ ẩn chức năng trên giao diện.
Nguyên tắc P3: ra ngoài phạm vi thì trả lỗi từ chối, không trả danh sách rỗng.
"""
from django.contrib.auth.mixins import LoginRequiredMixin

from .audit import record_denied
from .constants import Rank, rank_level
from .exceptions import OutOfScopeError
from .scope import get_user_scope


def get_rank(user):
    """Cấp bậc của một người dùng, hoặc None nếu chưa có hồ sơ."""
    if getattr(user, "is_superuser", False) and getattr(user, "profile", None) is None:
        return Rank.ADMIN
    profile = getattr(user, "profile", None)
    return profile.rank if profile else None


def has_rank(user, minimum):
    """Người này có cấp bậc từ `minimum` trở lên không."""
    return rank_level(get_rank(user)) >= rank_level(minimum)


def is_admin(user):
    """Admin có tất cả các quyền, ở mọi bộ phận."""
    return get_rank(user) == Rank.ADMIN


def in_department(user, department_id):
    """Người này có thuộc bộ phận đó không. Admin thì luôn đúng."""
    scope = get_user_scope(user)
    return scope.all_departments or department_id in scope.department_ids


def assert_rank(user, minimum, request=None):
    """Chặn nếu cấp bậc thấp hơn mức yêu cầu."""
    if not has_rank(user, minimum):
        record_denied(user, getattr(request, "path", ""), request)
        raise OutOfScopeError()


def assert_can_view(user, obj, request=None):
    """Chặn nếu bản ghi nằm ngoài phạm vi quyền.

    Dùng ở màn hình chi tiết. Không được thay bằng cách trả 404 hay danh
    sách rỗng — người dùng cần biết là bị từ chối, không phải là không có.
    """
    manager = getattr(type(obj), "objects", None)
    if manager is None or not hasattr(manager, "can_view"):
        raise OutOfScopeError()
    if not manager.can_view(user, obj):
        record_denied(user, getattr(request, "path", ""), request)
        raise OutOfScopeError()
    return True


class RankRequiredMixin(LoginRequiredMixin):
    """Mixin cho view cần cấp bậc tối thiểu.

    Đặt `minimum_rank` trên lớp view. Mọi view có phạm vi quyền phải dùng
    mixin này hoặc gọi `assert_rank` — không tự viết điều kiện kiểm riêng.
    """

    minimum_rank = Rank.STAFF

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            assert_rank(request.user, self.minimum_rank, request)
        return super().dispatch(request, *args, **kwargs)


class ScopedListMixin:
    """Mixin cho màn hình danh sách có phạm vi quyền.

    Luôn lấy dữ liệu qua `objects.in_scope(user)` và lấy sẵn dữ liệu liên
    quan trong cùng một lệnh (quy tắc 2).
    """

    select_related_fields = ()
    prefetch_related_fields = ()

    def get_queryset(self):
        qs = self.model.objects.in_scope(self.request.user)
        if self.select_related_fields:
            qs = qs.select_related(*self.select_related_fields)
        if self.prefetch_related_fields:
            qs = qs.prefetch_related(*self.prefetch_related_fields)
        return qs
