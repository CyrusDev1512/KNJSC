"""Rà toàn vẹn dữ liệu — chỉ đọc, trừ khi có `--sua`. Chạy trước và sau mỗi lần phát hành VPS.

    manage.py kiem_tra_du_lieu                 rà mọi bảng
    manage.py kiem_tra_du_lieu --bang van_don  rà một bảng
    manage.py kiem_tra_du_lieu --sua           tính lại cột tách / cột tính sẵn của bảng lệch

DB chưa chạy migration `forms_builder/0017` (vừa cập nhật mã): chỉ rà mã đơn trùng; `--sua` đổi mã các dòng thừa
thành `TRUNG-<số dòng>-<mã cũ>` (giữ dòng gắn đơn gốc) để migrate chạy được (TL-76).

Thoát mã 1 khi còn chỗ lệch, để kịch bản phát hành dừng được. Các phép rà ở `orders/services/integrity_service.py`.
"""
from django.core.management.base import BaseCommand, CommandError

from forms_builder.models import TableDef
from orders.services import integrity_service


class Command(BaseCommand):
    help = "Rà toàn vẹn dữ liệu: cột tách, mã đơn trùng, đơn mồ côi, sl_*, giá trị ngoài danh sách chọn."

    def add_arguments(self, parser):
        parser.add_argument("--bang", action="append", help="Mã bảng cần rà (lặp được). Bỏ trống: mọi bảng.")
        parser.add_argument("--sua", action="store_true", help="Tính lại cột tách và cột tính sẵn của bảng lệch; trước migration 0017 thì đổi mã các dòng trùng thừa.")

    def handle(self, *args, bang=None, sua=False, **options):
        tables = None
        if bang:
            tables = list(TableDef.all_objects.filter(code__in=bang))
            thieu = set(bang) - {t.code for t in tables}
            if thieu:
                raise CommandError("Không có bảng: " + ", ".join(sorted(thieu)))
        tong = integrity_service.run(tables=tables, fix=sua, on_line=self.stdout.write)
        if tong:
            self.stdout.write(f"Còn {tong} chỗ lệch.")
            raise SystemExit(1)
        self.stdout.write("Dữ liệu khớp.")
