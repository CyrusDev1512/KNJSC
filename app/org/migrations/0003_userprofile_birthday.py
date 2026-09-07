"""Ngày sinh trên hồ sơ nhân sự — FR-10.4, ADR-015.

Chạy xuôi: thêm cột `birthday` (ngày, được trống, có chỉ mục) vào
`org_userprofile`; hồ sơ cũ để trống nên không đổi gì. Chạy ngược: bỏ cột.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("org", "0002_userprofile_profile_full_name_trgm"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="birthday",
            field=models.DateField(blank=True, db_index=True, null=True, verbose_name="Ngày sinh"),
        ),
    ]
