"""Thêm hành động "Sao lưu" vào nhật ký hoạt động — Giai đoạn 7.

Người vận hành lọc nhật ký theo "Sao lưu" là thấy đêm qua thành công hay
thất bại (docs/05 mục B3). Chỉ đổi danh sách lựa chọn, không đổi dữ liệu;
chạy ngược chỉ thu hẹp danh sách, bản ghi cũ giữ nguyên.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_backgroundjob"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditlog",
            name="action",
            field=models.CharField(
                choices=[
                    ("login", "Đăng nhập"),
                    ("login_failed", "Đăng nhập thất bại"),
                    ("logout", "Đăng xuất"),
                    ("create", "Tạo"),
                    ("update", "Sửa"),
                    ("delete", "Xoá"),
                    ("export", "Xuất dữ liệu"),
                    ("import", "Nhập dữ liệu"),
                    ("permission", "Đổi quyền"),
                    ("denied", "Từ chối truy cập"),
                    ("backup", "Sao lưu"),
                ],
                db_index=True,
                max_length=20,
                verbose_name="Hành động",
            ),
        ),
    ]
