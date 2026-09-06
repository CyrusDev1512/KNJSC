"""Danh sách chọn, màu cột và ngưỡng cảnh báo trên định nghĩa cột — FR-8.7, FR-8.8.

Chạy xuôi: bốn cột mới trên `forms_builder_columndef`, đều có giá trị mặc định
nên bản ghi cũ không đổi. Chạy ngược: bỏ bốn cột, không đụng dữ liệu bảng.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("forms_builder", "0007_folder_tabledef_folder"),
    ]

    operations = [
        migrations.AddField(
            model_name="columndef",
            name="alert_op",
            field=models.CharField(
                blank=True,
                choices=[
                    ("gt", "Đỏ khi lớn hơn ngưỡng"),
                    ("lt", "Đỏ khi nhỏ hơn ngưỡng"),
                ],
                default="",
                help_text="Chỉ cho cột kiểu số. Ô vượt ngưỡng tô đỏ, ô đạt tô xanh lá.",
                max_length=2,
                verbose_name="Cảnh báo",
            ),
        ),
        migrations.AddField(
            model_name="columndef",
            name="alert_value",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=18,
                null=True,
                verbose_name="Ngưỡng",
            ),
        ),
        migrations.AddField(
            model_name="columndef",
            name="highlight",
            field=models.CharField(
                blank=True,
                choices=[
                    ("vang", "Vàng"),
                    ("do", "Đỏ"),
                    ("luc", "Xanh lá"),
                    ("xanh", "Xanh dương"),
                ],
                default="",
                help_text="Tô nền tiêu đề và mọi ô của cột trên Bảng dữ liệu.",
                max_length=8,
                verbose_name="Màu cột",
            ),
        ),
        migrations.AddField(
            model_name="columndef",
            name="options",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Giá trị được chọn của cột kiểu Chọn một. Manager quản lý, người điền chỉ chọn.",
                verbose_name="Danh sách chọn",
            ),
        ),
    ]
