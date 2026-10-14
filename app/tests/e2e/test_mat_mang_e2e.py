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


def test_loi_bao_chua_luu_khong_bi_yeu_cau_khac_xoa(live_server, trang, dang_nhap, kn_crm, setup, nguoi_dung):  # noqa: F811
    """AC-10.12 — Lên đơn: bấm Lưu đơn lúc mất mạng thì lời báo "Mất kết nối mạng…" còn nguyên dù một yêu cầu khác của
    trang (tra khách theo số điện thoại) thành công ngay sau đó — trước đây yêu cầu tra khách xong là lời báo biến mất,
    người dùng tưởng đơn đã lưu (bài trên đỏ chập chờn 2/5 lần vì đúng cuộc đua này); Lưu đơn thành công thì lời báo tắt"""
    dang_nhap(trang, nguoi_dung["staff_sale_1"])
    trang.goto(f"{live_server.url}/van-don/len-don/")
    f = trang.locator("form:has([name=customer_name])")
    f.locator("[name=customer_name]").fill("Khách Mất Mạng")
    f.locator("[name=market]").select_option("us")
    f.locator("[name=payment_method]").select_option(index=1)
    f.locator("[name=product]").first.select_option(setup[2][0].code)
    f.locator("[name=quantity]").first.fill("1")
    f.locator("[name=unit_price]").first.fill("10")
    f.locator("[name=phone]").fill("0901000222")
    # Lần tra khách theo tên (chạy khi rời ô tên) xong lúc còn mạng. Tra theo số chỉ chạy khi rời ô số, tức lúc bấm nút
    # đã mất mạng: nó hỏng cùng lần Lưu đơn, thứ tự hai lỗi không cố định — bài dưới ép thứ tự xấu (TL-100)
    trang.wait_for_timeout(1_000)
    trang.context.set_offline(True)
    f.locator("button[type=submit]").click()
    bao = trang.locator(".loi-mang-noi")
    bao.wait_for(timeout=8_000)
    trang.context.set_offline(False)
    # Một yêu cầu khác của trang thành công: tra khách theo số vừa sửa
    with trang.expect_response(lambda r: "kiem-khach" in r.url and r.ok, timeout=8_000):
        f.locator("[name=phone]").fill("0901000333")
        f.locator("[name=phone]").dispatch_event("change")
    trang.wait_for_timeout(300)
    assert bao.is_visible(), "lời báo chưa lưu biến mất sau khi tra khách xong"
    assert not Order.objects.exists()
    f.locator("button[type=submit]").click()
    assert _cho_db(trang, lambda: Order.objects.count() == 1)
    trang.locator(".loi-mang-noi").wait_for(state="detached", timeout=8_000)


# Ghi thứ tự các yêu cầu HTMX gửi hỏng: "form" là Lưu đơn, tên ô (phone…) là tra khách chạy ngầm
_GHI_LOI_GUI = """
window.__loiGui = [];
document.addEventListener('htmx:sendError', function (e) {
  var el = e.detail && e.detail.elt;
  window.__loiGui.push(!el ? '?' : el.tagName === 'FORM' ? 'form' : (el.name || el.tagName));
});
"""


def test_loi_bao_con_khi_tra_khach_hong_sau_luu_don(live_server, trang, dang_nhap, kn_crm, setup, nguoi_dung):  # noqa: F811
    """AC-10.12 — Lên đơn: lần tra khách hỏng tới SAU lần Lưu đơn hỏng (thứ tự máy CI chậm gặp ngày 14.10.2026, TL-100)
    thì lần tra khách thành công kế tiếp vẫn không xoá lời báo "Mất kết nối mạng…", vì đơn chưa lưu; Lưu đơn thành công
    thì lời báo tắt và ra đúng một đơn"""
    trang.add_init_script(_GHI_LOI_GUI)
    dang_nhap(trang, nguoi_dung["staff_sale_1"])
    trang.goto(f"{live_server.url}/van-don/len-don/")
    f = trang.locator("form:has([name=customer_name])")
    f.locator("[name=customer_name]").fill("Khách Đua Mạng")
    f.locator("[name=market]").select_option("us")
    f.locator("[name=payment_method]").select_option(index=1)
    f.locator("[name=product]").first.select_option(setup[2][0].code)
    f.locator("[name=quantity]").first.fill("1")
    f.locator("[name=unit_price]").first.fill("10")
    f.locator("[name=phone]").fill("0901000444")
    trang.wait_for_load_state("networkidle")
    trang.context.set_offline(True)
    f.locator("button[type=submit]").click()
    trang.wait_for_function("() => window.__loiGui.includes('form')", timeout=8_000)
    # Còn mất mạng: tra khách thêm một lần, hỏng tới sau lần Lưu đơn
    f.locator("[name=phone]").dispatch_event("change")
    trang.wait_for_function(
        "() => window.__loiGui.lastIndexOf('phone') > window.__loiGui.lastIndexOf('form')", timeout=8_000)
    bao = trang.locator(".loi-mang-noi")
    assert bao.is_visible()
    trang.context.set_offline(False)
    with trang.expect_response(lambda r: "kiem-khach" in r.url and r.ok, timeout=8_000):
        f.locator("[name=phone]").fill("0901000555")
        f.locator("[name=phone]").dispatch_event("change")
    trang.wait_for_timeout(300)
    assert bao.is_visible(), f"lời báo chưa lưu biến mất sau khi tra khách xong (thứ tự lỗi: {trang.evaluate('window.__loiGui')})"
    assert not Order.objects.exists()
    f.locator("button[type=submit]").click()
    assert _cho_db(trang, lambda: Order.objects.count() == 1)
    trang.locator(".loi-mang-noi").wait_for(state="detached", timeout=8_000)
    trang.wait_for_timeout(1_000)
    assert Order.objects.count() == 1
