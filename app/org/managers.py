"""Manager áp phạm vi cho module org.

Hồ sơ nhân sự không kế thừa `ScopedModel` vì nó không bị xoá mềm và người
sở hữu chính là cột `user`. Nhưng phạm vi quyền vẫn phải áp qua đúng một
hàm chung — `core.managers.apply_scope`.

Bộ phận và team thì có xoá mềm, nên manager mặc định của chúng phải loại
sẵn bản ghi đã xoá — giống `ScopedManager`. Không làm vậy thì mọi nơi gọi
đều phải tự nhớ `.filter(deleted_at__isnull=True)`, quên một chỗ là bản ghi
đã xoá hiện trở lại.
"""
from django.db import models

from core.managers import SoftDeleteQuerySet, apply_department_scope, apply_scope


class ProfileQuerySet(models.QuerySet):
    def in_scope(self, user):
        """Staff thấy hồ sơ của chính mình, Leader thấy team mình phụ trách,
        Manager thấy cả bộ phận, Admin thấy tất cả."""
        return apply_scope(self, user, owner="user", team="team", department="department")

    def can_view(self, user, obj):
        return self.in_scope(user).filter(pk=obj.pk).exists()


class ProfileManager(models.Manager.from_queryset(ProfileQuerySet)):
    pass


class TeamQuerySet(SoftDeleteQuerySet):
    """Team vẫn phải xoá mềm (BR-4), nên kế thừa SoftDeleteQuerySet.

    Kế thừa thẳng `models.QuerySet` sẽ làm mất `delete()` xoá mềm và
    `hard_delete()` — đó là lỗi đã từng xảy ra ở đây.
    """

    def in_scope(self, user):
        """Manager thấy team của bộ phận mình, Leader thấy team mình phụ trách."""
        return apply_scope(self, user, owner="leader", team="pk", department="department")

    def can_view(self, user, obj):
        return self.in_scope(user).filter(pk=obj.pk).exists()


class DepartmentQuerySet(SoftDeleteQuerySet):
    def in_scope(self, user):
        """Mọi cấp bậc phi-admin chỉ thấy bộ phận của mình."""
        return apply_department_scope(self, user)

    def can_view(self, user, obj):
        return self.in_scope(user).filter(pk=obj.pk).exists()


class AliveManager(models.Manager):
    """Manager loại sẵn bản ghi đã đánh dấu xoá.

    Muốn lấy cả bản ghi đã xoá thì dùng `all_objects`.
    """

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class TeamManager(AliveManager.from_queryset(TeamQuerySet)):
    pass


class DepartmentManager(AliveManager.from_queryset(DepartmentQuerySet)):
    pass


class AllTeamManager(models.Manager.from_queryset(TeamQuerySet)):
    """Gồm cả team đã xoá. Dùng cho tệp chuyển đổi dữ liệu và kiểm thử."""


class AllDepartmentManager(models.Manager.from_queryset(DepartmentQuerySet)):
    """Gồm cả bộ phận đã xoá."""
