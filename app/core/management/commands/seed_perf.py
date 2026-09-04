"""Sinh dữ liệu giả để đo hiệu năng — AC-7.1, NFR-1, backlog K6.

    python manage.py seed_perf                 # 50.000 dòng vận đơn
    python manage.py seed_perf --so-dong 5000
    python manage.py seed_perf --xoa-cu        # xoá dòng giả cũ trước khi sinh

Dòng giả nhận ra được bằng mã đơn `PERF-…`, nên xoá lại được mà không đụng
dữ liệu thật. Số liệu sinh **có chủ đích** giống dữ liệu thật: số điện thoại
trùng ~20% (cột Lọc trùng có việc để làm), đủ tám trạng thái, ngày trải 12
tháng, số lượng từng sản phẩm. Ngẫu nhiên theo hạt giống cố định để hai máy
sinh ra cùng một bộ.

Không chạy trên máy chủ thật khi DEBUG tắt — cùng khoá với `du_lieu_mau`.
"""
import random
from datetime import date, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.constants import PERF_TABLE_ROWS
from forms_builder.models import DataRecord

PERF_PREFIX = "PERF-"
HAT_GIONG = 20260903
TEN = ["Nguyễn Văn An", "Trần Thị Bình", "Lê Minh Châu", "Phạm Quốc Dũng", "Hoàng Thu Hà",
       "Taylor Minh", "Emily Tran", "Daniel Pham", "Sarah Le", "Jordan Nguyen"]
THANH_PHO = [("Calgary", "AB"), ("Toronto", "ON"), ("Vancouver", "BC"), ("Montreal", "QC"),
             ("Edmonton", "AB"), ("Ottawa", "ON")]


def rows(n, *, products, sellers, statuses, payments, staff, start=date(2025, 9, 1), seed=HAT_GIONG):
    """Sinh `n` dict giá trị cho bảng vận đơn. Dùng chung với bài kiểm hiệu năng."""
    rng = random.Random(seed)
    so_khach = max(n // 5 * 4, 1)                 # ~20% số điện thoại trùng
    for i in range(n):
        khach = rng.randrange(so_khach)
        thanh_pho, bang = rng.choice(THANH_PHO)
        gia_tri = {
            "ma_don": f"{PERF_PREFIX}{i + 1:06d}",
            "ngay": (start + timedelta(days=rng.randrange(365))).isoformat(),
            "ten_khach": f"{rng.choice(TEN)} {khach}",
            "so_dien_thoai": f"{rng.choice(['403', '416', '604', '514'])}{khach:07d}",
            "dia_chi": f"{rng.randrange(1, 999)} {rng.choice(['Yonge St', 'Main St', 'King St', 'Queen St'])}",
            "thanh_pho": thanh_pho, "bang": bang,
            "zipcode": f"T{rng.randrange(10):d}Y{rng.randrange(10)}J{rng.randrange(10)}",
            "quoc_gia": "Canada", "loai_tien": "CAD",
            "gia_tien": str(rng.choice([120, 207, 218, 243, 256, 270, 322, 333, 350])),
            "pttt": rng.choice(["Chuyển khoản", "Thẻ", "Thu hộ khi giao"]),
            "nguoi_ban": rng.choice(sellers) if sellers else "",
            "trang_thai_vc": rng.choice(statuses),
            "nv_van_don": rng.choice(staff) if staff else "",
            "trang_thai_tt": rng.choice(payments),
            "mua_lai": rng.choice([1, 1, 1, 2, 2, 3]),
            "ghi_chu": rng.choice(["", "", "Giao buổi tối", "Gọi trước khi giao\nKhách hay vắng"]),
        }
        san_pham = rng.sample(products, k=min(len(products), rng.choice([1, 1, 2, 3]))) if products else []
        tong = 0
        for ma in san_pham:
            sl = rng.randrange(1, 6)
            gia_tri[ma] = sl
            tong += sl
        gia_tri["so_luong"] = tong
        yield gia_tri


def run(*, n=PERF_TABLE_ROWS, actor=None, batch=1000, on_progress=None):
    """Sinh `n` dòng vào bảng vận đơn. Trả về số dòng đã tạo."""
    from forms_builder.services import record_service
    from orders.constants import PaymentStatus, ShippingStatus, WAYBILL_DEPARTMENT_CODE
    from orders.services import dispatch_service
    from org.models import UserProfile

    bang = dispatch_service.ensure_waybill_table(actor=actor)
    columns = list(bang.columns.order_by("order", "id"))
    products = [ma for _, ma, _ in dispatch_service.product_columns()]
    staff = list(UserProfile.objects.filter(department__code=WAYBILL_DEPARTMENT_CODE)
                 .values_list("user__username", flat=True))
    sellers = list(UserProfile.objects.filter(department__code="sale")
                   .values_list("full_name", flat=True)) or ["Ngọc Anh", "Khánh Huyền", "NHITTQ"]
    nguon = rows(
        n, products=products, sellers=sellers, staff=staff,
        statuses=[c.label for c in ShippingStatus], payments=[c.label for c in PaymentStatus],
    )
    tao = 0
    lo = []
    for gia_tri in nguon:
        lo.append(gia_tri)
        if len(lo) >= batch:
            tao += record_service.create_records_bulk(bang, lo, actor=actor, columns=columns).created
            lo = []
            if on_progress:
                on_progress(tao)
    if lo:
        tao += record_service.create_records_bulk(bang, lo, actor=actor, columns=columns).created
    return tao


def clear():
    """Xoá cứng dòng giả — chúng không phải dữ liệu nghiệp vụ, không cần giữ dấu."""
    from orders.constants import WAYBILL_TABLE_CODE

    ds = DataRecord.all_objects.filter(table__code=WAYBILL_TABLE_CODE, data__ma_don__startswith=PERF_PREFIX)
    so = ds.count()
    ds._raw_delete(ds.db)
    return so


class Command(BaseCommand):
    help = "Sinh dữ liệu giả (mặc định 50.000 dòng vận đơn) để đo hiệu năng"

    def add_arguments(self, parser):
        parser.add_argument("--so-dong", type=int, default=PERF_TABLE_ROWS, dest="so_dong")
        parser.add_argument("--xoa-cu", action="store_true", dest="xoa_cu",
                            help="Xoá dòng giả PERF-* đã sinh trước đó")
        parser.add_argument("--dong-y-chay-that", action="store_true", dest="dong_y")

    def handle(self, *args, **o):
        if not settings.DEBUG and not o["dong_y"]:
            raise CommandError("DEBUG đang tắt — dữ liệu giả không dành cho máy chủ thật. "
                               "Chắc chắn thì thêm --dong-y-chay-that.")
        from org.models import UserProfile

        if o["xoa_cu"]:
            self.stdout.write(f"Đã xoá {clear()} dòng giả cũ.")
        ho_so = UserProfile.objects.filter(rank="admin").select_related("user").first()
        if ho_so is None:
            raise CommandError("Chưa có tài khoản quản trị — chạy `manage.py du_lieu_mau` trước.")
        tao = run(n=o["so_dong"], actor=ho_so.user,
                  on_progress=lambda n: self.stdout.write(f"  {n} dòng…", ending="\r"))
        self.stdout.write(self.style.SUCCESS(f"\nĐã sinh {tao} dòng vận đơn giả (PERF-*)."))
