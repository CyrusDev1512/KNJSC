"""Ngưỡng màu ba bậc của Báo cáo tổng hợp (ADR-040 đợt 3): một cột JSON trên nguồn báo cáo,
rỗng mặc định — chạy ngược chỉ bỏ cột, không đụng dữ liệu nghiệp vụ."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0004_remove_report_unique_per_person_per_day"),
    ]

    operations = [
        migrations.AddField(
            model_name="reportsource",
            name="thresholds",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
