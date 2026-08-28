"""Cấu trúc dữ liệu lõi.

Mọi model nghiệp vụ kế thừa từ đây để có sẵn dấu thời gian, xoá mềm và
phạm vi quyền.
"""
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils import timezone

from .constants import AuditAction
from .managers import (
    AllObjectsManager, AuditQuerySet, ScopedManager, SoftDeleteQuerySet,
)


class TimestampedModel(models.Model):
    """Ghi lại lúc tạo và lúc sửa gần nhất.

    Lưu theo giờ quốc tế, hiển thị theo giờ Việt Nam (quy tắc 5).
    """

    created_at = models.DateTimeField("Tạo lúc", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("Sửa lúc", auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """Xoá là đánh dấu, không xoá cứng (BR-4)."""

    deleted_at = models.DateTimeField("Xoá lúc", null=True, blank=True, db_index=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Người xoá",
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+",
    )

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, by=None):
        """Đánh dấu xoá thay vì xoá khỏi cơ sở dữ liệu."""
        self.deleted_at = timezone.now()
        self.deleted_by = by
        self.save(update_fields=["deleted_at", "deleted_by", "updated_at"]
                  if hasattr(self, "updated_at") else ["deleted_at", "deleted_by"])

    def hard_delete(self, using=None):
        """Chỉ dùng cho tệp chuyển đổi dữ liệu và kiểm thử."""
        return super().delete(using=using)

    @property
    def is_deleted(self):
        return self.deleted_at is not None


class ScopedModel(TimestampedModel, SoftDeleteModel):
    """Model có phạm vi quyền.

    Truy vấn phải đi qua `objects.in_scope(user)`. Không viết điều kiện lọc
    quyền ở view (quy tắc 11).
    """

    # Tên ba cột mà manager dùng để áp phạm vi
    SCOPE_OWNER_FIELD = "created_by"
    SCOPE_TEAM_FIELD = "team"
    SCOPE_DEPARTMENT_FIELD = "department"

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Người tạo",
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+", db_index=True,
    )

    objects = ScopedManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True


class AuditLog(TimestampedModel):
    """Nhật ký hoạt động.

    Quy tắc BR-6: chỉ ghi thêm. Không ai được sửa hoặc xoá bản ghi ở đây,
    kể cả quản trị viên. Không ghi dữ liệu nhạy cảm vào cột `detail`.
    """

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Người thực hiện",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )
    actor_label = models.CharField("Tên người thực hiện", max_length=150, blank=True)
    action = models.CharField(
        "Hành động", max_length=20, choices=AuditAction.choices, db_index=True,
    )
    target_type = models.CharField("Loại đối tượng", max_length=80, blank=True, db_index=True)
    target_id = models.CharField("Mã đối tượng", max_length=80, blank=True, db_index=True)
    detail = models.CharField("Chi tiết", max_length=500, blank=True)
    ip_address = models.GenericIPAddressField("Địa chỉ IP", null=True, blank=True)

    objects = AuditQuerySet.as_manager()

    class Meta:
        verbose_name = "Nhật ký hoạt động"
        verbose_name_plural = "Nhật ký hoạt động"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action", "-created_at"], name="audit_action_time_idx"),
            models.Index(fields=["target_type", "target_id"], name="audit_target_idx"),
            # Cột tìm bằng __icontains — chỉ mục B-tree không phục vụ được kiểu
            # tìm này, phải dùng GIN với pg_trgm (quy tắc 9)
            GinIndex(
                name="audit_actor_label_trgm",
                fields=["actor_label"],
                opclasses=["gin_trgm_ops"],
            ),
        ]

    def __str__(self):
        # Lưu giờ quốc tế, hiển thị giờ Việt Nam — BR-7, quy tắc 5
        gio_vn = timezone.localtime(self.created_at) if self.created_at else None
        moc = f"{gio_vn:%d.%m.%Y %H:%M}" if gio_vn else "—"
        return f"{moc} · {self.actor_label} · {self.get_action_display()}"

    def save(self, *args, **kwargs):
        """Chỉ cho phép tạo mới. Sửa bản ghi nhật ký là vi phạm BR-6."""
        if self.pk is not None:
            raise RuntimeError("Không được sửa bản ghi nhật ký hoạt động (BR-6).")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("Không được xoá bản ghi nhật ký hoạt động (BR-6).")
