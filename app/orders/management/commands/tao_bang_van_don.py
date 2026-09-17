"""Tạo các bảng vận đơn theo đúng cấu trúc đã duyệt.

Chạy được nhiều lần: đã có thì chỉ bổ sung cột còn thiếu. Máy sạch chưa có
bộ phận Vận đơn thì tạo luôn, vì bảng phải thuộc về bộ phận đó. Lệnh này được
`deploy/entrypoint.sh` gọi ngay sau `migrate`, nên `docker compose up` trên
máy mới có cả bảng vận đơn chuẩn và Vận đơn DB, không cần nhớ chạy tay.
"""
from django.core.management.base import BaseCommand

from org.models import Department
from org.services import org_service
from orders.constants import WAYBILL_DEPARTMENT_CODE, WAYBILL_DEPARTMENT_NAME
from orders.services import dispatch_service, waybill_db_service


class Command(BaseCommand):
    help = "Tạo hoặc bổ sung các bảng vận đơn theo cấu trúc đã duyệt"

    def handle(self, *args, **options):
        if not Department.all_objects.filter(code=WAYBILL_DEPARTMENT_CODE).exists():
            org_service.create_department(
                name=WAYBILL_DEPARTMENT_NAME, code=WAYBILL_DEPARTMENT_CODE)
            self.stdout.write(f"Da tao bo phan {WAYBILL_DEPARTMENT_NAME}")
        bang = dispatch_service.ensure_waybill_table()
        self.stdout.write(
            f"Bang {bang.code}: {bang.columns.count()} cot, bo phan {bang.department}"
        )
        bang_db = waybill_db_service.ensure_table()
        self.stdout.write(
            f"Bang {bang_db.code}: {bang_db.columns.count()} cot, bo phan {bang_db.department}"
        )
