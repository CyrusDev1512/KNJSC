"""Tạo bảng vận đơn theo đúng cấu trúc chuẩn.

Chạy được nhiều lần: đã có thì chỉ bổ sung cột còn thiếu. Máy sạch chưa có
bộ phận Vận đơn thì tạo luôn, vì bảng phải thuộc về bộ phận đó. Lệnh này được
`deploy/entrypoint.sh` gọi ngay sau `migrate`, nên `docker compose up` trên
máy mới là có bảng, không cần nhớ chạy tay.
"""
from django.core.management.base import BaseCommand

from org.models import Department
from org.services import org_service
from orders.constants import WAYBILL_DEPARTMENT_CODE, WAYBILL_DEPARTMENT_NAME
from orders.services import dispatch_service


class Command(BaseCommand):
    help = "Tạo hoặc bổ sung bảng vận đơn theo cấu trúc chuẩn"

    def handle(self, *args, **options):
        if not Department.all_objects.filter(code=WAYBILL_DEPARTMENT_CODE).exists():
            org_service.create_department(
                name=WAYBILL_DEPARTMENT_NAME, code=WAYBILL_DEPARTMENT_CODE)
            self.stdout.write(f"Da tao bo phan {WAYBILL_DEPARTMENT_NAME}")
        bang = dispatch_service.ensure_waybill_table()
        self.stdout.write(
            f"Bang {bang.code}: {bang.columns.count()} cot, bo phan {bang.department}"
        )
