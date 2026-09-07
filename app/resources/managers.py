"""Manager của Tài nguyên.

Danh mục dùng chung toàn công ty (Q64): ai đăng nhập cũng xem được cả danh
sách, nên không có `in_scope`; manager chỉ loại bản ghi đã xoá mềm.
"""
from django.db import models

from core.managers import AliveManager, SoftDeleteQuerySet


class CategoryManager(AliveManager.from_queryset(SoftDeleteQuerySet)):
    pass


class AllCategoryManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    pass


class ResourceManager(AliveManager.from_queryset(SoftDeleteQuerySet)):
    pass


class AllResourceManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    pass
