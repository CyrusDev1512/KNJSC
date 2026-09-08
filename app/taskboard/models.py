"""Việc trong bộ phận — FR-11.1 tới FR-11.5, ADR-017."""
from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import ScopedModel

from .constants import OPEN_STATUSES, TITLE_MAX, TaskPriority, TaskStatus
from .managers import AllTaskManager, TaskManager


class Task(ScopedModel):
    """Một việc: ai tạo, ai làm, trạng thái, ưu tiên, hạn."""

    # Phạm vi có hai người liên quan, viết riêng ở managers.py — không dùng SCOPE_*

    title = models.CharField("Tiêu đề", max_length=TITLE_MAX)
    description = models.TextField("Mô tả", blank=True)
    department = models.ForeignKey(
        "org.Department", verbose_name="Bộ phận", on_delete=models.PROTECT,
        related_name="tasks",
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Người làm",
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="tasks_assigned", db_index=True,
    )
    status = models.CharField(
        "Trạng thái", max_length=12, choices=TaskStatus.choices,
        default=TaskStatus.MOI, db_index=True,
    )
    priority = models.CharField(
        "Ưu tiên", max_length=8, choices=TaskPriority.choices, default=TaskPriority.VUA,
    )
    due_date = models.DateField("Hạn", null=True, blank=True, db_index=True)
    done_at = models.DateTimeField("Xong lúc", null=True, blank=True)

    objects = TaskManager()
    all_objects = AllTaskManager()

    class Meta:
        verbose_name = "Việc"
        verbose_name_plural = "Việc"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["department", "status", "-created_at"], name="task_dept_status_idx"),
            models.Index(fields=["assignee", "status"], name="task_assignee_status_idx"),
            models.Index(fields=["created_by", "-created_at"], name="task_creator_created_idx"),
        ]

    def __str__(self):
        return self.title

    @property
    def qua_han(self):
        """Còn mở mà đã qua hạn (theo ngày Việt Nam)."""
        return (
            self.due_date is not None
            and self.status in OPEN_STATUSES
            and self.due_date < timezone.localdate()
        )
