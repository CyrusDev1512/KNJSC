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

Các lệnh ghi (lưu ô, định dạng) sửa thật dữ liệu: lệnh chỉ chọn dòng
giả `PERF-*` do `seed_perf` sinh để ghi, có dưới `SO_DONG_DICH_TOI_THIEU` dòng
thì dừng trước khi đo. DEBUG tắt thì từ chối như mọi lệnh dữ liệu giả, trừ khi
ghi rõ `--dong-y-chay-that` (TL-98).
"""
import os
import platform
import random
import statistics
import time
import uuid
from unittest.mock import patch
from datetime import date

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.http import QueryDict
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext

from core.constants import (
    GRID_FORMAT_CELLS_MAX, PERF_POLL_P95_MS, PERF_READ_P95_MS, PERF_RECOMPUTE_SECONDS,
    PERF_WRITE_P95_MS,
)
from core.management.commands.seed_perf import PERF_PREFIX, SALE_TABLE_CODE, chan_khi_debug_tat
from forms_builder.models import DataRecord, TableDef

#: Lệnh ghi chỉ đụng dòng PERF-*: lấy tối đa chừng này dòng làm đích, ít hơn mức tối thiểu (lượt dán 500 ô)
#: thì dừng — không bao giờ ghi vào dòng thật (TL-98)
SO_DONG_DICH_TOI_DA = 5_000
SO_DONG_DICH_TOI_THIEU = 500
#: Lượt sửa 20 ô Số lượng của bảng Sale đo tải
SO_O_SALE = 20

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
        parser.add_argument("--dong-y-chay-that", action="store_true", dest="dong_y",
                            help="Cho phép chạy khi DEBUG tắt. Chỉ dùng khi biết chắc mình làm gì.")

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
            r = client.post(duong_dan, du_lieu() if callable(du_lieu) else du_lieu, content_type="application/json")
            if r.status_code != ma:
                raise CommandError(f"POST {duong_dan} trả {r.status_code}, mong {ma}: "
                                   + r.content.decode("utf-8", "replace")[:300])
        return ham

    # ── Chạy ──
    def handle(self, *args, **o):
        chan_khi_debug_tat(o["dong_y"])
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
        pk_vd = list(DataRecord.objects.in_scope(nguoi)
                     .filter(table=van_don, data__ma_don__startswith=PERF_PREFIX)
                     .order_by("-pk").values_list("pk", flat=True)[:SO_DONG_DICH_TOI_DA])
        if len(pk_vd) < SO_DONG_DICH_TOI_THIEU:
            raise CommandError(
                f"Chỉ có {len(pk_vd)} dòng giả {PERF_PREFIX}* trong phạm vi {nguoi.username} — các lệnh ghi của "
                f"phép đo chỉ được đụng dòng giả (cần ít nhất {SO_DONG_DICH_TOI_THIEU}). "
                "Chạy `manage.py seed_perf` trước.")
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
            self._do("Lưới lọc tháng hiện tại", DOC, self._get(c, f"{goc}du-lieu/?{loc_thang}"), giai_thich=gt)
            self._do("Khối ở vị trí 49.900", DOC, self._get(c, f"{goc}du-lieu/?offset=49900"), giai_thich=gt)
            self._do("Sắp xếp theo Tên khách (cột tách)", DOC, self._get(c, f"{goc}du-lieu/?sap=ten_khach"), giai_thich=gt)
            self._do("Sắp xếp theo Thành phố (khoá JSON)", DOC, self._get(c, f"{goc}du-lieu/?sap=thanh_pho&chieu=giam"), giai_thich=gt)
            self._do("Tìm nhanh `tim=Taylor`", DOC, self._get(c, f"{goc}du-lieu/?tim=Taylor"), giai_thich=gt)
            self._do("Lọc trạng thái + chứa chữ + sắp xếp", DOC,
                     self._get(c, f"{goc}du-lieu/?f_trang_thai_vc__trong=%C4%90ang%20giao&f_ten_khach__chua=Taylor&sap=ngay"),
                     giai_thich=gt)
            self._do("Chỉ dòng trùng `trung=1`", DOC, self._get(c, f"{goc}du-lieu/?trung=1"), giai_thich=gt)
            self._do("Hộp lọc Trạng thái VC (cột tách)", DOC, self._get(c, f"{goc}loc/trang_thai_vc/"), giai_thich=gt)
            self._do("Hộp lọc Thành phố (khoá JSON)", DOC, self._get(c, f"{goc}loc/thanh_pho/"), giai_thich=gt)
            self._do("Hộp lọc Tên khách (cột tách, 86 nghìn giá trị)", DOC, self._get(c, f"{goc}loc/ten_khach/"), giai_thich=gt)
            self._do("moi-nhat/ (mỗi tab hỏi mỗi 8 giây)", HOI, self._get(c, f"{goc}moi-nhat/"), giai_thich=gt)
            # month_counts đã bỏ cùng cấp Quý/Tháng của thư mục (ADR-040);
            # trang thư mục đo qua table_stats bên trong build
            self._do("tree_service.build (trang thư mục)", DOC,
                     lambda: tree_service.build(nguoi), giai_thich=gt)

            # ── Ghi JSON/CAS hiện hành, đọc old mới cho từng lượt ──
            def payload(n, formatting=False):
                def make():
                    ids = rng.sample(pk_vd, n)
                    rows = DataRecord.objects.filter(pk__in=ids, data__ma_don__startswith=PERF_PREFIX)
                    return {"operation": str(uuid.uuid4()), "kind": "format" if formatting else "paste",
                        "cells": [{"id": r.pk, "column": "ghi_chu", "property": "fs" if formatting else "value",
                                   "old": r.style.get("ghi_chu", {}).get("fs") if formatting else r.data.get("ghi_chu"),
                                   "value": rng.choice([12,13,14]) if formatting else f"đo tải {uuid.uuid4().hex}"}
                                  for r in rows]}
                return make
            for n in (1, 20, SO_DONG_DICH_TOI_THIEU):
                self._do(f"luu-json {n} ô", GHI, self._post(c, f"{goc}luu-json/", payload(n)))
            self._do("luu-json định dạng 100 ô", GHI,
                     self._post(c, f"{goc}luu-json/", payload(100, True)))
            self.stdout.write("Không đo dong-moi/ và sửa perf_sale qua CRM: các đường này đã được thay thế.")

            # ── Nền ──
            # QueryDict, không phải dict: build_grid gọi params.getlist với bảng vận đơn (gãy từ cfecde6)
            luoi = grid_service.build_grid(nguoi, QueryDict(), table=van_don)
            ds_xuat = luoi.queryset.order_by("-pk")[:50_000]
            def xuat():
                wb = export_service.build_workbook(ds_xuat, luoi.columns, title=van_don.name)
                wb.save(os.devnull)
            self._do("Xuất Excel 50.000 dòng (worker nền)", NEN, xuat, lan=1)

            # Không chấm một lượt no-op là tính lại thành công. Fixture chỉ dành cho DB kiểm tải.
            if bang_sale is not None and not o["bo_tinh_lai_lon"]:
                self._recompute(bang_sale)
            else:
                self.stdout.write("Tính lại: CHƯA ĐO (không có fixture hoặc đã chọn bỏ).")


        tong_giay = time.monotonic() - bat_dau_tat_ca
        tep = self._ghi_bao_cao(o["nhan"], so_dong, tong_giay)
        so_hong = sum(1 for k in self.ket_qua if k.dat is False)
        self.stdout.write(self.style.SUCCESS(f"\nĐã ghi {tep} — {len(self.ket_qua)} đường, "
                                             f"{so_hong} KHÔNG ĐẠT, tổng {tong_giay:.0f} giây."))

    def _recompute(self, table):
        """Chuẩn bị số tính sai có chủ đích ngoài thời gian đo, kiểm lại từng kết quả."""
        from django.db.models import F, Func, Value, JSONField
        from forms_builder.services import table_service
        name = str(settings.DATABASES['default']['NAME'])
        if name != 'knjsc_loadtest' and not name.startswith('test_'):
            raise CommandError("Tính lại chỉ chạy trên database kiểm thử riêng.")
        rows = DataRecord.all_objects.filter(table=table)
        if rows.exclude(data__ma_don__startswith=PERF_PREFIX).exists():
            raise CommandError("Bảng tính lại có dòng không phải PERF-*; không sửa.")
        columns = list(table.columns.all())
        computed = [c for c in columns if c.is_computed]
        if not computed or not rows.exists():
            self.stdout.write("Tính lại: CHƯA ĐO (không có ô tính).")
            return
        # Chỉ fixture riêng; tạo công việc ghi thật trước khi bắt đầu bấm giờ.
        expr = F('data')
        for col in computed:
            expr = Func(expr, Value('{'+col.code+'}'), Value('"__PERF_STALE__"'),
                        function='jsonb_set', output_field=JSONField())
        rows.update(data=expr)
        with patch.object(table_service, 'RECOMPUTE_THREADS', 1):
            result = self._do(f"Tính lại {rows.count()} dòng — một luồng", TINH,
                              lambda: table_service.resync_table(table), lan=1)
        for row in rows.iterator(chunk_size=1000):
            for col in computed:
                expected = col.compute(row.data)
                if row.data.get(col.code) != (None if expected is None else str(expected)):
                    raise CommandError("Tính lại trả kết quả sai.")
        result.ghi_chu = "Fixture PERF riêng có ô sai trước đo; một luồng để đếm đủ SQL, không đại diện tải worker song song."

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
