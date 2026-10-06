"""Đi giữa KN ERP và KN CRM không mất đăng nhập — AC-1.10 (06.10.2026).

Máy local: hai dịch vụ chạy ở cổng 8020 và 8021, liên kết sang nhau mặc định trỏ `localhost`. Người dùng mở hệ thống
bằng `127.0.0.1:8020` (đúng địa chỉ `KN JSC.bat` mở) bấm "KN CRM" là sang `localhost:8021` — trình duyệt coi đó là
host khác, không gửi cookie phiên, nên trang đăng nhập hiện ra như thể mất quyền. Nay liên kết giữ đúng host đang mở,
chỉ đổi cổng; trên VPS (tên miền thật) liên kết giữ nguyên như cấu hình.
"""
import pytest
from django.test import Client

pytestmark = pytest.mark.django_db


def test_link_sang_crm_giu_host_dang_mo(client, nguoi_dung, settings):
    """AC-1.10 — Mở ERP bằng 127.0.0.1:8020 thì nút KN CRM trỏ 127.0.0.1:8021 (không phải localhost:8021); mở bằng localhost thì giữ localhost"""
    settings.BANGTINH_URL = "http://localhost:8021/"
    client.force_login(nguoi_dung["manager_sale"])
    html = client.get("/", HTTP_HOST="127.0.0.1:8020").content.decode()
    assert 'href="http://127.0.0.1:8021/"' in html
    assert "localhost:8021" not in html
    html = client.get("/", HTTP_HOST="localhost:8020").content.decode()
    assert 'href="http://localhost:8021/"' in html


def test_len_don_chuyen_sang_crm_cung_host(client, nguoi_dung, settings):
    """AC-1.10 — Đường dẫn Lên đơn cũ ở ERP chuyển sang CRM cùng host đang mở"""
    settings.BANGTINH_URL = "http://localhost:8021/"
    client.force_login(nguoi_dung["staff_sale_1"])
    r = client.get("/len-don/", HTTP_HOST="127.0.0.1:8020")
    assert r.status_code == 302
    assert r["Location"].startswith("http://127.0.0.1:8021/")


def test_ten_mien_that_giu_nguyen_cau_hinh(client, nguoi_dung, settings):
    """AC-1.10 — Trên VPS (tên miền thật) liên kết sang CRM đúng như cấu hình, không bị đổi theo host"""
    settings.BANGTINH_URL = "https://crm.vi-du.vn/"
    settings.ALLOWED_HOSTS = ["erp.vi-du.vn"]
    client.force_login(nguoi_dung["manager_sale"])
    html = client.get("/", HTTP_HOST="erp.vi-du.vn").content.decode()
    assert 'href="https://crm.vi-du.vn/"' in html


def test_link_tu_crm_ve_erp_giu_host_dang_mo(nguoi_dung, settings):
    """AC-1.10 — Mở CRM bằng 127.0.0.1:8021 thì nút KN ERP trỏ 127.0.0.1:8020"""
    settings.MAIN_APP_URL = "http://localhost:8020/"
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    c = Client()
    c.force_login(nguoi_dung["manager_sale"])
    html = c.get("/", HTTP_HOST="127.0.0.1:8021").content.decode()
    assert 'href="http://127.0.0.1:8020/"' in html
    assert "localhost:8020" not in html
