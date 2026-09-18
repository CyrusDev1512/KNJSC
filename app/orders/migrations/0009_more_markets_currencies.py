"""Bảy thị trường, tám loại tiền — ADR-031 bổ sung 18.09.2026.

Chỉ đổi `choices` của `Order.market` và `Order.currency` trong trạng thái migration;
SQL là no-op, không đụng dòng đơn đã có. Chạy ngược trả lại ba nước / bốn loại tiền.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0008_market_payment_methods"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="currency",
            field=models.CharField(
                choices=[
                    ("VND", "Việt Nam đồng"),
                    ("USD", "Đô la Mỹ"),
                    ("CAD", "Đô la Canada"),
                    ("PHP", "Peso Philippines"),
                    ("EUR", "Euro"),
                    ("KRW", "Won Hàn Quốc"),
                    ("JPY", "Yên Nhật"),
                    ("AUD", "Đô la Úc"),
                ],
                default="USD",
                max_length=3,
                verbose_name="Loại tiền tệ",
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="market",
            field=models.CharField(
                choices=[
                    ("us", "Hoa Kỳ"),
                    ("ca", "Canada"),
                    ("ph", "Philippines"),
                    ("eu", "Châu Âu"),
                    ("kr", "Hàn Quốc"),
                    ("jp", "Nhật Bản"),
                    ("au", "Úc"),
                ],
                db_index=True,
                default="us",
                max_length=4,
                verbose_name="Quốc gia",
            ),
        ),
    ]
