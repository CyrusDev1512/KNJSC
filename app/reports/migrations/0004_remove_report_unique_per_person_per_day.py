"""Bỏ khoá "một bản/người/ngày" của báo cáo hằng ngày — ADR-038.

Chạy xuôi: bỏ ràng buộc `report_unique_per_person_per_day`; dữ liệu giữ nguyên.
Chạy ngược: thêm lại ràng buộc — **thất bại nếu đã có người nộp nhiều lần trong
ngày**; khi đó quay lui bằng backup, không xoá bản nộp của ai.
"""
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("reports", "0003_report_revision")]

    operations = [
        migrations.RemoveConstraint(
            model_name="dailyreport",
            name="report_unique_per_person_per_day",
        ),
    ]
