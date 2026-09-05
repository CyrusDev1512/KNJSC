"""Thư mục chứa bảng — ADR-010.

Chạy xuôi: thêm bảng `forms_builder_folder` và cột `folder_id` (rỗng) trên
định nghĩa bảng. Chạy ngược: bỏ cả hai, không đụng dữ liệu bảng.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("forms_builder", "0006_columndef_is_key_datarecord_style"),
        ("org", "0002_userprofile_profile_full_name_trgm"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Folder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Tạo lúc")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Sửa lúc")),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True, verbose_name="Xoá lúc")),
                ("name", models.CharField(max_length=120, verbose_name="Tên thư mục")),
                ("order", models.PositiveSmallIntegerField(default=0, verbose_name="Thứ tự")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL, verbose_name="Người tạo")),
                ("deleted_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL, verbose_name="Người xoá")),
                ("department", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="folders", to="org.department", verbose_name="Bộ phận")),
            ],
            options={
                "verbose_name": "Thư mục",
                "verbose_name_plural": "Thư mục",
                "ordering": ["department", "order", "name"],
            },
        ),
        migrations.AddConstraint(
            model_name="folder",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted_at__isnull", True)),
                fields=("department", "name"),
                name="folder_name_unique_per_department",
            ),
        ),
        migrations.AddField(
            model_name="tabledef",
            name="folder",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="tables", to="forms_builder.folder", verbose_name="Thư mục"),
        ),
    ]
