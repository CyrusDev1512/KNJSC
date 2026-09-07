"""Manager của Tài nguyên.

Danh mục dùng chung toàn công ty (Q64): ai đăng nhập cũng xem được cả danh
sách, nên không có `in_scope`; manager chỉ loại bản ghi đã xoá mềm.
"""
from django.db import models

from core.managers import SoftDeleteQuerySet


class AliveManager(models.Manager):
    """Loại sẵn bản ghi đã đánh dấu xoá; muốn lấy cả thì dùng `all_objects`."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class CategoryManager(AliveManager.from_queryset(SoftDeleteQuerySet)):
    pass


class AllCategoryManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    pass


class ResourceManager(AliveManager.from_queryset(SoftDeleteQuerySet)):
    pass


class AllResourceManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    pass
