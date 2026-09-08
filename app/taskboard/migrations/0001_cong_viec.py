"""Việc trong bộ phận — FR-11.1 tới FR-11.5, ADR-017.

Chạy xuôi: tạo bảng `taskboard_task` kèm chỉ mục (bộ phận, trạng thái, ngày),
(người làm, trạng thái), (người tạo, ngày). Chạy ngược: bỏ bảng.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("org", "0003_userprofile_birthday"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Task",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, db_index=True, verbose_name="Tạo lúc"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Sửa lúc"),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True, db_index=True, null=True, verbose_name="Xoá lúc"
                    ),
                ),
                ("title", models.CharField(max_length=200, verbose_name="Tiêu đề")),
                ("description", models.TextField(blank=True, verbose_name="Mô tả")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("moi", "Mới"),
                            ("dang_lam", "Đang làm"),
                            ("xong", "Xong"),
                            ("huy", "Huỷ"),
                        ],
                        db_index=True,
                        default="moi",
                        max_length=12,
                        verbose_name="Trạng thái",
                    ),
                ),
                (
                    "priority",
                    models.CharField(
                        choices=[("thap", "Thấp"), ("vua", "Vừa"), ("cao", "Cao")],
                        default="vua",
                        max_length=8,
                        verbose_name="Ưu tiên",
                    ),
                ),
                (
                    "due_date",
                    models.DateField(
                        blank=True, db_index=True, null=True, verbose_name="Hạn"
                    ),
                ),
                (
                    "done_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Xong lúc"
                    ),
                ),
                (
                    "assignee",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="tasks_assigned",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Người làm",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Người tạo",
                    ),
                ),
                (
                    "deleted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Người xoá",
                    ),
                ),
                (
                    "department",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="tasks",
                        to="org.department",
                        verbose_name="Bộ phận",
                    ),
                ),
            ],
            options={
                "verbose_name": "Việc",
                "verbose_name_plural": "Việc",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["department", "status", "-created_at"],
                        name="task_dept_status_idx",
                    ),
                    models.Index(
                        fields=["assignee", "status"], name="task_assignee_status_idx"
                    ),
                    models.Index(
                        fields=["created_by", "-created_at"],
                        name="task_creator_created_idx",
                    ),
                ],
            },
        ),
    ]
