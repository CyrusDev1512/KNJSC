"""Custom Manager áp phạm vi quyền.

Quy tắc 11: dữ liệu có phạm vi quyền phải đi qua manager này, không được
gọi `.objects.filter()` trực tiếp ở view. Quy tắc 1 và 3 trong bảng cấm:
phạm vi phải áp ở một chỗ duy nhất, tại tầng truy cập dữ liệu.

Mỗi model có phạm vi khai báo tên ba cột của nó:

    SCOPE_OWNER_FIELD       cột trỏ tới người tạo
    SCOPE_TEAM_FIELD        cột trỏ tới team, để None nếu không có
    SCOPE_DEPARTMENT_FIELD  cột trỏ tới bộ phận
"""
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .constants import Rank
from .scope import get_user_scope


class SoftDeleteQuerySet(models.QuerySet):
    """Xoá là đánh dấu, không xoá cứng (BR-4)."""

    def delete(self, by=None):
        """Đánh dấu xoá cả lô, ghi luôn người xoá.

        Bản đầu bỏ quên `deleted_by`, nên xoá theo lô thì mất dấu ai xoá —
        khác hẳn `SoftDeleteModel.delete()` vốn có ghi.
        """
        return self.update(deleted_at=timezone.now(), deleted_by=by)

    def hard_delete(self):
        """Chỉ dùng cho tệp chuyển đổi dữ liệu và kiểm thử."""
        return super().delete()

    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)


def apply_scope(queryset, user, *, owner, team=None, department=None):
    """Áp phạm vi quyền lên một queryset bất kỳ.

    Đây là chỗ duy nhất biết cách biến `Scope` thành điều kiện lọc. Mọi
    manager có phạm vi quyền đều gọi vào đây, kể cả model không kế thừa
    `ScopedModel` — ví dụ hồ sơ nhân sự bên module org.

        owner       đường dẫn tới người sở hữu bản ghi
        team        đường dẫn tới team, None nếu model không có
        department  đường dẫn tới bộ phận, None nếu model không có

    Ba tham số nhận **đường dẫn truy vấn của Django**, không phải tên cột thô.
    Bản đầu tự nối hậu tố `_id` vào tên, khiến `team="id"` sinh ra `id_id__in`
    — một cột không tồn tại. Giờ truyền thẳng `team="pk"` là chạy đúng.
    """
    scope = get_user_scope(user)
    if scope.all_departments:
        return queryset

    if scope.rank == Rank.MANAGER and department:
        return queryset.filter(**{f"{department}__in": scope.department_ids})

    if scope.rank == Rank.LEADER and team:
        # Team mình phụ trách, cộng thêm bản ghi của chính mình
        return queryset.filter(
            Q(**{f"{team}__in": scope.team_ids})
            | Q(**{owner: scope.user_id})
        )

    # Staff, và mọi trường hợp model không khai báo đủ cột
    return queryset.filter(**{owner: scope.user_id})


def apply_department_scope(queryset, user, *, field="pk"):
    """Áp phạm vi cho chính bảng Bộ phận.

    Bộ phận không có người tạo và không có team, nên không dùng được
    `apply_scope`. Mọi cấp bậc phi-admin chỉ thấy bộ phận của mình.
    """
    scope = get_user_scope(user)
    if scope.all_departments:
        return queryset
    return queryset.filter(**{f"{field}__in": scope.department_ids})


class ScopedQuerySet(SoftDeleteQuerySet):
    def in_scope(self, user):
        """Lọc còn lại đúng những bản ghi người này được xem.

        Trả về queryset đã lọc. Nếu người dùng không có phạm vi nào thì
        view phải trả lỗi từ chối, không hiển thị danh sách rỗng (FR-3.5).
        """
        model = self.model
        return apply_scope(
            self, user,
            owner=getattr(model, "SCOPE_OWNER_FIELD", "created_by"),
            team=getattr(model, "SCOPE_TEAM_FIELD", None),
            department=getattr(model, "SCOPE_DEPARTMENT_FIELD", None),
        )

    def can_view(self, user, obj):
        """Kiểm một bản ghi cụ thể có nằm trong phạm vi không."""
        return self.in_scope(user).filter(pk=obj.pk).exists()


class AuditQuerySet(models.QuerySet):
    """Nhật ký cũng có phạm vi: mỗi người chỉ xem được hoạt động của những
    người nằm trong phạm vi của mình.

    Lọc theo `actor__profile__...` bằng chuỗi nên core không phải import
    module org — giữ đúng chiều phụ thuộc.
    """

    #: Nhật ký chỉ ghi thêm. Chặn ở cả mức đối tượng lẫn mức queryset —
    #: chặn mỗi mức đối tượng thì `AuditLog.objects.filter(...).delete()`
    #: vẫn xoá cứng được, tức là BR-6 hở.
    def delete(self):
        raise RuntimeError("Không được xoá bản ghi nhật ký hoạt động (BR-6).")

    def update(self, **kwargs):
        raise RuntimeError("Không được sửa bản ghi nhật ký hoạt động (BR-6).")

    def in_scope(self, user):
        return apply_scope(
            self, user,
            owner="actor",
            team="actor__profile__team",
            department="actor__profile__department",
        )


class ScopedManager(models.Manager.from_queryset(ScopedQuerySet)):
    """Manager mặc định của model có phạm vi quyền.

    Đã loại sẵn bản ghi bị đánh dấu xoá. Muốn lấy cả bản ghi đã xoá thì
    dùng `all_objects`.
    """

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllObjectsManager(models.Manager.from_queryset(ScopedQuerySet)):
    """Lấy mọi bản ghi kể cả đã đánh dấu xoá. Dùng cho tệp chuyển đổi và quản trị."""
