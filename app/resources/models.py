"""Tài nguyên dùng chung chia theo mục — FR-13.1 tới FR-13.4, ADR-015.

Danh mục là của toàn công ty (Q64): ai cũng xem, Manager trở lên sửa. Không
có cột mật khẩu và ghi chú bị chặn từ khoá bí mật (FR-13.4) — kho này trả
lời "có gì, ai giữ, tình trạng ra sao", không phải két sắt.
"""
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower

from core.models import SoftDeleteModel, TimestampedModel

from .constants import CATEGORY_NAME_MAX, LINK_MAX, NAME_MAX, NOTE_MAX, ResourceStatus
from .managers import AllCategoryManager, AllResourceManager, CategoryManager, ResourceManager


class ResourceCategory(TimestampedModel, SoftDeleteModel):
    """Mục tài nguyên: BM, Via, Page, Tài khoản QC, SIM…"""

    name = models.CharField("Tên mục", max_length=CATEGORY_NAME_MAX)
    order = models.PositiveSmallIntegerField("Thứ tự", default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Người tạo",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )

    objects = CategoryManager()
    all_objects = AllCategoryManager()

    class Meta:
        verbose_name = "Mục tài nguyên"
        verbose_name_plural = "Mục tài nguyên"
        ordering = ["order", "name"]
        constraints = [
            # Trùng tên (không phân biệt hoa thường) thì chặn, chỉ tính mục chưa xoá — BR-4
            models.UniqueConstraint(
                Lower("name"), condition=Q(deleted_at__isnull=True),
                name="resource_category_name_unique",
            ),
        ]

    def __str__(self):
        return self.name


class Resource(TimestampedModel, SoftDeleteModel):
    """Một tài nguyên: tên, mục, tình trạng, ai đang giữ."""

    category = models.ForeignKey(
        ResourceCategory, verbose_name="Mục", on_delete=models.PROTECT, related_name="resources",
    )
    name = models.CharField("Tên", max_length=NAME_MAX)
    note = models.CharField("Ghi chú", max_length=NOTE_MAX, blank=True)
    link = models.CharField("Liên kết", max_length=LINK_MAX, blank=True)
    status = models.CharField(
        "Trạng thái", max_length=12, choices=ResourceStatus.choices,
        default=ResourceStatus.TRONG, db_index=True,
    )
    holder = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Người giữ",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="resources_held", db_index=True,
    )
    department = models.ForeignKey(
        "org.Department", verbose_name="Bộ phận dùng",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="resources",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Người tạo",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )

    objects = ResourceManager()
    all_objects = AllResourceManager()

    class Meta:
        verbose_name = "Tài nguyên"
        verbose_name_plural = "Tài nguyên"
        ordering = ["category__order", "category__name", "name"]
        indexes = [
            models.Index(fields=["category", "status"], name="resource_cat_status_idx"),
            # Tìm theo tên dùng __icontains — cần GIN với pg_trgm (quy tắc 9)
            GinIndex(name="resource_name_trgm", fields=["name"], opclasses=["gin_trgm_ops"]),
        ]

    def __str__(self):
        return self.name
