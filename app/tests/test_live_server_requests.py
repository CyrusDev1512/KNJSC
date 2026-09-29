"""TL-67 — Máy chủ thử phải xử lý xong mọi yêu cầu rồi pytest mới dọn bảng.

Bài trình duyệt kết thúc lúc lưới còn gọi máy chủ thì lệnh TRUNCATE dọn bảng của pytest-django kẹt khoá
với truy vấn đang chạy (CI #94, #96). Các bài dưới đây kiểm bộ đếm yêu cầu và phép chờ mà fixture tự chạy
ở `conftest.py` gốc dùng; bài trình duyệt thật chạy lặp để kiểm cả luồng (biên bản TL-67).
"""
import threading
import time

from django.core.handlers.wsgi import WSGIHandler
from django.core.signals import request_finished, request_started
from django.db import close_old_connections
from django.test.client import ClientHandler

from tests.live_server_requests import LIVE_SERVER_REQUESTS, LiveServerRequests


def _sau(giay, viec):
    hen = threading.Timer(giay, viec)
    hen.start()
    return hen


def test_may_chu_ranh_thi_chi_cho_khoang_yen():
    """TL-67 — Máy chủ không xử lý gì: chỉ chờ khoảng yên ngắn rồi cho dọn bảng."""
    dem = LiveServerRequests()
    bat_dau = time.monotonic()
    assert dem.wait_idle(quiet=0.05, timeout=2) is True
    assert time.monotonic() - bat_dau < 0.5


def test_con_yeu_cau_dang_do_thi_cho_no_xong():
    """TL-67 — Còn một yêu cầu đang xử lý (lưới vừa gọi tải lại dữ liệu): chờ tới khi nó xong."""
    dem = LiveServerRequests()
    dem.on_started(sender=WSGIHandler)
    _sau(0.3, lambda: dem.on_finished(sender=WSGIHandler))
    bat_dau = time.monotonic()
    assert dem.wait_idle(quiet=0.05, timeout=3) is True
    assert time.monotonic() - bat_dau >= 0.3
    assert dem.in_flight == 0


def test_yeu_cau_toi_trong_khoang_yen_thi_cho_ca_no():
    """TL-67 — Yêu cầu trình duyệt gửi trước khi đóng tab, tới máy chủ trong khoảng yên: chờ cả nó."""
    dem = LiveServerRequests()
    _sau(0.05, lambda: dem.on_started(sender=WSGIHandler))
    _sau(0.4, lambda: dem.on_finished(sender=WSGIHandler))
    bat_dau = time.monotonic()
    assert dem.wait_idle(quiet=0.2, timeout=3) is True
    assert time.monotonic() - bat_dau >= 0.4


def test_yeu_cau_khong_bao_gio_xong_thi_toi_han_la_thoi():
    """TL-67 — Yêu cầu treo: chờ tới hạn rồi thôi, báo chưa yên, không treo cả bộ kiểm thử."""
    dem = LiveServerRequests()
    dem.on_started(sender=WSGIHandler)
    bat_dau = time.monotonic()
    assert dem.wait_idle(quiet=0.05, timeout=0.3) is False
    assert 0.3 <= time.monotonic() - bat_dau < 1.5


def test_yeu_cau_cua_test_client_khong_tinh():
    """TL-67 — Test client chạy ngay trong luồng bài kiểm và có khi không phát request_finished (phản hồi
    luồng không ai đọc hết): không tính, để bộ đếm không bao giờ treo ở số dương."""
    dem = LiveServerRequests()
    dem.on_started(sender=ClientHandler)
    dem.on_finished(sender=None)
    assert dem.in_flight == 0


def test_bo_dem_chung_nghe_tin_hieu_that_cua_django():
    """TL-67 — Bộ đếm chung nối vào request_started/request_finished của Django (không nối thì fixture
    chờ vô ích). Gỡ tạm close_old_connections như test client của Django, để không đụng kết nối CSDL."""
    request_started.disconnect(close_old_connections)
    request_finished.disconnect(close_old_connections)
    try:
        truoc = LIVE_SERVER_REQUESTS.in_flight
        request_started.send(sender=WSGIHandler, environ={})
        try:
            assert LIVE_SERVER_REQUESTS.in_flight == truoc + 1
        finally:
            request_finished.send(sender=WSGIHandler)
        assert LIVE_SERVER_REQUESTS.in_flight == truoc
    finally:
        request_started.connect(close_old_connections)
        request_finished.connect(close_old_connections)
