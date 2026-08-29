"""Tạo bảng vận đơn theo đúng cấu trúc chuẩn.

Chạy được nhiều lần: đã có thì chỉ bổ sung cột còn thiếu.
"""
from django.core.management.base import BaseCommand

from orders.services import dispatch_service


class Command(BaseCommand):
    help = "Tạo hoặc bổ sung bảng vận đơn theo cấu trúc chuẩn"

    def handle(self, *args, **options):
        bang = dispatch_service.ensure_waybill_table()
        self.stdout.write(
            f"Bang {bang.code}: {bang.columns.count()} cot, bo phan {bang.department}"
        )
