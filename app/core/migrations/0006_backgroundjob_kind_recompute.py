"""Thêm loại tác vụ nền "Tính lại cột" (ADR-016). Chỉ đổi danh sách chọn, đảo ngược được."""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0005_auditlog_action_backup")]

    operations = [
        migrations.AlterField(
            model_name="backgroundjob",
            name="kind",
            field=models.CharField(
                choices=[("import", "Nhập tệp"), ("export", "Xuất tệp"), ("backup", "Sao lưu"),
                         ("cleanup", "Dọn dẹp"), ("recompute", "Tính lại cột")],
                db_index=True, max_length=12, verbose_name="Loại",
            ),
        ),
    ]
