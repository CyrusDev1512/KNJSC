"""Bỏ công tắc "Vận đơn xem toàn bảng" (ADR-026): từ 17.09.2026 nhân viên Vận
đơn luôn thấy toàn bảng, lọc "Tôi" là việc của lưới — ADR-033. Đảo ngược được:
Django thêm lại cột với mặc định False. Giữ `delivery_view_version` vì
`destination_service` vẫn dùng để ép tab tải lại khi đổi bảng nhận đơn.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("forms_builder", "0012_order_destination"),
    ]

    operations = [
        migrations.RemoveField(model_name="tabledef", name="delivery_view_all"),
    ]
