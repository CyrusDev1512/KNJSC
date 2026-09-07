"""Bỏ chỉ mục đơn trên cột ghim của bài Bảng tin.

Chỉ mục ghép `post_pinned_created_idx` (ghim, ngày tạo) đã phục vụ cả lọc theo
ghim lẫn thứ tự "ghim đứng đầu, mới nhất trước", nên chỉ mục đơn `is_pinned`
là thừa — mỗi lần ghi bài phải cập nhật thêm một chỉ mục vô ích. Đảo ngược
được: chạy lùi thì tạo lại chỉ mục đơn.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("feed", "0001_bang_tin"),
    ]

    operations = [
        migrations.AlterField(
            model_name="post",
            name="is_pinned",
            field=models.BooleanField(default=False, verbose_name="Ghim"),
        ),
    ]
