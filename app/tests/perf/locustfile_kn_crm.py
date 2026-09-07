"""Kiểm tải KN CRM: 100 người cùng lúc trên 100 nghìn khách — AC-10.6, NFR-2, docs/06 tầng 9.

Chạy trên máy đã có `du_lieu_mau` (tài khoản) và `seed_perf --so-dong 100000
--so-thang 24 --dien-day --bang-sale` (dữ liệu), máy chủ KN CRM ở chế độ
gunicorn (không đo trên `runserver`):

    locust -f tests/perf/locustfile_kn_crm.py --host http://localhost:8021 \\
           --users 100 --spawn-rate 10 --run-time 5m --headless --reset-stats

Không bấm giao diện (không Playwright): mỗi người ảo là **một tab lưới** gọi
đúng những HTTP mà trình duyệt gọi, kể cả hỏi `moi-nhat/` mỗi 8 giây ở nền.
Nhịp thao tác như người thật: nhân viên 4–12 giây một thao tác, quản lý thưa
hơn (đo 07.09: 100 người ≈ 15 yêu cầu/giây, trong đó một nửa là poll). Bốn vai
theo trọng số (100 người → đúng 70 / 20 / 7 / 3):

- **Nhân viên vận đơn (70)** "di qua di lại": mở lưới tháng hiện tại, chuyển
  trang, sắp xếp, hộp lọc, áp bộ lọc, tìm nhanh, xem dòng trùng, sửa 1 ô,
  kéo điền 5 ô, định dạng 10 ô, thỉnh thoảng thêm dòng.
- **Sale / Marketing (20)**: trang chủ, thư mục, lưới bảng của bộ phận mình
  (`perf_sale` có cột tính sẵn / `bao_cao_mkt`), lọc, sửa ô; Sale lên đơn ở
  KN ERP (`ERP_HOST`) thỉnh thoảng — đơn đẩy sang bảng vận đơn.
- **Trưởng nhóm / quản lý (7)**: dán 200–500 ô, xoá rồi khôi phục 20 dòng,
  tạo thư mục, xuất Excel một lần trong phiên (tác vụ nền).
- **Manager (3)**: sau `MANAGER_DELAY` giây **thêm một cột tính sẵn** vào
  `perf_sale` (20.000 dòng) rồi **sửa** công thức của nó; một người trong
  ba làm việc đó trên bảng vận đơn 100.000 dòng. Cột thêm ra được gỡ ở
  cuối phiên.

**Tự chấm khi dừng** (ngưỡng ở `core/constants.py`, "như Excel trên máy thường";
`--reset-stats` để chấm từ lúc cả 100 người đã đăng nhập xong — 20 giây đầu ai
cũng băm mật khẩu cùng lúc, không phải cảnh làm việc):
nhóm *đọc* p95 ≤ 1 s, nhóm *ghi* p95 ≤ 0,5 s, `moi-nhat/` p95 ≤ 0,3 s, không
yêu cầu nào hỏng, cột tính sẵn 100.000 dòng ≤ 30 s **và** p95 nhóm đọc của
những người khác trong lúc đó vẫn ≤ 1 s. In ĐẠT / KHÔNG ĐẠT từng dòng, thoát
mã 1 nếu có dòng đỏ, ghi báo cáo `storage/perf/<ngày>-tai-100.md`.

Biến môi trường: `ERP_HOST` (`http://localhost:8020`, Sale đăng nhập riêng ở
đó để lên đơn); `KNJSC_MAT_KHAU`; `MANAGER_DELAY` (giây, mặc định 90); `MANAGER_VAN_DON=0`
bỏ bước đổi cột trên bảng vận đơn (chạy thử ngắn);
`KNJSC_PERF_DIR` (thư mục báo cáo, mặc định `../storage/perf`).
"""
import os
import random
import re
import statistics
import sys
import time
from datetime import date
from pathlib import Path

import gevent
from locust import HttpUser, between, events, task
from requests.adapters import HTTPAdapter

try:
    from core.constants import (
        GRID_POLL_SECONDS, PERF_POLL_P95_MS, PERF_READ_P95_MS, PERF_RECOMPUTE_SECONDS, PERF_WRITE_P95_MS,
    )
except Exception:  # noqa: BLE001 — chạy ngoài thư mục app thì dùng đúng con số đã chốt
    GRID_POLL_SECONDS, PERF_READ_P95_MS, PERF_WRITE_P95_MS, PERF_POLL_P95_MS, PERF_RECOMPUTE_SECONDS = 8, 1000, 500, 300, 30

MAT_KHAU = os.environ.get("KNJSC_MAT_KHAU", "MatKhauTam-2026")
ERP_HOST = os.environ.get("ERP_HOST", "http://localhost:8020")
MANAGER_DELAY = int(os.environ.get("MANAGER_DELAY", "90"))
MANAGER_VAN_DON = os.environ.get("MANAGER_VAN_DON", "1") == "1"    # 0: không đổi cột trên bảng vận đơn (chạy thử ngắn)
PERF_DIR = Path(os.environ.get("KNJSC_PERF_DIR", str(Path(__file__).resolve().parents[3] / "storage" / "perf")))

VAN_DON = "van_don"
SALE = "perf_sale"
MKT = "bao_cao_mkt"
TRANG_THAI = ["Đã lên đơn", "Đang giao", "Đã nhận hàng", "Hẹn lại"]
THANH_PHO = ["Calgary", "Toronto", "Vancouver", "Montreal"]
TIM = ["Taylor", "Emily", "Yonge", "Calgary", "403"]

# Nhóm chấm điểm nằm ở đầu tên yêu cầu: "đọc: …", "ghi: …", "hỏi: …", "nền: …", "tính lại: …"
DOC, GHI, HOI, NEN, TINH = "đọc", "ghi", "hỏi", "nền", "tính lại"
NGUONG = {DOC: PERF_READ_P95_MS, GHI: PERF_WRITE_P95_MS, HOI: PERF_POLL_P95_MS}

#: Mọi yêu cầu (mốc giây, tên, ms, hỏng) — để tính p95 theo cửa sổ thời gian
NHAT_KY = []
#: Cửa sổ Manager tính lại cột tính sẵn: (bảng, bắt đầu, kết thúc, ms, hỏng)
CUA_SO_TINH_LAI = []
_MA_TAB = [0]
_SO_QUAN_LY = [0]
#: Lượt bị từ chối vì dòng vừa bị người khác xoá — tranh chấp thật giữa 100 người, không phải lỗi
TRANH_CHAP = [0]


def _thang_nay():
    hom_nay = date.today()
    from calendar import monthrange
    dau = hom_nay.replace(day=1)
    cuoi = hom_nay.replace(day=monthrange(hom_nay.year, hom_nay.month)[1])
    return f"f_ngay__lon_bang={dau.isoformat()}&f_ngay__nho_bang={cuoi.isoformat()}"


def _csrf(client, duong_dan, name=None):
    kq = client.get(duong_dan, name=name or duong_dan)
    m = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', kq.text)
    return m.group(1) if m else client.cookies.get("csrftoken", "")


def _dang_nhap(client, ten, goc=""):
    """Đăng nhập ở máy chủ của client, hoặc ở `goc` (KN ERP) — cookie giữ riêng từng tên máy."""
    token = _csrf(client, f"{goc}/dang-nhap/", name="đăng nhập")
    client.post(f"{goc}/dang-nhap/", {"username": ten, "password": MAT_KHAU, "csrfmiddlewaretoken": token},
                headers={"Referer": (goc or client.base_url) + "/dang-nhap/"}, name="đăng nhập")


class TabLuoi(HttpUser):
    """Một tab Bảng tính: đăng nhập, nhớ pk các dòng đang thấy, hỏi `moi-nhat/` mỗi 8 giây ở nền."""

    abstract = True
    tai_khoan = ""
    bang = VAN_DON

    def on_start(self):
        _MA_TAB[0] += 1
        self.stt = _MA_TAB[0]
        # Như trình duyệt: kết nối keep-alive bị máy chủ đóng đúng lúc gửi thì gửi lại
        # một lần (chỉ GET — urllib3 không thử lại POST)
        self.client.mount("http://", HTTPAdapter(max_retries=1))
        _dang_nhap(self.client, self.tai_khoan)
        self.goc = f"/bang-tinh/{self.bang}/"
        self.pks = []
        self.qs = ""
        self._poll = gevent.spawn(self._hoi_moc)

    def on_stop(self):
        if getattr(self, "_poll", None):
            self._poll.kill(block=False)

    # ── tiện ích ──
    def _headers(self):
        token = self.client.cookies.get("csrftoken", "")
        return {"Referer": self.client.base_url + self.goc, "X-CSRFToken": token, "HX-Request": "true"}

    def _luoi(self, qs="", ten="đọc: lưới"):
        kq = self.client.get(f"{self.goc}?{qs}" if qs else self.goc, name=ten)
        pks = re.findall(r"/o/(\d+)/", kq.text)
        if pks:
            self.pks = list(dict.fromkeys(int(p) for p in pks))
        self.qs = qs
        return kq

    def _post(self, duong, du_lieu, ten, ma=(200,)):
        with self.client.post(duong, du_lieu, headers=self._headers(), name=ten,
                              catch_response=True, allow_redirects=False) as kq:
            if kq.status_code == 403 and ("xoá" in kq.text or "xoa-dong" in ten or "khoi-phuc-dong" in ten):
                # Dòng vừa bị người khác xoá hay khôi phục (bảy trưởng nhóm cùng xoá/khôi
                # phục trên một trang): máy chủ từ chối đúng (quy tắc 8), người thật tải
                # lại trang rồi làm tiếp — tranh chấp, không phải lỗi
                TRANH_CHAP[0] += 1
                self.pks = []
                kq.success()
            elif kq.status_code not in ma:
                kq.failure(f"HTTP {kq.status_code}: {kq.text[:120]}")
            return kq

    def _hoi_moc(self):
        """Đúng như trình duyệt: hỏi mốc mới nhất mỗi GRID_POLL_SECONDS giây khi tab còn mở."""
        while True:
            gevent.sleep(GRID_POLL_SECONDS + random.random())
            self.client.get(f"{self.goc}moi-nhat/", name=f"{HOI}: moi-nhat/")

    def _o(self, n, cot="ghi_chu"):
        if not self.pks:
            self._luoi(self.qs)
        chon = random.sample(self.pks, min(n, len(self.pks))) if self.pks else []
        return [f"{pk}:{cot}" for pk in chon]

    # ── hành vi chung ──
    def luu_o(self, n, cot="ghi_chu", ten=None):
        o = self._o(n, cot)
        if not o:
            return
        self._post(f"{self.goc}luu-o/", {"o": o, "gt": [f"tải {random.randrange(9999)}" for _ in o]},
                   ten or f"{GHI}: luu-o {n} ô")

    def dinh_dang(self, n):
        o = self._o(n)
        if not o:
            return
        self._post(f"{self.goc}dinh-dang/", {"o": o, "b": "1", "bg": random.choice(["vang", "xanh", ""])},
                   f"{GHI}: dinh-dang {n} ô")


class NhanVienVanDon(TabLuoi):
    """70 người: di qua di lại trên bảng vận đơn 100.000 dòng — một thao tác mỗi 4–12 giây
    (người thật nhìn trang vài giây rồi mới bấm tiếp), cộng poll `moi-nhat/` mỗi 8 giây."""

    weight = 70
    wait_time = between(4, 12)
    tai_khoan = "vd.staff"
    bang = VAN_DON

    @task(6)
    def mo_luoi_thang(self):
        self._luoi(_thang_nay(), f"{DOC}: lưới lọc tháng")

    @task(5)
    def chuyen_trang(self):
        trang = random.randint(1, 6)
        giu = "&".join(p for p in self.qs.split("&") if p and not p.startswith("trang="))
        self._luoi(f"{giu}&trang={trang}" if giu else f"trang={trang}", f"{DOC}: chuyển trang")

    @task(3)
    def sap_xep(self):
        cot = random.choice(["ten_khach", "ngay", "thanh_pho", "gia_tien", "trang_thai_vc"])
        chieu = random.choice(["", "&chieu=giam"])
        self._luoi(f"{_thang_nay()}&sap={cot}{chieu}", f"{DOC}: sắp xếp")

    @task(3)
    def hop_loc(self):
        cot = random.choice(["trang_thai_vc", "thanh_pho", "nguoi_ban", "pttt"])
        self.client.get(f"{self.goc}loc/{cot}/", name=f"{DOC}: hộp lọc")

    @task(3)
    def ap_loc(self):
        self._luoi(f"f_trang_thai_vc__trong={random.choice(TRANG_THAI)}&f_thanh_pho__trong={random.choice(THANH_PHO)}",
                   f"{DOC}: áp bộ lọc")

    @task(2)
    def tim_nhanh(self):
        self._luoi(f"tim={random.choice(TIM)}", f"{DOC}: tìm nhanh")

    @task(1)
    def dong_trung(self):
        self._luoi(f"{_thang_nay()}&trung=1", f"{DOC}: dòng trùng")

    @task(4)
    def sua_mot_o(self):
        self.luu_o(1, ten=f"{GHI}: luu-o 1 ô")

    @task(2)
    def keo_dien(self):
        self.luu_o(5, ten=f"{GHI}: luu-o 5 ô")

    @task(1)
    def dinh_dang_10(self):
        self.dinh_dang(10)

    @task(1)
    def them_dong(self):
        so = random.randrange(10**7)
        self._post(f"{self.goc}dong-moi/", {
            "ma_don": f"PERF-T{so:07d}", "ngay": date.today().isoformat(), "ten_khach": f"Khách tải {so}",
            "so_dien_thoai": f"403{so:07d}", "thanh_pho": "Calgary", "gia_tien": "120",
            "trang_thai_vc": "Đã lên đơn", "_stt": "2",
        }, f"{GHI}: dong-moi")


class NhanVienSaleMkt(TabLuoi):
    """20 người: Sale trên `perf_sale` (có cột tính sẵn), Marketing trên `bao_cao_mkt`.
    Tài khoản Manager/Leader vì Staff chỉ thấy dòng mình tạo, mà dữ liệu đo là do seed tạo."""

    weight = 20
    wait_time = between(5, 15)

    def on_start(self):
        la_sale = _MA_TAB[0] % 2 == 0
        self.tai_khoan = "sale.leader" if la_sale else "mkt.leader"
        self.bang = SALE if la_sale else MKT
        self.la_sale = la_sale
        super().on_start()
        if la_sale:
            _dang_nhap(self.client, self.tai_khoan, goc=ERP_HOST)      # lên đơn ở KN ERP

    @task(3)
    def trang_chu(self):
        self.client.get("/", name=f"{DOC}: trang chủ")

    @task(2)
    def thu_muc(self):
        self.client.get("/thu-muc/", name=f"{DOC}: thư mục")

    @task(5)
    def mo_luoi(self):
        self._luoi("", f"{DOC}: lưới bộ phận")

    @task(2)
    def loc(self):
        qs = f"f_trang_thai__trong={random.choice(['Mới', 'Chốt', 'Huỷ'])}" if self.la_sale else "trang=1"
        self._luoi(qs, f"{DOC}: áp bộ lọc")

    @task(2)
    def sua_o(self):
        cot = "so_luong" if self.la_sale else None
        if cot:
            o = self._o(3, cot)
            if o:
                self._post(f"{self.goc}luu-o/", {"o": o, "gt": [str(random.randint(1, 9)) for _ in o]},
                           f"{GHI}: luu-o 3 ô (tính lại Doanh thu)")
        else:
            self.luu_o(1, ten=f"{GHI}: luu-o 1 ô")

    @task(1)
    def len_don(self):
        """Sale lên đơn ở KN ERP — đơn đẩy sang bảng vận đơn (cùng cookie vì cùng tên máy)."""
        if not self.la_sale:
            return
        token = _csrf(self.client, f"{ERP_HOST}/len-don/", name=f"{DOC}: ERP lên đơn (form)")
        so = random.randrange(10_000_000, 99_999_999)
        with self.client.post(f"{ERP_HOST}/len-don/", {
            "csrfmiddlewaretoken": token,
            "phone": f"09{so}", "customer_name": f"Khách tải {so}",
            "market": "ca", "state": "AB", "city": "Calgary", "zipcode": "T1Y1J1",
            "address_line": "12 Main St", "payment_method": "transfer", "currency": "CAD",
            "line_product": ["retinol-cream"], "line_quantity": ["2"], "line_price": ["120.00"],
        }, headers={"Referer": f"{ERP_HOST}/len-don/"}, name=f"{GHI}: ERP lên đơn [POST]",
                catch_response=True, allow_redirects=False) as kq:
            if kq.status_code not in (200, 302):
                kq.failure(f"HTTP {kq.status_code}")


class TruongNhom(TabLuoi):
    """7 người: dán nhiều ô, xoá và khôi phục dòng, tạo thư mục, xuất Excel một lần."""

    weight = 7
    wait_time = between(8, 20)

    def on_start(self):
        # vd.manager làm việc nặng trên bảng vận đơn (Vận đơn không có Leader trong dữ liệu mẫu),
        # sale.leader trên perf_sale — Leader như Manager trong bộ phận mình (ADR-015)
        tren_van_don = _MA_TAB[0] % 3 != 0
        self.tai_khoan = "vd.manager" if tren_van_don else "sale.leader"
        self.bang = VAN_DON if tren_van_don else SALE
        self.da_xuat = False
        super().on_start()

    @task(3)
    def mo_luoi(self):
        self._luoi(_thang_nay() if self.bang == VAN_DON else "", f"{DOC}: lưới lọc tháng")

    @task(3)
    def dan_nhieu_o(self):
        n = random.choice([200, 300, 500])
        # 500 ô là 5 cột × 100 dòng của trang đang xem: mỗi dòng nhiều ô, đúng như dán một khối
        if not self.pks:
            self._luoi(self.qs)
        cac_cot = ["ghi_chu", "thanh_pho", "bang", "zipcode", "pttt"] if self.bang == VAN_DON else ["ghi_chu", "thanh_pho"]
        o = [f"{pk}:{cot}" for pk in self.pks[:100] for cot in cac_cot][:n]
        if o:
            self._post(f"{self.goc}luu-o/", {"o": o, "gt": [f"dán {random.randrange(999)}" for _ in o]},
                       f"{GHI}: luu-o dán {n} ô")

    @task(2)
    def xoa_va_khoi_phuc(self):
        o = self._o(20)
        pks = [x.split(":")[0] for x in o]
        if not pks:
            return
        self._post(f"{self.goc}xoa-dong/", {"pk": pks}, f"{GHI}: xoa-dong 20 dòng")
        self._post(f"{self.goc}khoi-phuc-dong/", {"pk": pks}, f"{GHI}: khoi-phuc-dong 20 dòng")

    @task(1)
    def tao_thu_muc(self):
        self._post("/bang-tinh/thu-muc/moi/", {"name": f"Tải {random.randrange(9999)}", "ve": self.bang},
                   f"{GHI}: thu-muc moi", ma=(200, 302))

    @task(1)
    def xuat_excel(self):
        if self.da_xuat:
            return
        self.da_xuat = True
        with self.client.get(f"{self.goc}xuat/?{_thang_nay()}", name=f"{NEN}: xuất Excel (tháng, tác vụ nền)",
                             catch_response=True, allow_redirects=False) as kq:
            if kq.status_code not in (200, 302):
                kq.failure(f"HTTP {kq.status_code}")


class QuanLy(TabLuoi):
    """3 người: giữa phiên thêm rồi sửa một cột tính sẵn — 20.000 dòng (Sale) và 100.000 dòng (Vận đơn)."""

    weight = 3
    wait_time = between(10, 20)

    def on_start(self):
        _SO_QUAN_LY[0] += 1
        self.tren_van_don = MANAGER_VAN_DON and _SO_QUAN_LY[0] == 1     # người đầu tiên làm trên bảng vận đơn
        self.tai_khoan = "vd.manager" if self.tren_van_don else "sale.manager"
        self.bang = VAN_DON if self.tren_van_don else SALE
        self.ma_cot = f"tai_{_MA_TAB[0]}"
        self.pk_cot = None
        self.da_them = self.da_sua = False
        self.bat_dau = time.time()
        super().on_start()

    @task(3)
    def mo_luoi(self):
        self._luoi("", f"{DOC}: lưới bộ phận")

    def _cot_tinh_san(self, ten, du_lieu, duong):
        """POST form sửa cột rồi ghi cửa sổ thời gian — trong lúc đó p95 người khác phải giữ."""
        token = _csrf(self.client, f"/bang/{self.bang}/cot/", name=f"{DOC}: trang Sửa cột")
        bat_dau = time.time()
        with self.client.post(duong, {**du_lieu, "csrfmiddlewaretoken": token},
                              headers={"Referer": self.client.base_url + f"/bang/{self.bang}/cot/"},
                              name=ten, catch_response=True, allow_redirects=False) as kq:
            hong = kq.status_code != 302
            if hong:
                kq.failure(f"HTTP {kq.status_code}: form không hợp lệ hoặc bị từ chối")
        # Bảng lớn tính lại ở tác vụ nền (ADR-016): đợi tới khi moi-nhat/ hết báo
        # `tinh_lai` — cửa sổ tính lại là từ lúc bấm Lưu tới lúc worker xong
        han = time.time() + 600
        while not hong and time.time() < han:
            gevent.sleep(2)
            kq = self.client.get(f"{self.goc}moi-nhat/", name=f"{HOI}: moi-nhat/")
            try:
                if kq.status_code != 200 or not kq.json().get("tinh_lai"):
                    break
            except ValueError:
                break
        CUA_SO_TINH_LAI.append((self.bang, bat_dau, time.time(), (time.time() - bat_dau) * 1000, hong))
        return not hong

    def _pk_cot_moi(self):
        kq = self.client.get(f"/bang/{self.bang}/cot/", name=f"{DOC}: trang Sửa cột")
        m = re.search(rf'cot=(\d+)[^>]*>[^<]*{re.escape(self.ma_cot)}|{re.escape(self.ma_cot)}.*?cot=(\d+)', kq.text, re.S)
        if m:
            return m.group(1) or m.group(2)
        return None

    @task(1)
    def cot_tinh_san(self):
        if time.time() - self.bat_dau < MANAGER_DELAY:
            return
        trai, phai = ("gia_tien", "so_luong") if self.tren_van_don else ("don_gia", "so_luong")
        so_dong = "100.000" if self.tren_van_don else "20.000"
        if not self.da_them:
            self.da_them = True
            if self._cot_tinh_san(f"{TINH}: thêm cột tính sẵn ({so_dong} dòng)", {
                "name": f"Tổng tải {self.stt}", "code": self.ma_cot, "field_type": "money", "order": "0",
                "is_computed": "on", "compute_op": "multiply", "compute_left": trai,
                "compute_right": phai, "compute_decimals": "2",
            }, f"/bang/{self.bang}/cot/"):
                self.pk_cot = self._pk_cot_moi()
        elif not self.da_sua and self.pk_cot:
            self.da_sua = True
            self._cot_tinh_san(f"{TINH}: sửa công thức cột tính sẵn ({so_dong} dòng)", {
                "name": f"Tổng tải {self.stt}", "code": self.ma_cot, "field_type": "money", "order": "0",
                "is_computed": "on", "compute_op": "add", "compute_left": trai,
                "compute_right": phai, "compute_decimals": "0",
            }, f"/bang/{self.bang}/cot/?cot={self.pk_cot}")

    def on_stop(self):
        super().on_stop()
        if self.pk_cot:
            token = self.client.cookies.get("csrftoken", "")
            self.client.post(f"/bang/{self.bang}/cot/{self.pk_cot}/bo/", {"csrfmiddlewaretoken": token},
                             headers={"Referer": self.client.base_url + f"/bang/{self.bang}/cot/"},
                             name=f"{TINH}: gỡ cột tính sẵn (dọn)", allow_redirects=False)


@events.spawning_complete.add_listener
def _da_vao_du(user_count, **kw):
    """`--reset-stats`: chấm từ lúc 100 người đã đăng nhập xong (trạng thái làm việc
    ổn định), bỏ 20 giây đầu ai cũng băm mật khẩu cùng lúc — nhật ký riêng cũng xoá theo."""
    if getattr(_ENV[0].parsed_options, "reset_stats", False) if _ENV[0] else False:
        NHAT_KY.clear()


_ENV = [None]


@events.init.add_listener
def _nho_moi_truong(environment, **kw):
    _ENV[0] = environment


# ── Ghi nhật ký từng yêu cầu để tính p95 theo cửa sổ ──
@events.request.add_listener
def _ghi(request_type, name, response_time, response_length, exception, **kw):
    NHAT_KY.append((time.time(), name, response_time, exception is not None))


def _p95(cac_ms):
    if not cac_ms:
        return 0.0
    cac_ms = sorted(cac_ms)
    return cac_ms[min(len(cac_ms) - 1, int(round(0.95 * len(cac_ms) + 0.5)) - 1)]


def _nhom(ten):
    return ten.split(":", 1)[0] if ":" in ten else ""


@events.quitting.add_listener
def _tu_cham(environment, **kw):
    """AC-10.6: chấm từng nhóm theo ngưỡng, kể cả p95 người khác trong lúc Manager tính lại cột."""
    stats = environment.stats
    tong = stats.total
    dong_bang = ["| Yêu cầu | Số lần | Hỏng | p50 | p95 | p99 | Lớn nhất | RPS |", "|---|--:|--:|--:|--:|--:|--:|--:|"]
    for e in sorted(stats.entries.values(), key=lambda e: e.name):
        dong_bang.append(
            f"| {e.name} | {e.num_requests} | {e.num_failures} | {e.get_response_time_percentile(0.5) or 0:.0f} "
            f"| {e.get_response_time_percentile(0.95) or 0:.0f} | {e.get_response_time_percentile(0.99) or 0:.0f} "
            f"| {e.max_response_time:.0f} | {e.total_rps:.1f} |"
        )

    cham = []            # (tên, giá trị, ngưỡng, đạt)
    for nhom, nguong in NGUONG.items():
        ms = [m for _, ten, m, hong in NHAT_KY if _nhom(ten) == nhom and not hong]
        if ms:
            p95 = _p95(ms)
            cham.append((f"p95 nhóm {nhom} ({len(ms)} lượt)", f"{p95:.0f} ms", f"≤ {nguong} ms", p95 <= nguong))
    cham.append(("Yêu cầu hỏng", str(tong.num_failures), "= 0", tong.num_failures == 0))
    cham.append(("Lượt bị từ chối vì dòng vừa bị người khác xoá (tranh chấp, không tính lỗi)", str(TRANH_CHAP[0]), "ghi nhận", True))
    for bang, t1, t2, ms, hong in CUA_SO_TINH_LAI:
        lon = bang == VAN_DON
        nguong_s = PERF_RECOMPUTE_SECONDS
        cham.append((f"Tính lại cột tính sẵn `{bang}`", f"{ms / 1000:.1f} s" + (" (hỏng)" if hong else ""),
                     f"≤ {nguong_s} s" if lon else "ghi nhận", (not hong and ms <= nguong_s * 1000) if lon else not hong))
        khac = [m for t, ten, m, h in NHAT_KY if t1 <= t <= t2 and _nhom(ten) == DOC and not h]
        if khac:
            p95 = _p95(khac)
            cham.append((f"… p95 nhóm đọc của người khác trong {t2 - t1:.0f} s đó ({len(khac)} lượt)",
                         f"{p95:.0f} ms", f"≤ {PERF_READ_P95_MS} ms", p95 <= PERF_READ_P95_MS))
    if not CUA_SO_TINH_LAI:
        cham.append(("Tính lại cột tính sẵn", "chưa chạy (phiên ngắn hơn MANAGER_DELAY?)", "phải có", False))

    dat_het = all(d for _, _, _, d in cham)
    print(f"\n== AC-10.6: {tong.num_requests} yêu cầu, {tong.total_rps:.1f} RPS, "
          f"p95 chung = {tong.get_response_time_percentile(0.95) or 0:.0f} ms, hỏng = {tong.num_failures}")
    for ten, gia_tri, nguong, d in cham:
        print(f"  {'ĐẠT      ' if d else 'KHÔNG ĐẠT'}  {ten}: {gia_tri} (ngưỡng {nguong})")
    print("ĐẠT" if dat_het else "KHÔNG ĐẠT")
    environment.process_exit_code = 0 if dat_het else 1

    # Báo cáo
    try:
        PERF_DIR.mkdir(parents=True, exist_ok=True)
        opts = environment.parsed_options
        so_nguoi = getattr(opts, "num_users", None) or "?"
        thoi_luong = getattr(opts, "run_time", None) or "?"
        tep = PERF_DIR / f"{date.today().isoformat()}-tai-{so_nguoi}.md"
        noi_dung = [
            f"# Kiểm tải KN CRM — {date.today().isoformat()}, {so_nguoi} người, {thoi_luong}",
            "",
            f"Máy chủ `{environment.host}`, ERP `{ERP_HOST}`, kịch bản `tests/perf/locustfile_kn_crm.py`, "
            f"Manager đổi cột sau {MANAGER_DELAY} s. Kết quả chung: **{'ĐẠT' if dat_het else 'KHÔNG ĐẠT'}**.",
            "",
            f"Tổng {tong.num_requests} yêu cầu, {tong.total_rps:.1f} RPS, p50 {tong.get_response_time_percentile(0.5) or 0:.0f} ms, "
            f"p95 {tong.get_response_time_percentile(0.95) or 0:.0f} ms, p99 {tong.get_response_time_percentile(0.99) or 0:.0f} ms, "
            f"hỏng {tong.num_failures}.",
            "", "## Chấm theo ngưỡng (core/constants.py)", "",
            "| Tiêu chí | Đo được | Ngưỡng | Kết quả |", "|---|--:|--:|---|",
            *[f"| {ten} | {gia_tri} | {nguong} | {'ĐẠT' if d else '**KHÔNG ĐẠT**'} |" for ten, gia_tri, nguong, d in cham],
            "", "## Từng yêu cầu (ms)", "", *dong_bang, "",
        ]
        if stats.errors:
            noi_dung += ["## Lỗi", "", "| Yêu cầu | Lỗi | Số lần |", "|---|---|--:|",
                         *[f"| {e.name} | {str(e.error)[:160]} | {e.occurrences} |" for e in stats.errors.values()], ""]
        tep.write_text("\n".join(noi_dung), encoding="utf-8")
        print(f"Đã ghi {tep}")
    except OSError as loi:
        print(f"Không ghi được báo cáo: {loi}", file=sys.stderr)
