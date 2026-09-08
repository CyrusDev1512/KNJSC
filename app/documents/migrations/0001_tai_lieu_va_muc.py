"""Mục tài liệu và tài liệu — FR-9.1 tới FR-9.5, ADR-017.

Chạy xuôi: tạo hai bảng `documents_documentcategory` và `documents_document`
kèm chỉ mục (mục, ngày), (bộ phận, ngày) và GIN trigram trên tiêu đề, ràng
buộc tên mục duy nhất trong cùng phạm vi khi chưa xoá. Chạy ngược: bỏ hai
bảng; tệp trong `storage/tai-lieu/` giữ nguyên trên đĩa.
"""
import django.contrib.postgres.indexes
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        # Chỉ mục GIN dùng gin_trgm_ops, nên phần mở rộng pg_trgm phải bật trước
        ("core", "0002_pg_trgm"),
        ("org", "0003_userprofile_birthday"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentCategory",
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
                ("name", models.CharField(max_length=120, verbose_name="Tên mục")),
                (
                    "order",
                    models.PositiveSmallIntegerField(default=0, verbose_name="Thứ tự"),
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
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="document_categories",
                        to="org.department",
                        verbose_name="Bộ phận",
                    ),
                ),
            ],
            options={
                "verbose_name": "Mục tài liệu",
                "verbose_name_plural": "Mục tài liệu",
                "ordering": ["order", "name"],
            },
        ),
        migrations.CreateModel(
            name="Document",
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
                (
                    "description",
                    models.CharField(blank=True, max_length=500, verbose_name="Mô tả"),
                ),
                (
                    "file_path",
                    models.CharField(
                        blank=True, max_length=300, verbose_name="Đường dẫn tệp"
                    ),
                ),
                (
                    "file_name",
                    models.CharField(
                        blank=True, max_length=200, verbose_name="Tên tệp gốc"
                    ),
                ),
                (
                    "file_kind",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("xlsx", "Excel"),
                            ("csv", "CSV"),
                            ("jpg", "Ảnh JPG"),
                            ("png", "Ảnh PNG"),
                            ("pdf", "PDF"),
                            ("docx", "Word"),
                        ],
                        max_length=8,
                        verbose_name="Loại tệp",
                    ),
                ),
                (
                    "file_size",
                    models.PositiveIntegerField(
                        default=0, verbose_name="Cỡ tệp (byte)"
                    ),
                ),
                (
                    "link",
                    models.URLField(
                        blank=True, max_length=500, verbose_name="Liên kết"
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
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="documents",
                        to="org.department",
                        verbose_name="Bộ phận",
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="documents",
                        to="documents.documentcategory",
                        verbose_name="Mục",
                    ),
                ),
            ],
            options={
                "verbose_name": "Tài liệu",
                "verbose_name_plural": "Tài liệu",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="documentcategory",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted_at__isnull", True)),
                fields=("department", "name"),
                name="doc_category_name_unique",
                nulls_distinct=False,
            ),
        ),
        migrations.AddIndex(
            model_name="document",
            index=models.Index(
                fields=["category", "-created_at"], name="document_cat_created_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="document",
            index=models.Index(
                fields=["department", "-created_at"], name="document_dept_created_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="document",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["title"], name="document_title_trgm", opclasses=["gin_trgm_ops"]
            ),
        ),
    ]
