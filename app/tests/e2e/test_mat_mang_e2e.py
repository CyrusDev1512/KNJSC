"""Mất mạng giữa chừng: người dùng biết rõ là chưa lưu, có mạng lại thì lưu đúng một lần — AC-10.12 (săn lỗi 06.10.2026).

Đo trên hệ thống thật: lưới Vận đơn mất mạng lúc tự lưu thì báo "Failed to fetch" (chữ Anh thô của trình duyệt), còn
Lên đơn bấm Lưu khi mất mạng thì **không báo gì** về việc lưu (HTMX gửi hỏng là im lặng ở mọi trang). Nay một script
dùng chung (`static/js/loi-mang.js`, nạp đầu tiên ở cả bốn khung trang) đổi lỗi mạng của `fetch` thành lời tiếng
Việt, và báo khi yêu cầu HTMX không gửi được hay máy chủ lỗi 5xx.
"""
import time

import pytest

from crm.tests.test_waybill_new import order, setup  # noqa: F401  (fixture dùng lại)
from orders.models import Order

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]


@pytest.fixture
def kn_crm(settings):
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.BANGTINH_URL = ""
    return settings


def _cho_db(trang, dat, han=10.0):
    het = time.monotonic() + han
    while not dat() and time.monotonic() < het:
        trang.wait_for_timeout(200)
    return dat()


def test_luoi_mat_mang_bao_tieng_viet_roi_tu_luu(live_server, trang, dang_nhap, kn_crm, setup, nguoi_dung):  # noqa: F811
    """AC-10.12 — Lưới Vận đơn: sửa ô lúc mất mạng thì thanh trạng thái "Lỗi lưu" và lời báo tiếng Việt "Mất kết nối mạng…" (không còn "Failed to fetch"), ô vẫn giữ chữ vừa gõ; có mạng lại thì tự lưu đúng giá trị, trạng thái "Đã lưu"; không lỗi JS"""
    dong = order(setup, nguoi_dung["staff_sale_1"]).record
    loi_js = []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(trang, nguoi_dung["staff_vd"])
    trang.goto(f"{live_server.url}/bang-tinh/van_don/")
    o = f".mg-cell[data-code='ten_khach'][data-id='{dong.pk}']"
    trang.wait_for_selector(o)
    trang.click(o)
    trang.keyboard.type("Khách Mất Mạng")
    trang.context.set_offline(True)
    trang.keyboard.press("Enter")
    trang.wait_for_function("() => document.getElementById('bt-trang-thai').textContent === 'Lỗi lưu'", timeout=8_000)
    tin = trang.locator("#mg-message").text_content()
    assert "Failed to fetch" not in tin and "Mất kết nối mạng" in tin, tin
    trang.context.set_offline(False)
    assert _cho_db(trang, lambda: (dong.refresh_from_db() or dong.data.get("ten_khach")) == "Khách Mất Mạng")
    trang.wait_for_function("() => document.getElementById('bt-trang-thai').textContent === 'Đã lưu'", timeout=8_000)
    assert not loi_js, loi_js


def test_len_don_mat_mang_bao_chua_luu_roi_luu_mot_don(live_server, trang, dang_nhap, kn_crm, setup, nguoi_dung):  # noqa: F811
    """AC-10.12 — Lên đơn: bấm Lưu đơn lúc mất mạng thì hiện lời báo "Mất kết nối mạng…" (trước đây im lặng), dữ liệu đã điền còn nguyên; có mạng lại bấm Lưu đơn thì ra đúng một đơn"""
    dang_nhap(trang, nguoi_dung["staff_sale_1"])
    trang.goto(f"{live_server.url}/van-don/len-don/")
    f = trang.locator("form:has([name=customer_name])")
    f.locator("[name=customer_name]").fill("Khách Mất Mạng")
    f.locator("[name=phone]").fill("0901000111")
    f.locator("[name=market]").select_option("us")
    f.locator("[name=payment_method]").select_option(index=1)
    f.locator("[name=product]").first.select_option(setup[2][0].code)
    f.locator("[name=quantity]").first.fill("1")
    f.locator("[name=unit_price]").first.fill("10")
    trang.context.set_offline(True)
    f.locator("button[type=submit]").click()
    bao = trang.locator(".loi-mang-noi")
    bao.wait_for(timeout=8_000)
    assert "Mất kết nối mạng" in bao.text_content()
    assert f.locator("[name=customer_name]").input_value() == "Khách Mất Mạng"
    assert not Order.objects.exists()
    trang.context.set_offline(False)
    f.locator("button[type=submit]").click()
    assert _cho_db(trang, lambda: Order.objects.count() == 1)
    trang.wait_for_timeout(1_000)
    assert Order.objects.count() == 1
