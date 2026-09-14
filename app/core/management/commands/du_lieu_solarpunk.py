"""Dữ liệu tổng hợp để nghiệm thu UI; chỉ chạy ở database preview riêng."""
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from forms_builder.models import FormDef
from orders.models import Product
from orders.services import order_service
from reports.services import daily_service


class Command(BaseCommand):
    help = "Tạo báo cáo và đơn tổng hợp trong môi trường Solarpunk riêng"

    def handle(self, *args, **options):
        if settings.SETTINGS_MODULE != 'knjsc.settings.solarpunk_preview' or settings.DATABASES['default']['NAME'] != 'solarpunk':
            raise CommandError('Chỉ chạy trên settings và database preview Solarpunk.')
        users = get_user_model()
        actor = users.objects.get(username='mkt.staff')
        form = FormDef.objects.get(code='bc_mkt_ngay')
        today = timezone.localdate()
        for offset in range(5):
            day = today-timedelta(days=offset)
            if not daily_service.already_submitted(form, actor, day):
                daily_service.submit(form, {'ngay':day.isoformat(),'marketer':actor.profile.full_name,'so_mess':'240','cpqc':'1250000','so_don':'32','doanh_so':'18400000'},report_date=day,actor=actor)
        product, _ = Product.objects.get_or_create(code='SOLAR-TEST', defaults={'name':'Sản phẩm kiểm thử Solarpunk'})
        from orders.models import Order
        count = Order.objects.filter(customer__name__startswith='Khách mẫu Solarpunk').count()
        for i in range(count, 120):
            order_service.create_order(phone=f'090099{i:04}',customer_name=f'Khách mẫu Solarpunk {i+1:03}',
                lines=[{'product':product.code,'quantity':1+i%3,'unit_price':'125000'}],
                actor=users.objects.get(username='sale.staff' if i%2==0 else 'sale.staff2'))
        self.stdout.write(self.style.SUCCESS('Đã chuẩn bị báo cáo và 120 đơn tổng hợp.'))
