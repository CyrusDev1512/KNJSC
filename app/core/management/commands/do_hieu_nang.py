"""Đo từng đường nóng của KN CRM trên dữ liệu đã nạp — AC-10.6, docs/06 tầng 9.

    python manage.py seed_perf --so-dong 100000 --so-thang 24 --dien-day --bang-sale
    python manage.py do_hieu_nang                    # 3 lần mỗi đường, ghi storage/perf/<ngày>-don-le.md
    python manage.py do_hieu_nang --giai-thich       # kèm EXPLAIN (ANALYZE, BUFFERS) truy vấn nặng nhất
    python manage.py do_hieu_nang --nhan sau         # tệp ...-don-le-sau.md, để so "trước / sau"
    python manage.py do_hieu_nang --bo-tinh-lai-lon  # bỏ bước tính lại 100.000 dòng (chậm)

Đo **một người, không tải** — đây là mức trần: đường nào đã chậm ở đây thì 100
người cùng lúc chắc chắn chậm hơn. Gọi thẳng view qua `django.test.Client`
(cùng tiến trình, không qua mạng, có cả thời gian vẽ template), bấm giờ
`--lan` lần, lấy **trung vị**; mỗi lần đếm số lệnh truy vấn và lệnh chậm nhất.
Ngưỡng theo `core.constants` (PERF_READ_P95_MS, PERF_WRITE_P95_MS, …).

Các lệnh ghi (lưu ô, dòng mới, định dạng) sửa thật dữ liệu giả PERF-* — chạy
trên dữ liệu `seed_perf`, không chạy trên dữ liệu thật.
"""
import os
import platform
import random
import statistics
import time
from datetime import date

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext

from core.constants import (
    GRID_FORMAT_CELLS_MAX, PERF_POLL_P95_MS, PERF_READ_P95_MS, PERF_RECOMPUTE_SECONDS,
    PERF_WRITE_P95_MS,
)
from core.management.commands.seed_perf import SALE_TABLE_CODE
from forms_builder.models import DataRecord, TableDef

DOC = "đọc"
GHI = "ghi"
HOI = "hỏi mốc"
NEN = "nền"
TINH = "tính lại"
NGUONG = {DOC: PERF_READ_P95_MS, GHI: PERF_WRITE_P95_MS, HOI: PERF_POLL_P95_MS,
          NEN: None, TINH: PERF_RECOMPUTE_SECONDS * 1000}


def _so(n):
    """Số kiểu Việt: 1.234.567 (chấm ngăn nghìn), không lẻ."""
    return f"{n:,.0f}".replace(",", ".")


class Do:
    """Một dòng của bảng đo: tên, nhóm ngưỡng, các lần đo (ms), truy vấn."""

    def __init__(self, ten, nhom):
        self.ten, self.nhom = ten, nhom
        self.ms = []
        self.so_truy_van = 0
        self.cham_nhat = ("", 0.0)     # (sql, ms) của lệnh chậm nhất trong lần đo cuối
        self.giai_thich = ""
        self.ghi_chu = ""

    @property
    def trung_vi(self):
        return statistics.median(self.ms) if self.ms else 0

    @property
    def nguong(self):
        return NGUONG[self.nhom]

    @property
    def dat(self):
        return None if self.nguong is None else self.trung_vi <= self.nguong


class Command(BaseCommand):
    help = "Đo từng đường nóng của KN CRM (một người, không tải) trên dữ liệu seed_perf"

    def add_arguments(self, parser):
        parser.add_argument("--lan", type=int, default=3, help="Số lần đo mỗi đường (mặc định 3)")
        parser.add_argument("--giai-thich", action="store_true", dest="giai_thich",
                            help="Chạy EXPLAIN (ANALYZE, BUFFERS) cho lệnh chậm nhất của mỗi đường")
        parser.add_argument("--bo-tinh-lai-lon", action="store_true", dest="bo_tinh_lai_lon",
                            help="Bỏ bước tính lại cột tính sẵn trên bảng vận đơn 100.000 dòng")
        parser.add_argument("--nhan", default="", help="Hậu tố tên tệp báo cáo, ví dụ `truoc`, `sau`")
        parser.add_argument("--nguoi", default="vd.staff", help="Tài khoản Vận đơn dùng để đo")
        parser.add_argument("--nguoi-sale", default="sale.manager", dest="nguoi_sale",
                            help="Tài khoản Sale đo bảng perf_sale (Staff chỉ thấy dòng mình tạo nên mặc định là Manager)")
        parser.add_argument("--quan-ly-sale", default="sale.manager", dest="quan_ly_sale")

    # ── Khung đo ──
    def _do(self, ten, nhom, ham, *, lan=None, giai_thich=False):
        kq = Do(ten, nhom)
        for _ in range(lan or self.lan):
            with CaptureQueriesContext(connection) as ctx:
                bat_dau = time.perf_counter()
                ham()
                kq.ms.append((time.perf_counter() - bat_dau) * 1000)
            kq.so_truy_van = len(ctx.captured_queries)
            if ctx.captured_queries:
                q = max(ctx.captured_queries, key=lambda q: float(q["time"]))
                kq.cham_nhat = (q["sql"], float(q["time"]) * 1000)
        if giai_thich and kq.cham_nhat[0].lstrip().upper().startswith("SELECT"):
            try:
                with connection.cursor() as c:
                    c.execute("EXPLAIN (ANALYZE, BUFFERS) " + kq.cham_nhat[0])
                    kq.giai_thich = "\n".join(r[0] for r in c.fetchall())
            except Exception as loi:      # noqa: BLE001 — chỉ là phụ lục, không được làm hỏng phép đo
                kq.giai_thich = f"(không EXPLAIN được: {loi})"
        self.ket_qua.append(kq)
        dau = "—" if kq.dat is None else ("ĐẠT" if kq.dat else "KHÔNG ĐẠT")
        self.stdout.write(f"  {ten:<52} {kq.trung_vi:>9.0f} ms  {kq.so_truy_van:>3} tv  {dau}")
        return kq

    def _get(self, client, duong_dan, ma=200):
        def ham():
            r = client.get(duong_dan)
            if r.status_code != ma:
                raise CommandError(f"GET {duong_dan} trả {r.status_code}, mong {ma}")
        return ham

    def _post(self, client, duong_dan, du_lieu, ma=200):
        def ham():
            r = client.post(duong_dan, du_lieu() if callable(du_lieu) else du_lieu)
            if r.status_code != ma:
                raise CommandError(f"POST {duong_dan} trả {r.status_code}, mong {ma}: "
                                   + r.content.decode("utf-8", "replace")[:300])
        return ham

    # ── Chạy ──
    def handle(self, *args, **o):
        from crm.services import grid_service, tree_service
        from forms_builder.services import export_service, table_service
        from orders.constants import WAYBILL_TABLE_CODE

        self.lan = o["lan"]
        self.ket_qua = []
        User = get_user_model()
        nguoi = User.objects.filter(username=o["nguoi"]).select_related("profile__department").first()
        nguoi_sale = User.objects.filter(username=o["nguoi_sale"]).select_related("profile__department").first()
        quan_ly_sale = User.objects.filter(username=o["quan_ly_sale"]).first()
        if nguoi is None or nguoi_sale is None or quan_ly_sale is None:
            raise CommandError("Thiếu tài khoản mẫu — chạy `manage.py du_lieu_mau` trước.")
        van_don = TableDef.all_objects.get(code=WAYBILL_TABLE_CODE)
        bang_sale = TableDef.all_objects.filter(code=SALE_TABLE_CODE).first()
        so_dong = DataRecord.all_objects.filter(table=van_don).count()
        if so_dong < 1000:
            raise CommandError(f"Bảng vận đơn chỉ có {so_dong} dòng — chạy `manage.py seed_perf` trước.")

        rng = random.Random(7)
        pk_vd = list(DataRecord.objects.in_scope(nguoi).filter(table=van_don).order_by("-pk").values_list("pk", flat=True)[:5000])
        hom_nay = date.today()
        thang = tree_service.Month(hom_nay.year, hom_nay.month)
        loc_thang = f"f_ngay__lon_bang={thang.first.isoformat()}&f_ngay__nho_bang={thang.last.isoformat()}"
        goc = f"/bang-tinh/{van_don.code}/"

        self.stdout.write(f"Bảng vận đơn: {_so(so_dong)} dòng; đo {self.lan} lần mỗi đường, lấy trung vị.")
        bat_dau_tat_ca = time.monotonic()
        with override_settings(ROOT_URLCONF="knjsc.urls_bangtinh", GRID_ONLY_TABLES=set(),
                               ALLOWED_HOSTS=[*settings.ALLOWED_HOSTS, "testserver"]):
            c = Client()
            c.force_login(nguoi)
            gt = o["giai_thich"]
            # ── Đọc ──
            self._do("Trang chủ KN CRM /", DOC, self._get(c, "/"), giai_thich=gt)
            self._do("Thư mục /thu-muc/ (cây Quý ▸ Tháng)", DOC, self._get(c, "/thu-muc/"), giai_thich=gt)
            self._do("Lưới vận đơn mặc định", DOC, self._get(c, goc), giai_thich=gt)
            self._do("Lưới lọc tháng hiện tại", DOC, self._get(c, f"{goc}?{loc_thang}"), giai_thich=gt)
            self._do("Lưới trang 500", DOC, self._get(c, f"{goc}?trang=500"), giai_thich=gt)
            self._do("Sắp xếp theo Tên khách (cột tách)", DOC, self._get(c, f"{goc}?sap=ten_khach"), giai_thich=gt)
            self._do("Sắp xếp theo Thành phố (khoá JSON)", DOC, self._get(c, f"{goc}?sap=thanh_pho&chieu=giam"), giai_thich=gt)
            self._do("Tìm nhanh `tim=Taylor`", DOC, self._get(c, f"{goc}?tim=Taylor"), giai_thich=gt)
            self._do("Lọc trạng thái + chứa chữ + sắp xếp", DOC,
                     self._get(c, f"{goc}?f_trang_thai_vc__trong=%C4%90ang%20giao&f_ten_khach__chua=Taylor&sap=ngay"),
                     giai_thich=gt)
            self._do("Chỉ dòng trùng `trung=1`", DOC, self._get(c, f"{goc}?trung=1"), giai_thich=gt)
            self._do("Hộp lọc Trạng thái VC (cột tách)", DOC, self._get(c, f"{goc}loc/trang_thai_vc/"), giai_thich=gt)
            self._do("Hộp lọc Thành phố (khoá JSON)", DOC, self._get(c, f"{goc}loc/thanh_pho/"), giai_thich=gt)
            self._do("Hộp lọc Tên khách (cột tách, 86 nghìn giá trị)", DOC, self._get(c, f"{goc}loc/ten_khach/"), giai_thich=gt)
            self._do("moi-nhat/ (mỗi tab hỏi mỗi 8 giây)", HOI, self._get(c, f"{goc}moi-nhat/"), giai_thich=gt)
            self._do("tree_service.month_counts (Vận đơn)", DOC,
                     lambda: tree_service.month_counts(nguoi, van_don.department), giai_thich=gt)

            # ── Ghi ──
            def luu_o(n):
                def du_lieu():
                    pks = rng.sample(pk_vd, n)
                    return {"o": [f"{pk}:ghi_chu" for pk in pks], "gt": [f"đo tải {rng.randrange(9999)}" for _ in pks]}
                return du_lieu
            self._do("luu-o 1 ô", GHI, self._post(c, f"{goc}luu-o/", luu_o(1)))
            self._do("luu-o 20 ô (kéo điền)", GHI, self._post(c, f"{goc}luu-o/", luu_o(20)))
            self._do("luu-o 500 ô (dán)", GHI, self._post(c, f"{goc}luu-o/", luu_o(500)))
            self._do("dong-moi (thêm một dòng)", GHI, self._post(c, f"{goc}dong-moi/", lambda: {
                "ma_don": f"PERF-DO-{rng.randrange(10**7):07d}", "ngay": hom_nay.isoformat(),
                "ten_khach": "Khách đo tải", "so_dien_thoai": f"403{rng.randrange(10**7):07d}",
                "thanh_pho": "Calgary", "gia_tien": "120", "trang_thai_vc": "Đã lên đơn", "_stt": "2",
            }))
            self._do(f"dinh-dang {min(100, GRID_FORMAT_CELLS_MAX)} ô đậm", GHI, self._post(c, f"{goc}dinh-dang/", lambda: {
                "o": [f"{pk}:ghi_chu" for pk in rng.sample(pk_vd, 100)], "b": "1",
            }))

            # ── Bảng Sale có cột tính sẵn ──
            if bang_sale is not None:
                cs = Client()
                cs.force_login(nguoi_sale)
                goc_sale = f"/bang-tinh/{bang_sale.code}/"
                pk_sale = list(DataRecord.objects.in_scope(nguoi_sale).filter(table=bang_sale).values_list("pk", flat=True)[:2000])
                self._do("Lưới perf_sale mặc định (có cột tính sẵn)", DOC, self._get(cs, goc_sale), giai_thich=gt)
                self._do("luu-o 20 ô Số lượng → tính lại Doanh thu", GHI, self._post(cs, f"{goc_sale}luu-o/", lambda: {
                    "o": [f"{pk}:so_luong" for pk in rng.sample(pk_sale, 20)],
                    "gt": [str(rng.randrange(1, 9)) for _ in range(20)],
                }))

            # ── Nền ──
            luoi = grid_service.build_grid(nguoi, {}, table=van_don)
            ds_xuat = luoi.queryset.order_by("-pk")[:50_000]
            def xuat():
                wb = export_service.build_workbook(ds_xuat, luoi.columns, title=van_don.name)
                wb.save(os.devnull)
            self._do("Xuất Excel 50.000 dòng (worker nền)", NEN, xuat, lan=1)

            # ── Tính lại cột tính sẵn (Manager đổi công thức) ──
            if bang_sale is not None:
                kq = self._do(f"Tính lại cột tính sẵn perf_sale ({_so(DataRecord.all_objects.filter(table=bang_sale).count())} dòng)",
                              TINH, lambda: table_service.resync_table(bang_sale), lan=1)
                kq.ghi_chu = "resync_table đồng bộ trong request"
            if not o["bo_tinh_lai_lon"]:
                kq = self._do(f"Tính lại cột tách bảng vận đơn ({_so(so_dong)} dòng)",
                              TINH, lambda: table_service.resync_table(van_don), lan=1)
                kq.ghi_chu = "cùng đường resync_table — cỡ khi Manager thêm cột tính sẵn vào bảng vận đơn"

        tong_giay = time.monotonic() - bat_dau_tat_ca
        tep = self._ghi_bao_cao(o["nhan"], so_dong, tong_giay)
        so_hong = sum(1 for k in self.ket_qua if k.dat is False)
        self.stdout.write(self.style.SUCCESS(f"\nĐã ghi {tep} — {len(self.ket_qua)} đường, "
                                             f"{so_hong} KHÔNG ĐẠT, tổng {tong_giay:.0f} giây."))

    # ── Báo cáo ──
    def _may(self):
        with connection.cursor() as c:
            c.execute("SHOW server_version")
            pg = c.fetchone()[0]
            c.execute("SHOW shared_buffers")
            sb = c.fetchone()[0]
            c.execute("SHOW work_mem")
            wm = c.fetchone()[0]
            c.execute("SHOW max_connections")
            mc = c.fetchone()[0]
        ram = ""
        try:
            with open("/proc/meminfo", encoding="utf-8") as f:
                for dong in f:
                    if dong.startswith("MemTotal"):
                        ram = f"{int(dong.split()[1]) // 1024 // 1024} GB"
        except OSError:
            pass
        return [
            f"- Máy: {os.cpu_count()} nhân, RAM {ram or '?'}, {platform.system()} {platform.release()}",
            f"- PostgreSQL {pg}: shared_buffers {sb}, work_mem {wm}, max_connections {mc}",
            f"- Django settings `{os.environ.get('DJANGO_SETTINGS_MODULE', '')}`, DEBUG={settings.DEBUG}, "
            f"CONN_MAX_AGE={settings.DATABASES['default'].get('CONN_MAX_AGE')}, "
            f"SESSION_ENGINE `{settings.SESSION_ENGINE.rsplit('.', 1)[-1]}`",
        ]

    def _ghi_bao_cao(self, nhan, so_dong, tong_giay):
        thu_muc = settings.STORAGE_DIR / "perf"
        thu_muc.mkdir(parents=True, exist_ok=True)
        tep = thu_muc / f"{date.today().isoformat()}-don-le{('-' + nhan) if nhan else ''}.md"
        dong = [
            f"# Đo đơn lẻ KN CRM — {date.today().isoformat()}" + (f" ({nhan})" if nhan else ""),
            "",
            f"Một người, không tải, {self.lan} lần mỗi đường, lấy trung vị. Bảng vận đơn {_so(so_dong)} dòng.",
            "Ngưỡng: đọc ≤ %d ms, ghi ≤ %d ms, hỏi mốc ≤ %d ms, tính lại ≤ %d s (core/constants.py)."
            % (PERF_READ_P95_MS, PERF_WRITE_P95_MS, PERF_POLL_P95_MS, PERF_RECOMPUTE_SECONDS),
            "", *self._may(), "",
            "| # | Đường | Nhóm | Trung vị | Nhỏ nhất | Lớn nhất | Truy vấn | Lệnh chậm nhất | Ngưỡng | Kết quả |",
            "|--:|---|---|--:|--:|--:|--:|--:|--:|---|",
        ]
        for i, k in enumerate(self.ket_qua, start=1):
            dat = "—" if k.dat is None else ("ĐẠT" if k.dat else "**KHÔNG ĐẠT**")
            nguong = "—" if k.nguong is None else f"{_so(k.nguong)} ms"
            dong.append(
                f"| {i} | {k.ten} | {k.nhom} | {_so(k.trung_vi)} ms | {_so(min(k.ms))} | {_so(max(k.ms))} "
                f"| {k.so_truy_van} | {_so(k.cham_nhat[1])} ms | {nguong} | {dat} |"
            )
        ghi_chu = [f"- {k.ten}: {k.ghi_chu}" for k in self.ket_qua if k.ghi_chu]
        if ghi_chu:
            dong += ["", "Ghi chú:", *ghi_chu]
        dong += ["", f"Tổng thời gian đo: {tong_giay:.0f} giây."]
        giai_thich = [k for k in self.ket_qua if k.giai_thich]
        if giai_thich:
            dong += ["", "## Phụ lục — EXPLAIN (ANALYZE, BUFFERS) lệnh chậm nhất mỗi đường", ""]
            for k in giai_thich:
                dong += [f"### {k.ten} — {k.cham_nhat[1]:.0f} ms", "", "```sql",
                         k.cham_nhat[0][:1500], "```", "", "```", k.giai_thich, "```", ""]
        tep.write_text("\n".join(dong) + "\n", encoding="utf-8")
        return tep
