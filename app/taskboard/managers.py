"""Manager áp phạm vi cho Công việc — một chỗ duy nhất (quy tắc 11), FR-11.3.

Khác `apply_scope` ở chỗ một việc có hai người liên quan: người tạo và
người làm. Staff thấy việc mình nhận hoặc tạo; Leader thấy việc của team
(người làm hoặc người tạo trong team) cộng việc của mình; Manager cả bộ
phận; Admin tất cả.
"""
from django.db import models
from django.db.models import Q

from core.constants import Rank
from core.managers import SoftDeleteQuerySet
from core.scope import get_user_scope


class TaskQuerySet(SoftDeleteQuerySet):
    def in_scope(self, user):
        scope = get_user_scope(user)
        if scope.all_departments:
            return self
        cua_minh = Q(assignee_id=scope.user_id) | Q(created_by_id=scope.user_id)
        if scope.rank == Rank.MANAGER:
            return self.filter(Q(department_id__in=scope.department_ids) | cua_minh)
        if scope.rank == Rank.LEADER:
            return self.filter(
                Q(assignee__profile__team_id__in=scope.team_ids)
                | Q(created_by__profile__team_id__in=scope.team_ids)
                | cua_minh
            )
        return self.filter(cua_minh)

    def can_view(self, user, obj):
        return self.in_scope(user).filter(pk=obj.pk).exists()


class TaskManager(models.Manager.from_queryset(TaskQuerySet)):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllTaskManager(models.Manager.from_queryset(TaskQuerySet)):
    """Gồm cả việc đã gỡ. Dùng cho tệp chuyển đổi và kiểm thử."""
