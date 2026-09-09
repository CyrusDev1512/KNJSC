import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('forms_builder', '0009_record_updated_phone_idx'),
        ('orders', '0002_trang_thai_van_don_va_tien_te'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name='WaybillItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Tạo lúc')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Sửa lúc')),
                ('deleted_at', models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='Xoá lúc')),
                ('quantity', models.PositiveIntegerField(verbose_name='Số lượng')),
                ('unit_price', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=18, verbose_name='Đơn giá')),
                ('paid_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=18, verbose_name='Đã thanh toán')),
                ('deleted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Người xoá')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='orders.product')),
                ('record', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='waybill_items', to='forms_builder.datarecord')),
            ],
            options={
                'ordering': ['pk'],
                'constraints': [
                    models.CheckConstraint(condition=models.Q(quantity__gt=0), name='waybill_item_quantity_positive'),
                    models.CheckConstraint(condition=models.Q(unit_price__gte=0), name='waybill_item_price_nonnegative'),
                    models.CheckConstraint(condition=models.Q(paid_amount__gte=0), name='waybill_item_paid_nonnegative'),
                ],
            },
        ),
    ]
