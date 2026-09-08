"""Tài liệu chia theo mục — FR-9.1 tới FR-9.5, ADR-017.

Tệp không dùng `FileField`: lưu tay dưới `STORAGE_DIR/tai-lieu/` và giữ
đường dẫn tương đối, như luồng nhập tệp của forms_builder. Tải về đi qua
view có kiểm quyền, không có đường tĩnh (FR-9.3).
"""
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower

from core.constants import FileKind
from core.models import ScopedModel, SoftDeleteModel, TimestampedModel

from .constants import CATEGORY_NAME_MAX, DESCRIPTION_MAX, FILE_NAME_MAX, TITLE_MAX
from .managers import AllCategoryManager, AllDocumentManager, CategoryManager, DocumentManager


class DocumentCategory(TimestampedModel, SoftDeleteModel):
    """Mục tài liệu. Bộ phận trống nghĩa là dùng chung toàn công ty."""

    name = models.CharField("Tên mục", max_length=CATEGORY_NAME_MAX)
    department = models.ForeignKey(
        "org.Department", verbose_name="Bộ phận",
        null=True, blank=True, on_delete=models.PROTECT,
        related_name="document_categories",
    )
    order = models.PositiveSmallIntegerField("Thứ tự", default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Người tạo",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )

    objects = CategoryManager()
    all_objects = AllCategoryManager()

    class Meta:
        verbose_name = "Mục tài liệu"
        verbose_name_plural = "Mục tài liệu"
        ordering = ["order", "name"]
        constraints = [
            # Trùng tên trong cùng bộ phận (kể cả cùng "toàn công ty") thì
            # chặn, không phân biệt hoa thường, chỉ tính mục chưa xoá — BR-4
            models.UniqueConstraint(
                Lower("name"), F("department"), nulls_distinct=False,
                condition=Q(deleted_at__isnull=True),
                name="doc_category_name_unique",
            ),
        ]

    def __str__(self):
        return self.name

    @property
    def pham_vi(self):
        return self.department.name if self.department_id else "Toàn công ty"


class Document(ScopedModel):
    """Một tài liệu: tệp đã tải lên, hoặc chỉ là liên kết."""

    # Phạm vi theo mục (bộ phận hoặc toàn công ty), viết ở managers.py — không dùng SCOPE_*

    title = models.CharField("Tiêu đề", max_length=TITLE_MAX)
    category = models.ForeignKey(
        DocumentCategory, verbose_name="Mục", on_delete=models.PROTECT,
        related_name="documents",
    )
    # Chép từ mục lúc tạo để lọc phạm vi không phải join
    department = models.ForeignKey(
        "org.Department", verbose_name="Bộ phận",
        null=True, blank=True, on_delete=models.PROTECT, related_name="documents",
    )
    description = models.CharField("Mô tả", max_length=DESCRIPTION_MAX, blank=True)
    file_path = models.CharField("Đường dẫn tệp", max_length=300, blank=True)
    file_name = models.CharField("Tên tệp gốc", max_length=FILE_NAME_MAX, blank=True)
    file_kind = models.CharField("Loại tệp", max_length=8, choices=FileKind.choices, blank=True)
    file_size = models.PositiveIntegerField("Cỡ tệp (byte)", default=0)
    link = models.URLField("Liên kết", max_length=500, blank=True)

    objects = DocumentManager()
    all_objects = AllDocumentManager()

    class Meta:
        verbose_name = "Tài liệu"
        verbose_name_plural = "Tài liệu"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category", "-created_at"], name="document_cat_created_idx"),
            models.Index(fields=["department", "-created_at"], name="document_dept_created_idx"),
            # Tìm theo tiêu đề dùng __icontains — cần GIN với pg_trgm (quy tắc 9)
            GinIndex(name="document_title_trgm", fields=["title"], opclasses=["gin_trgm_ops"]),
        ]

    def __str__(self):
        return self.title

    @property
    def la_lien_ket(self):
        return not self.file_path
