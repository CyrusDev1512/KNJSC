"""Kịch bản đo tải — AC-10.1, NFR-2, backlog Q44 (Locust, chỉ dùng khi kiểm thử).

Ba vai chạy song song đúng như một ngày làm việc:

- Sale        lên đơn (POST) và xem danh sách đơn
- Vận đơn     mở Bảng tính, lọc theo trạng thái, sửa một ô
- Marketing   nộp báo cáo ngày, mở báo cáo tổng hợp

Chạy trên máy đã có `du_lieu_mau` (tài khoản) và nên có `seed_perf` (50.000
dòng vận đơn) để đo đúng cỡ thật:

    locust -f tests/perf/locustfile.py --host http://localhost:8020 \\
           --users 50 --spawn-rate 5 --run-time 1m --headless

**Tự chấm:** khi dừng, kịch bản tính p99 của mọi yêu cầu; quá 3 giây thì thoát
mã 1 — đúng câu chữ của AC-10.1 *"không có yêu cầu nào quá 3 giây"*.

Bảng tính chạy ở dịch vụ riêng: đặt `BANGTINH_HOST` (mặc định
`http://localhost:8021`) để vai Vận đơn gọi đúng chỗ.
"""
import os
import random
import re

from locust import HttpUser, between, events, task

MAT_KHAU = os.environ.get("KNJSC_MAT_KHAU", "MatKhauTam-2026")
BANGTINH_HOST = os.environ.get("BANGTINH_HOST", "http://localhost:8021")
NGUONG_P99_MS = 3000
TRANG_THAI = ["Đã lên đơn", "Đang giao", "Đã nhận hàng", "Hẹn lại"]


def _csrf(client, duong_dan):
    kq = client.get(duong_dan, name=duong_dan)
    m = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', kq.text)
    return m.group(1) if m else client.cookies.get("csrftoken", "")


def _dang_nhap(client, ten):
    token = _csrf(client, "/dang-nhap/")
    client.post("/dang-nhap/", {"username": ten, "password": MAT_KHAU, "csrfmiddlewaretoken": token},
                headers={"Referer": client.base_url + "/dang-nhap/"}, name="/dang-nhap/")


class NguoiSale(HttpUser):
    weight = 4
    wait_time = between(2, 6)

    def on_start(self):
        _dang_nhap(self.client, "sale.staff")

    @task(3)
    def xem_don(self):
        self.client.get("/don-hang/", name="/don-hang/")

    @task(1)
    def len_don(self):
        token = _csrf(self.client, "/len-don/")
        so = random.randrange(10_000_000, 99_999_999)
        self.client.post("/len-don/", {
            "csrfmiddlewaretoken": token,
            "phone": f"09{so}", "customer_name": f"Khách tải {so}",
            "market": "ca", "state": "AB", "city": "Calgary", "zipcode": "T1Y1J1",
            "address_line": "12 Main St", "payment_method": "transfer", "currency": "CAD",
            "line_product": ["retinol-cream"], "line_quantity": ["2"], "line_price": ["120.00"],
        }, headers={"Referer": self.client.base_url + "/len-don/"}, name="/len-don/ [POST]")


class NguoiVanDon(HttpUser):
    weight = 4
    wait_time = between(1, 4)
    host = BANGTINH_HOST

    def on_start(self):
        _dang_nhap(self.client, "vd.staff")
        self.o = []

    @task(4)
    def mo_luoi(self):
        trang_thai = random.choice(TRANG_THAI)
        kq = self.client.get(f"/bang-tinh/?f_trang_thai_vc__trong={trang_thai}", name="/bang-tinh/?loc")
        self.o = re.findall(r'data-sua-url="([^"]+)"', kq.text)[:50]

    @task(2)
    def hop_loc(self):
        self.client.get("/bang-tinh/loc/trang_thai_vc/", name="/bang-tinh/loc/<cot>/")

    @task(1)
    def sua_o(self):
        if not self.o:
            return
        duong = random.choice([u for u in self.o if u.endswith("/trang_thai_vc/")] or self.o)
        token = self.client.cookies.get("csrftoken", "")
        self.client.post(duong, {"gia_tri": random.choice(TRANG_THAI), "csrfmiddlewaretoken": token},
                         headers={"Referer": self.client.base_url + "/bang-tinh/", "X-CSRFToken": token},
                         name="/bang-tinh/o/<pk>/<cot>/ [POST]")


class NguoiMarketing(HttpUser):
    weight = 2
    wait_time = between(3, 8)

    def on_start(self):
        _dang_nhap(self.client, "mkt.staff")

    @task(2)
    def bao_cao_ngay(self):
        self.client.get("/bao-cao-ngay/", name="/bao-cao-ngay/")

    @task(1)
    def tong_hop(self):
        self.client.get("/bao-cao-tong-hop/?nhom=ngay", name="/bao-cao-tong-hop/")


@events.quitting.add_listener
def _tu_cham(environment, **kw):
    """AC-10.1: p99 mọi yêu cầu không quá 3 giây, và không yêu cầu nào hỏng."""
    tong = environment.stats.total
    p99 = tong.get_response_time_percentile(0.99) or 0
    print(f"\n== AC-10.1: {tong.num_requests} yêu cầu, p99 = {p99:.0f} ms, hỏng = {tong.num_failures}")
    if p99 > NGUONG_P99_MS or tong.num_failures:
        print("KHÔNG ĐẠT — p99 quá 3 giây hoặc có yêu cầu hỏng")
        environment.process_exit_code = 1
    else:
        print("ĐẠT")
        environment.process_exit_code = 0
