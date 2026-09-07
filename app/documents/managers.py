"""Manager áp phạm vi cho Tài liệu — một chỗ duy nhất (quy tắc 11).

Mục và tài liệu không có "người sở hữu" theo nghĩa phạm vi dữ liệu: mục
toàn công ty (bộ phận trống) ai cũng thấy, mục của bộ phận thì người trong
bộ phận đó thấy, Admin thấy tất cả. Luật này khác `apply_scope` (Staff chỉ
thấy của mình) nên viết riêng ở đây, không rải ra view.
"""
from django.db import models
from django.db.models import Q

from core.managers import SoftDeleteQuerySet
from core.scope import get_user_scope


def _theo_bo_phan(queryset, user):
    scope = get_user_scope(user)
    if scope.all_departments:
        return queryset
    return queryset.filter(
        Q(department__isnull=True) | Q(department_id__in=scope.department_ids)
    )


class CategoryQuerySet(SoftDeleteQuerySet):
    def in_scope(self, user):
        return _theo_bo_phan(self, user)

    def can_view(self, user, obj):
        return self.in_scope(user).filter(pk=obj.pk).exists()


class DocumentQuerySet(SoftDeleteQuerySet):
    def in_scope(self, user):
        return _theo_bo_phan(self, user)

    def can_view(self, user, obj):
        return self.in_scope(user).filter(pk=obj.pk).exists()


class AliveManager(models.Manager):
    """Loại sẵn bản ghi đã đánh dấu xoá; muốn lấy cả thì dùng `all_objects`."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class CategoryManager(AliveManager.from_queryset(CategoryQuerySet)):
    pass


class AllCategoryManager(models.Manager.from_queryset(CategoryQuerySet)):
    pass


class DocumentManager(AliveManager.from_queryset(DocumentQuerySet)):
    pass


class AllDocumentManager(models.Manager.from_queryset(DocumentQuerySet)):
    pass
