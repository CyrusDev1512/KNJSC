"""Sinh dữ liệu giả để đo hiệu năng — AC-7.1, AC-10.6, NFR-1, NFR-2, backlog K6.

    python manage.py seed_perf                 # 50.000 dòng vận đơn, 12 tháng
    python manage.py seed_perf --so-dong 100000 --so-thang 24 --dien-day --bang-sale
    python manage.py seed_perf --xoa-cu        # xoá dòng giả cũ trước khi sinh

Dòng giả nhận ra được bằng mã đơn `PERF-…`, nên xoá lại được mà không đụng
dữ liệu thật. Số liệu sinh **có chủ đích** giống dữ liệu thật: số điện thoại
trùng ~20% (cột Lọc trùng có việc để làm), đủ tám trạng thái, ngày trải đều
tới hôm nay (cây Quý ▸ Tháng của KN CRM có dữ liệu ở quý hiện tại), số lượng
từng sản phẩm. Ngẫu nhiên theo hạt giống cố định để hai máy sinh ra cùng một bộ.

Cỡ "100 nghìn khách, hàng triệu ô" (kiểm tải KN CRM, docs/06 tầng 9):
`--so-dong 100000 --so-thang 24 --dien-day` cho ~100.000 dòng × 30 cột ≈ 3 triệu
ô có giá trị, ~80.000 số điện thoại khác nhau. `--bang-sale` dựng thêm bảng
`perf_sale` của bộ phận Sale (20.000 dòng, **có cột tính sẵn** Doanh thu =
Đơn giá × Số lượng) để đo việc Manager đổi công thức mà không đụng bảng vận đơn.

Cuối lệnh in số dòng, số ô, số khách, thời gian, kích thước bảng, rồi chạy
`VACUUM ANALYZE` để trình lập kế hoạch của Postgres có thống kê đúng — không
thì lần đo đầu tiên sau khi nạp đi đường chậm vì thống kê còn của bảng rỗng.

Không chạy trên máy chủ thật khi DEBUG tắt — cùng khoá với `du_lieu_mau`.
"""
import random
import time
from datetime import date, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from core.constants import PERF_TABLE_ROWS
from forms_builder.models import DataRecord

PERF_PREFIX = "PERF-"
HAT_GIONG = 20260903
#: Bảng Sale dựng riêng cho đo tải, có cột tính sẵn
SALE_TABLE_CODE = "perf_sale"
SALE_TABLE_ROWS = 20_000
TEN = ["Nguyễn Văn An", "Trần Thị Bình", "Lê Minh Châu", "Phạm Quốc Dũng", "Hoàng Thu Hà",
       "Taylor Minh", "Emily Tran", "Daniel Pham", "Sarah Le", "Jordan Nguyen"]
THANH_PHO = [("Calgary", "AB"), ("Toronto", "ON"), ("Vancouver", "BC"), ("Montreal", "QC"),
             ("Edmonton", "AB"), ("Ottawa", "ON")]
MKT = ["FB Ads", "TikTok", "Google", "Organic", ""]
SAN_PHAM_SALE = ["Retinol Cream", "Retinol Serum", "Vitamin C Serum", "Sunscreen 50", "Niacinamide"]
TRANG_THAI_SALE = ["Mới", "Đã gọi", "Chốt", "Huỷ", "Chờ giao"]


def _khoang_ngay(months, start, days):
    """Ngày bắt đầu và số ngày trải: `--so-thang` thì tính lùi từ hôm nay cho
    tới ngày đầu của tháng thứ `months` trước; không thì giữ mốc cố định cũ."""
    if months is None:
        return start, days
    hom_nay = date.today()
    nam, thang = hom_nay.year, hom_nay.month - (months - 1)
    while thang <= 0:
        thang += 12
        nam -= 1
    dau = date(nam, thang, 1)
    return dau, (hom_nay - dau).days + 1


def rows(n, *, products, sellers, statuses, payments, staff, start=date(2025, 9, 1), seed=HAT_GIONG,
         months=None, dup_ratio=0.2, full=False, reconcile=("Đã về TK",)):
    """Sinh `n` dict giá trị cho bảng vận đơn. Dùng chung với bài kiểm hiệu năng.

    `months` thay `start`: trải ngày đều từ tháng thứ `months` trước tới hôm nay.
    `dup_ratio` là tỉ lệ dòng có số điện thoại trùng dòng khác. `full` điền đủ
    cả 30 cột chuẩn (kể cả thanh toán, bill, email…) thay vì 18 cột hay dùng.
    """
    rng = random.Random(seed)
    start, so_ngay = _khoang_ngay(months, start, 365)
    so_khach = max(int(n * (1 - dup_ratio)), 1)
    for i in range(n):
        khach = rng.randrange(so_khach)
        thanh_pho, bang = rng.choice(THANH_PHO)
        ngay = start + timedelta(days=rng.randrange(so_ngay))
        gia = rng.choice([120, 207, 218, 243, 256, 270, 322, 333, 350])
        gia_tri = {
            "ma_don": f"{PERF_PREFIX}{i + 1:06d}",
            "ngay": ngay.isoformat(),
            "ten_khach": f"{rng.choice(TEN)} {khach}",
            "so_dien_thoai": f"{rng.choice(['403', '416', '604', '514'])}{khach:07d}",
            "dia_chi": f"{rng.randrange(1, 999)} {rng.choice(['Yonge St', 'Main St', 'King St', 'Queen St'])}",
            "thanh_pho": thanh_pho, "bang": bang,
            "zipcode": f"T{rng.randrange(10):d}Y{rng.randrange(10)}J{rng.randrange(10)}",
            "quoc_gia": "Canada", "loai_tien": "CAD",
            "gia_tien": str(gia),
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
        if full:
            gia_tri.update({
                "san_pham": ", ".join(ma[3:].replace("_", " ") for ma in san_pham) or "Retinol Cream",
                "don_vi_phu": rng.choice(["", "Lọ 30ml", "Tuýp 50g"]),
                "facebook": f"fb.com/khach{khach}",
                "email": f"khach{khach}@example.com",
                "ngay_tt": (ngay + timedelta(days=rng.randrange(0, 10))).isoformat(),
                "so_tien_tt": str(gia * max(tong, 1)),
                "bill": f"BILL{i + 1:07d}",
                "black_list": rng.choice(["", "", "", "Bom hàng 1 lần"]),
                "mkt": rng.choice(MKT),
                "nguoi_chuyen_tien": f"{rng.choice(TEN)}",
                "doi_soat": rng.choice(list(reconcile) + [""]) if reconcile else "",
            })
        yield gia_tri


def sale_rows(n, *, sellers, seed=HAT_GIONG + 1, months=None):
    """Sinh `n` dict giá trị cho bảng Sale đo tải (`perf_sale`)."""
    rng = random.Random(seed)
    start, so_ngay = _khoang_ngay(months or 12, None, None)
    so_khach = max(n * 4 // 5, 1)
    for i in range(n):
        khach = rng.randrange(so_khach)
        thanh_pho, _ = rng.choice(THANH_PHO)
        so_luong = rng.randrange(1, 6)
        yield {
            "ma_don": f"{PERF_PREFIX}S{i + 1:06d}",
            "ngay": (start + timedelta(days=rng.randrange(so_ngay))).isoformat(),
            "ten_khach": f"{rng.choice(TEN)} {khach}",
            "so_dien_thoai": f"09{khach:08d}",
            "san_pham": rng.choice(SAN_PHAM_SALE),
            "so_luong": so_luong,
            "don_gia": str(rng.choice([120, 207, 218, 243, 256, 270])),
            "nguoi_ban": rng.choice(sellers) if sellers else "",
            "trang_thai": rng.choice(TRANG_THAI_SALE),
            "thanh_pho": thanh_pho,
            "ghi_chu": rng.choice(["", "", "Khách cũ", "Gọi lại chiều"]),
        }


#: Cột của bảng Sale đo tải — (nhãn, mã, kiểu, nhãn ý nghĩa, thêm)
SALE_COLUMNS = [
    ("Mã đơn", "ma_don", "text", "", {}),
    ("Ngày", "ngay", "date", "date", {}),
    ("Tên khách", "ten_khach", "text", "customer", {}),
    ("Số điện thoại", "so_dien_thoai", "text", "phone", {}),
    ("Sản phẩm", "san_pham", "text", "product", {}),
    ("Số lượng", "so_luong", "integer", "", {}),
    ("Đơn giá", "don_gia", "money", "", {}),
    ("Doanh thu", "doanh_thu", "money", "revenue",
     {"is_computed": True, "compute_op": "multiply", "compute_left": "don_gia",
      "compute_right": "so_luong", "compute_decimals": 2}),
    ("Người bán", "nguoi_ban", "text", "seller", {}),
    ("Trạng thái", "trang_thai", "text", "status", {}),
    ("Thành phố", "thanh_pho", "text", "", {}),
    ("Ghi chú", "ghi_chu", "long_text", "", {}),
]


def ensure_sale_table(*, actor=None):
    """Bảng `perf_sale` của bộ phận Sale, có cột tính sẵn Doanh thu. Tạo nếu chưa có."""
    from forms_builder.models import TableDef
    from forms_builder.services import table_service
    from org.models import Department

    bang = TableDef.all_objects.filter(code=SALE_TABLE_CODE).first()
    if bang is not None:
        return bang
    sale = Department.objects.filter(code="sale").first()
    if sale is None:
        raise CommandError("Chưa có bộ phận Sale — chạy `manage.py du_lieu_mau` trước.")
    bang = table_service.create_table(
        name="Đơn Sale (đo tải)", code=SALE_TABLE_CODE, department=sale,
        description="Bảng sinh bởi seed_perf để đo cột tính sẵn — xoá được.", actor=actor,
    )
    for thu_tu, (ten, ma, kieu, nhan, them) in enumerate(SALE_COLUMNS, start=1):
        table_service.add_column(bang, name=ten, code=ma, field_type=kieu, meaning=nhan,
                                 order=thu_tu, actor=actor, **them)
    return bang


def _nap(bang, nguon, *, actor, batch, on_progress):
    from forms_builder.services import record_service

    columns = list(bang.columns.order_by("order", "id"))
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


def run(*, n=PERF_TABLE_ROWS, actor=None, batch=1000, on_progress=None,
        months=None, dup_ratio=0.2, full=False):
    """Sinh `n` dòng vào bảng vận đơn. Trả về số dòng đã tạo."""
    from orders.constants import PaymentStatus, ShippingStatus, WAYBILL_DEPARTMENT_CODE
    from orders.services import dispatch_service
    from org.models import UserProfile

    bang = dispatch_service.ensure_waybill_table(actor=actor)
    products = [ma for _, ma, _ in dispatch_service.product_columns()]
    staff = list(UserProfile.objects.filter(department__code=WAYBILL_DEPARTMENT_CODE)
                 .values_list("user__username", flat=True))
    sellers = list(UserProfile.objects.filter(department__code="sale")
                   .values_list("full_name", flat=True)) or ["Ngọc Anh", "Khánh Huyền", "NHITTQ"]
    nguon = rows(
        n, products=products, sellers=sellers, staff=staff,
        statuses=[c.label for c in ShippingStatus], payments=[c.label for c in PaymentStatus],
        months=months, dup_ratio=dup_ratio, full=full,
    )
    return _nap(bang, nguon, actor=actor, batch=batch, on_progress=on_progress)


def run_sale(*, n=SALE_TABLE_ROWS, actor=None, batch=1000, on_progress=None, months=None):
    """Sinh `n` dòng vào bảng Sale đo tải (tạo bảng nếu chưa có). Trả số dòng đã tạo."""
    from org.models import UserProfile

    bang = ensure_sale_table(actor=actor)
    sellers = list(UserProfile.objects.filter(department__code="sale")
                   .values_list("full_name", flat=True)) or ["Ngọc Anh", "Khánh Huyền"]
    return _nap(bang, sale_rows(n, sellers=sellers, months=months),
                actor=actor, batch=batch, on_progress=on_progress)


def clear():
    """Xoá cứng dòng giả — chúng không phải dữ liệu nghiệp vụ, không cần giữ dấu.
    Bảng Sale đo tải giữ lại (rỗng) để cột tính sẵn còn đó cho lần nạp sau."""
    from orders.constants import WAYBILL_TABLE_CODE

    so = 0
    for ds in (
        DataRecord.all_objects.filter(table__code=WAYBILL_TABLE_CODE, data__ma_don__startswith=PERF_PREFIX),
        DataRecord.all_objects.filter(table__code=SALE_TABLE_CODE),
    ):
        so += ds.count()
        ds._raw_delete(ds.db)
    return so


def stats(table):
    """Số dòng, số ô có giá trị, số khách (số điện thoại khác nhau) của một bảng,
    và kích thước cả bảng bản ghi trên đĩa — để ghi vào báo cáo đo tải."""
    with connection.cursor() as c:
        c.execute("SELECT count(*) FROM forms_builder_datarecord WHERE table_id = %s", [table.pk])
        so_dong = c.fetchone()[0]
        c.execute(
            "SELECT count(*) FROM forms_builder_datarecord r, jsonb_each_text(r.data) e "
            "WHERE r.table_id = %s AND e.value IS NOT NULL AND e.value <> ''", [table.pk],
        )
        so_o = c.fetchone()[0]
        c.execute("SELECT count(DISTINCT val_phone) FROM forms_builder_datarecord "
                  "WHERE table_id = %s AND val_phone <> ''", [table.pk])
        so_khach = c.fetchone()[0]
        c.execute("SELECT pg_size_pretty(pg_total_relation_size('forms_builder_datarecord'))")
        kich_thuoc = c.fetchone()[0]
    return {"so_dong": so_dong, "so_o": so_o, "so_khach": so_khach, "kich_thuoc": kich_thuoc}


def vacuum_analyze():
    """Cập nhật thống kê cho trình lập kế hoạch. Không chạy được trong giao dịch."""
    with connection.cursor() as c:
        c.execute("VACUUM ANALYZE forms_builder_datarecord")


class Command(BaseCommand):
    help = "Sinh dữ liệu giả (mặc định 50.000 dòng vận đơn) để đo hiệu năng"

    def add_arguments(self, parser):
        parser.add_argument("--so-dong", type=int, default=PERF_TABLE_ROWS, dest="so_dong")
        parser.add_argument("--so-thang", type=int, default=None, dest="so_thang",
                            help="Trải ngày đều từ bấy nhiêu tháng trước tới hôm nay (mặc định: 12 tháng từ 09.2025)")
        parser.add_argument("--ti-le-trung", type=float, default=0.2, dest="ti_le_trung",
                            help="Tỉ lệ dòng có số điện thoại trùng dòng khác (mặc định 0.2)")
        parser.add_argument("--dien-day", action="store_true", dest="dien_day",
                            help="Điền đủ 30 cột chuẩn của bảng vận đơn (mặc định 18 cột hay dùng)")
        parser.add_argument("--bang-sale", action="store_true", dest="bang_sale",
                            help=f"Dựng thêm bảng {SALE_TABLE_CODE} của Sale ({SALE_TABLE_ROWS} dòng, có cột tính sẵn)")
        parser.add_argument("--so-dong-sale", type=int, default=SALE_TABLE_ROWS, dest="so_dong_sale")
        parser.add_argument("--xoa-cu", action="store_true", dest="xoa_cu",
                            help="Xoá dòng giả PERF-* đã sinh trước đó")
        parser.add_argument("--dong-y-chay-that", action="store_true", dest="dong_y")

    def handle(self, *args, **o):
        if not settings.DEBUG and not o["dong_y"]:
            raise CommandError("DEBUG đang tắt — dữ liệu giả không dành cho máy chủ thật. "
                               "Chắc chắn thì thêm --dong-y-chay-that.")
        from org.models import UserProfile
        from orders.services import dispatch_service

        if o["xoa_cu"]:
            self.stdout.write(f"Đã xoá {clear()} dòng giả cũ.")
        ho_so = UserProfile.objects.filter(rank="admin").select_related("user").first()
        if ho_so is None:
            raise CommandError("Chưa có tài khoản quản trị — chạy `manage.py du_lieu_mau` trước.")

        tien_do = lambda n: self.stdout.write(f"  {n} dòng…", ending="\r")   # noqa: E731
        bat_dau = time.monotonic()
        tao = run(n=o["so_dong"], actor=ho_so.user, on_progress=tien_do,
                  months=o["so_thang"], dup_ratio=o["ti_le_trung"], full=o["dien_day"])
        giay_vd = time.monotonic() - bat_dau
        self.stdout.write(self.style.SUCCESS(f"\nĐã sinh {tao} dòng vận đơn giả (PERF-*) trong {giay_vd:.0f} giây."))

        giay_sale = 0
        if o["bang_sale"]:
            bat_dau = time.monotonic()
            tao_sale = run_sale(n=o["so_dong_sale"], actor=ho_so.user, on_progress=tien_do, months=o["so_thang"])
            giay_sale = time.monotonic() - bat_dau
            self.stdout.write(self.style.SUCCESS(
                f"\nĐã sinh {tao_sale} dòng bảng {SALE_TABLE_CODE} (có cột tính sẵn) trong {giay_sale:.0f} giây."))

        self.stdout.write("VACUUM ANALYZE…")
        vacuum_analyze()

        dong = ["| Bảng | Dòng | Ô có giá trị | Số khách (SĐT khác nhau) |", "|---|---:|---:|---:|"]
        cac_bang = [dispatch_service.waybill_table()]
        if o["bang_sale"]:
            cac_bang.append(ensure_sale_table(actor=ho_so.user))
        kich_thuoc = ""
        for bang in cac_bang:
            tk = stats(bang)
            kich_thuoc = tk["kich_thuoc"]
            dong.append(f"| `{bang.code}` | {tk['so_dong']:,} | {tk['so_o']:,} | {tk['so_khach']:,} |")
        bang_md = "\n".join(dong).replace(",", ".")
        self.stdout.write("\n" + bang_md)
        self.stdout.write(f"Kích thước bảng bản ghi trên đĩa: {kich_thuoc}. "
                          f"Thời gian nạp: {giay_vd + giay_sale:.0f} giây.")

        thu_muc = settings.STORAGE_DIR / "perf"
        thu_muc.mkdir(parents=True, exist_ok=True)
        tep = thu_muc / f"{date.today().isoformat()}-du-lieu.md"
        tep.write_text(
            f"# Dữ liệu đo tải — nạp ngày {date.today().isoformat()}\n\n"
            f"Lệnh: `seed_perf --so-dong {o['so_dong']}"
            + (f" --so-thang {o['so_thang']}" if o["so_thang"] else "")
            + (" --dien-day" if o["dien_day"] else "")
            + (f" --bang-sale --so-dong-sale {o['so_dong_sale']}" if o["bang_sale"] else "")
            + f" --ti-le-trung {o['ti_le_trung']}`\n\n"
            + bang_md + "\n\n"
            + f"- Kích thước `forms_builder_datarecord` (kể cả chỉ mục): {kich_thuoc}\n"
            + f"- Thời gian nạp: vận đơn {giay_vd:.0f} giây"
            + (f", Sale {giay_sale:.0f} giây" if o["bang_sale"] else "") + "\n"
            + "- Đã chạy `VACUUM ANALYZE` sau khi nạp\n",
            encoding="utf-8",
        )
        self.stdout.write(f"Đã ghi {tep}")
