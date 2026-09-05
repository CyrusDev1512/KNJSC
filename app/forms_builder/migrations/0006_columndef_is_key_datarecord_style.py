"""Cột khoá và định dạng ô — ADR-010.

Hai trường mới đều có giá trị mặc định nên chạy xuôi không đụng dữ liệu cũ;
chạy ngược chỉ bỏ cột và ràng buộc.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("forms_builder", "0005_fielddef_default_value"),
    ]

    operations = [
        migrations.AddField(
            model_name="columndef",
            name="is_key",
            field=models.BooleanField(
                default=False,
                help_text="Giá trị nhận diện dòng; bấm ô này trên Bảng tính để lọc nhanh. Mỗi bảng một cột.",
                verbose_name="Cột khoá",
            ),
        ),
        migrations.AddConstraint(
            model_name="columndef",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_key", True)),
                fields=("table",),
                name="column_key_unique_per_table",
            ),
        ),
        migrations.AddField(
            model_name="datarecord",
            name="style",
            field=models.JSONField(blank=True, default=dict, verbose_name="Định dạng ô"),
        ),
    ]
