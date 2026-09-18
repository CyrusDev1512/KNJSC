"""ADR-036 — một bảng vận đơn duy nhất: bỏ cờ `receives_orders` và ràng buộc
`one_order_destination` của Bảng nhận đơn (ADR-029/034). Đảo được: thêm lại cột
mặc định False và ràng buộc."""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("forms_builder", "0013_remove_tabledef_delivery_view_all"),
    ]

    operations = [
        migrations.RemoveConstraint(model_name="tabledef", name="one_order_destination"),
        migrations.RemoveField(model_name="tabledef", name="receives_orders"),
    ]
