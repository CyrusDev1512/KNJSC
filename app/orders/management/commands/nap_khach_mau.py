"""Nạp khách hàng giả theo lô vào một bảng vận đơn — để xem lưới và cột Trùng
ở cỡ thật (300 nghìn khách), không đi qua Order/OrderLine.

    python manage.py nap_khach_mau --so-khach 300000              # vào Vận đơn mới
    python manage.py nap_khach_mau --bang van_don --so-khach 1000
    python manage.py nap_khach_mau --xoa-cu                       # chỉ xoá dòng KH-*

Khác `nap_du_lieu_van_don` (giữ đúng 10.000 mã MAU-* và chi tiết sản
phẩm, tối đa 100.000 dòng, nạp trong một giao dịch), lệnh này **chảy theo lô**
nên 300.000 khách không giữ hết trong bộ nhớ, và **cố ý có khách mua lại**:
mặc định 20% dòng là khách đã có số điện thoại trong bảng, để cột Trùng có
việc để làm. Một phần nhỏ (2%) trong số dòng mua lại ghi số điện thoại theo
định dạng khác — `+1 (416) 555-0123` thay vì `4165550123` — đúng như tệp Excel
thật: đây là những dòng cột Trùng hiện nay **không** bắt được, nạp vào để đo.

Mã đơn `KH-…` nhận ra được nên xoá lại được mà không đụng dữ liệu thật. Ngẫu
nhiên theo hạt giống cố định. Bảng có profile Vận đơn (`van_don`, Vận đơn
DB) thì mỗi dòng có phân công Vận đơn/CSKH để phạm vi Staff đúng như thật.
Không chạy trên máy chủ thật khi DEBUG tắt — cùng khoá với `seed_perf`.
"""
import random
import time
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.models import Count

from core.constants import Rank
from core.identity import employee_code
from forms_builder.models import DataRecord, TableDef
from orders.constants import PaymentStatus, ShippingStatus, is_waybill_table
from orders.models import Product, WaybillAssignment
from orders.services import assignment_service

from .nap_du_lieu_van_don import (
    BASE_PRICES, FIRST_NAMES, LAST_NAMES, NOTES, PLACES, POSTAL_LETTERS, STREETS,
)

PREFIX = "KH-"
HAT_GIONG = 20260916
BANG_MAC_DINH = "van_don"
TI_LE_MUA_LAI = 0.2
TI_LE_SO_LE = 0.02          # phần dòng mua lại ghi số điện thoại khác định dạng
SO_THANG = 36
LO = 2000
MA_VUNG = ("416", "647", "604", "778", "403", "587", "514", "613", "204", "902")
NOI_MY = (
    ("California", "Los Angeles", "900"), ("Texas", "Houston", "770"),
    ("New York", "New York", "100"), ("Florida", "Miami", "331"),
)


def _khach(i, seed):
    """Một khách: tên, số điện thoại 10 số, nơi ở. Cùng khách thì lần mua lại
    vẫn cùng địa chỉ — ngẫu nhiên theo số thứ tự khách, không theo dòng."""
    rng = random.Random(seed * 31 + i)
    ten = f"{FIRST_NAMES[i % len(FIRST_NAMES)]} {LAST_NAMES[(i // len(FIRST_NAMES)) % len(LAST_NAMES)]}"
    so = f"{MA_VUNG[i % len(MA_VUNG)]}{i % 10_000_000:07d}"
    if i % 5 == 0:
        bang, thanh_pho, buu = NOI_MY[i % len(NOI_MY)]
        quoc_gia, tien, zipcode = "Hoa Kỳ", "USD", f"{buu}{rng.randrange(100):02d}"
    else:
        bang, thanh_pho, buu = PLACES[i % len(PLACES)]
        quoc_gia, tien = "Canada", "CAD"
        zipcode = f"{buu} {rng.randrange(10)}{rng.choice(POSTAL_LETTERS)}{rng.randrange(10)}"
    return {
        "ten_khach": ten, "so_dien_thoai": so, "quoc_gia": quoc_gia, "loai_tien": tien,
        "bang": bang, "thanh_pho": thanh_pho, "zipcode": zipcode,
        "dia_chi": f"{1 + rng.randrange(998)} {rng.choice(STREETS)}",
    }


def _so_khac_dinh_dang(so):
    return f"+1 ({so[:3]}) {so[3:6]}-{so[6:]}"


def rows(so_khach, *, ti_le_mua_lai=TI_LE_MUA_LAI, so_thang=SO_THANG, products, sellers,
         pttt, seed=HAT_GIONG, hom_nay=None):
    """Sinh từng dict giá trị; trả về (giá trị, người bán). Số dòng =
    số khách / (1 − tỉ lệ mua lại), mỗi khách xuất hiện ít nhất một lần."""
    rng = random.Random(seed)
    so_dong = round(so_khach / (1 - ti_le_mua_lai)) if ti_le_mua_lai < 1 else so_khach
    thu_tu = list(range(so_khach)) + [rng.randrange(so_khach) for _ in range(so_dong - so_khach)]
    rng.shuffle(thu_tu)
    da_gap = set()
    cuoi = hom_nay or date.today()
    dau = cuoi - timedelta(days=30 * so_thang)
    trang_thai = list(ShippingStatus.labels)
    for i, k in enumerate(thu_tu):
        khach = _khach(k, seed)
        if k in da_gap and rng.random() < TI_LE_SO_LE:
            khach["so_dien_thoai"] = _so_khac_dinh_dang(khach["so_dien_thoai"])
        da_gap.add(k)
        ngay = dau + timedelta(days=rng.randrange((cuoi - dau).days + 1))
        chon = rng.sample(products, k=min(len(products), 1 + rng.randrange(3)))
        so_luong, tien, ten_sp = 0, Decimal(0), []
        for sp in chon:
            sl = 1 + rng.randrange(4)
            gia = BASE_PRICES[rng.randrange(len(BASE_PRICES))]
            so_luong += sl
            tien += gia * sl
            ten_sp.append(f"{sp.name} ×{sl}")
        vc = trang_thai[rng.randrange(len(trang_thai))]
        if vc == ShippingStatus.HUY_TRUOC_GIAO.label:
            da_tra = Decimal(0)
        else:
            da_tra = rng.choice((Decimal(0), tien, (tien / 2).quantize(Decimal("0.01"))))
        tt = (PaymentStatus.UNPAID if da_tra == 0 else PaymentStatus.PARTIAL
              if da_tra < tien else PaymentStatus.PAID)
        nguoi_ban = sellers[k % len(sellers)]
        gia_tri = {
            "ma_don": f"{PREFIX}{i + 1:06d}", "ngay": ngay.isoformat(), **khach,
            "san_pham": " + ".join(ten_sp), "so_luong": so_luong, "gia_tien": str(tien),
            "pttt": pttt[rng.randrange(len(pttt))] if pttt else "",
            "nguoi_ban": employee_code(nguoi_ban), "trang_thai_vc": vc,
            "trang_thai_tt": tt.label, "so_tien_tt": str(da_tra),
            "ghi_chu": NOTES[rng.randrange(len(NOTES))] if rng.random() < 0.3 else "",
        }
        if da_tra:
            gia_tri["ngay_tt"] = min(ngay + timedelta(days=rng.randrange(1, 8)), cuoi).isoformat()
            gia_tri["bill"] = f"BILL-{i + 1:06d}"
            gia_tri["pttt_thuc_te"] = gia_tri["pttt"]
        yield gia_tri, nguoi_ban


def _bang(code):
    bang = TableDef.all_objects.filter(code=code, is_active=True, deleted_at__isnull=True).first()
    if bang is None:
        raise CommandError(f"Không có bảng `{code}` đang hoạt động — chạy `manage.py tao_bang_van_don` trước.")
    return bang


def run(*, so_khach, bang=BANG_MAC_DINH, ti_le_mua_lai=TI_LE_MUA_LAI, so_thang=SO_THANG,
        seed=HAT_GIONG, lo=LO, on_progress=None):
    """Nạp `so_khach` khách vào bảng `bang`. Trả về số dòng đã tạo."""
    bang = _bang(bang)
    columns = list(bang.columns.order_by("order", "pk"))
    ma_cot = {c.code for c in columns}
    products = list(Product.objects.filter(is_active=True).order_by("code", "pk"))
    if not products:
        raise CommandError("Chưa có sản phẩm đang hoạt động — chạy `manage.py du_lieu_mau` trước.")
    sellers = list(assignment_service.candidates("care").filter(profile__department__code="sale"))
    if not sellers:
        raise CommandError("Chưa có nhân sự Sale đang hoạt động.")
    van_don = is_waybill_table(bang)
    giao = list(assignment_service.candidates("delivery")) if van_don else []
    if van_don and not giao:
        raise CommandError("Bảng có profile Vận đơn nhưng chưa có nhân sự Vận đơn để phân công.")
    cot_pttt = next((c for c in columns if c.code == "pttt"), None)
    pttt = list(cot_pttt.options) if cot_pttt and cot_pttt.options else []

    tao = 0
    dong, phan_cong = [], []

    def ghi():
        nonlocal tao
        DataRecord.objects.bulk_create(dong, batch_size=lo)
        if van_don:
            WaybillAssignment.objects.bulk_create(
                [WaybillAssignment(record=r, delivery=g, care=r.created_by, version=1)
                 for r, g in zip(dong, phan_cong)], batch_size=lo)
        tao += len(dong)
        dong.clear()
        phan_cong.clear()
        if on_progress:
            on_progress(tao)

    for i, (gia_tri, nguoi_ban) in enumerate(rows(
            so_khach, ti_le_mua_lai=ti_le_mua_lai, so_thang=so_thang,
            products=products, sellers=sellers, pttt=pttt, seed=seed)):
        r = DataRecord(table=bang, data={k: v for k, v in gia_tri.items() if k in ma_cot},
                       created_by=nguoi_ban, department=bang.department,
                       team=nguoi_ban.profile.team)
        r.sync_indexed_columns(columns)
        dong.append(r)
        phan_cong.append(giao[i % len(giao)] if giao else None)
        if len(dong) >= lo:
            ghi()
    if dong:
        ghi()
    return tao


def clear(bang=BANG_MAC_DINH):
    """Xoá cứng dòng giả KH-* — không phải dữ liệu nghiệp vụ, không cần giữ dấu."""
    ds = DataRecord.all_objects.filter(table__code=bang, data__ma_don__startswith=PREFIX)
    so = ds.count()
    if so:
        pc = WaybillAssignment.objects.filter(record__in=ds.values("pk"))
        pc._raw_delete(pc.db)
        ds._raw_delete(ds.db)
    return so


def stats(bang=BANG_MAC_DINH):
    """Số dòng, số khách (số điện thoại khác nhau), số dòng trùng, kích thước bảng."""
    ds = DataRecord.objects.filter(table__code=bang)
    tong = ds.count()
    so = ds.exclude(val_phone="").order_by().values("val_phone").annotate(n=Count("id"))
    khach = so.count()
    trung = sum(x["n"] for x in so.filter(n__gt=1))
    with connection.cursor() as c:
        c.execute("SELECT pg_size_pretty(pg_total_relation_size('forms_builder_datarecord'))")
        kich_thuoc = c.fetchone()[0]
    return {"dong": tong, "khach": khach, "trung": trung, "kich_thuoc": kich_thuoc}


class Command(BaseCommand):
    help = "Nạp khách hàng giả (mặc định 300.000, 20% mua lại) vào một bảng vận đơn"

    def add_arguments(self, parser):
        parser.add_argument("--bang", default=BANG_MAC_DINH, help="Mã bảng đích, mặc định Vận đơn mới")
        parser.add_argument("--so-khach", type=int, default=300_000, dest="so_khach")
        parser.add_argument("--ti-le-mua-lai", type=float, default=TI_LE_MUA_LAI, dest="ti_le",
                            help="Phần dòng là khách mua lại (0 → không trùng), mặc định 0.2")
        parser.add_argument("--so-thang", type=int, default=SO_THANG, dest="so_thang")
        parser.add_argument("--seed", type=int, default=HAT_GIONG)
        parser.add_argument("--xoa-cu", action="store_true", dest="xoa_cu",
                            help="Xoá dòng giả KH-* đã nạp trước đó rồi mới nạp; kèm --so-khach 0 thì chỉ xoá")
        parser.add_argument("--dong-y-chay-that", action="store_true", dest="dong_y")

    def handle(self, *args, **o):
        if not settings.DEBUG and not o["dong_y"]:
            raise CommandError("DEBUG đang tắt — dữ liệu giả không dành cho máy chủ thật. "
                               "Chắc chắn thì thêm --dong-y-chay-that.")
        if not 0 <= o["ti_le"] < 1:
            raise CommandError("--ti-le-mua-lai phải từ 0 tới dưới 1.")
        from org.models import UserProfile

        if not UserProfile.objects.filter(rank=Rank.ADMIN).exists():
            raise CommandError("Chưa có tài khoản quản trị — chạy `manage.py du_lieu_mau` trước.")
        _bang(o["bang"])
        if o["xoa_cu"]:
            self.stdout.write(f"Đã xoá {clear(o['bang'])} dòng giả KH-* cũ.")
        if o["so_khach"] <= 0:
            return
        bat_dau = time.monotonic()
        tao = run(so_khach=o["so_khach"], bang=o["bang"], ti_le_mua_lai=o["ti_le"],
                  so_thang=o["so_thang"], seed=o["seed"],
                  on_progress=lambda n: self.stdout.write(f"  {n:,} dòng…".replace(",", "."), ending="\r"))
        if not connection.in_atomic_block:      # VACUUM không chạy được trong giao dịch (bài kiểm)
            with connection.cursor() as c:
                c.execute("VACUUM ANALYZE forms_builder_datarecord")
        s = stats(o["bang"])
        giay = time.monotonic() - bat_dau
        self.stdout.write(self.style.SUCCESS(
            f"\nĐã nạp {tao:,} dòng KH-* vào {o['bang']} trong {giay:,.0f} giây.".replace(",", ".")))
        self.stdout.write(
            f"Bảng giờ có {s['dong']:,} dòng, {s['khach']:,} số điện thoại khác nhau, "
            f"{s['trung']:,} dòng có số trùng; bảng DataRecord {s['kich_thuoc']}.".replace(",", "."))
