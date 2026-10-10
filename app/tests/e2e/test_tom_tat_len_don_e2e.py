"""Tóm tắt Lên đơn không tính được thì nói rõ vì sao — AC-6.14 (chủ dự án 10.10.2026).

Trước đây mọi trường hợp chỉ ra một câu "Không tải được tóm tắt. Kiểm tra kết nối hoặc đăng nhập lại.", nên người
dùng không biết là hết phiên, vừa đổi tài khoản ở tab khác, máy chủ lỗi hay mất mạng.
"""
import pytest

from crm.tests.test_waybill_new import setup  # noqa: F401  (fixture dùng lại)
from tests.e2e.test_mat_mang_e2e import kn_crm  # noqa: F401  (fixture dùng lại)

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet]

TOM_TAT = "**/van-don/len-don/tom-tat/"


def _cho_tom_tat(trang, chu):
    trang.wait_for_function(
        "chu => document.querySelector('[data-order-summary]').textContent.includes(chu)", arg=chu, timeout=8_000)
    return trang.locator("[data-order-summary]").text_content()


def test_tom_tat_bao_ro_tung_truong_hop(live_server, trang, dang_nhap, kn_crm, setup, nguoi_dung):  # noqa: F811
    """AC-6.14 — Tóm tắt Lên đơn không tính được thì nói rõ vì sao: máy chủ trả 403 (tài khoản không lên đơn được hay
    vừa đăng nhập lại ở tab khác), máy chủ lỗi, mất mạng, hết phiên (bị chuyển về trang đăng nhập) — mỗi trường hợp
    một lời; tính được thì vẫn ra số dòng, số sản phẩm, tổng tiền; không lỗi JS"""
    loi_js = []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(trang, nguoi_dung["staff_sale_1"])
    trang.goto(f"{live_server.url}/van-don/len-don/")
    f = trang.locator("form[data-order-preview]")
    f.locator("[name=market]").select_option("us")
    f.locator("[name=product]").first.select_option(setup[2][0].code)
    f.locator("[name=unit_price]").first.fill("10")
    assert "1 dòng · 1 sản phẩm" in _cho_tom_tat(trang, "1 dòng")

    def go_lai(gia):
        f.locator("[name=unit_price]").first.fill(gia)

    trang.route(TOM_TAT, lambda r: r.fulfill(status=403, content_type="text/html", body="<h1>403</h1>"))
    go_lai("11")
    assert "không lên đơn được" in _cho_tom_tat(trang, "không lên đơn được")

    trang.unroute(TOM_TAT)
    trang.route(TOM_TAT, lambda r: r.fulfill(status=500, content_type="text/html", body="<h1>500</h1>"))
    go_lai("12")
    assert "Máy chủ đang lỗi" in _cho_tom_tat(trang, "Máy chủ đang lỗi")

    trang.unroute(TOM_TAT)
    trang.route(TOM_TAT, lambda r: r.abort("internetdisconnected"))
    go_lai("13")
    assert "Mất kết nối mạng" in _cho_tom_tat(trang, "Mất kết nối mạng")

    trang.unroute(TOM_TAT)
    trang.context.clear_cookies(name="sessionid")
    go_lai("14")
    assert "Phiên đăng nhập đã hết" in _cho_tom_tat(trang, "Phiên đăng nhập đã hết")
    assert not loi_js, loi_js
