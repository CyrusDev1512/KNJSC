"""Mã nhân sự trên hồ sơ — ADR-037.

Chạy xuôi: thêm cột `staff_code` (rỗng cho hồ sơ cũ) và ràng buộc duy nhất khi
khác rỗng; không gán mã ở đây — lệnh `gan_ma_nhan_su_cu` làm việc đó có kiểm.
Chạy ngược: bỏ ràng buộc và cột, mã đã gán mất theo cột.
"""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("org", "0004_accounting_department")]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="staff_code",
            field=models.CharField(blank=True, db_index=True, default="", max_length=20, verbose_name="Mã nhân sự"),
        ),
        migrations.AddConstraint(
            model_name="userprofile",
            constraint=models.UniqueConstraint(
                condition=models.Q(("staff_code", ""), _negated=True),
                fields=("staff_code",), name="profile_staff_code_unique",
            ),
        ),
    ]
