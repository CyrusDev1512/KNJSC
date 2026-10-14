"""Tóm tắt Lên đơn không tính được thì nói rõ vì sao — AC-6.14 (chủ dự án 10.10.2026; câu chữ theo ADR-053, 14.10.2026).

Trước đây mọi trường hợp chỉ ra một câu "Không tải được tóm tắt. Kiểm tra kết nối hoặc đăng nhập lại.", nên người
dùng không biết là hết phiên, vừa đổi tài khoản ở tab khác, máy chủ lỗi hay mất mạng. Từ ADR-053 trang do tài khoản khác
mở nhận 409 `nguoi_dung_doi`, mã bảo mật lệch nhận 403 JSON `code: csrf` — mỗi ca một lời, không bảo tải lại trang.
"""
import json

import pytest

from core.middleware import NGUOI_DUNG_DOI, PHIEN_CSRF

from crm.tests.test_waybill_new import setup  # noqa: F401  (fixture dùng lại)
from tests.e2e.test_mat_mang_e2e import kn_crm  # noqa: F401  (fixture dùng lại)

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet]

TOM_TAT = "**/van-don/len-don/tom-tat/"


def _cho_tom_tat(trang, chu):
    trang.wait_for_function(
        "chu => document.querySelector('[data-order-summary]').textContent.includes(chu)", arg=chu, timeout=8_000)
    return trang.locator("[data-order-summary]").text_content()


def test_tom_tat_bao_ro_tung_truong_hop(live_server, trang, dang_nhap, kn_crm, setup, nguoi_dung):  # noqa: F811
    """AC-6.14 — Tóm tắt Lên đơn không tính được thì nói rõ vì sao: máy chủ trả 403 (tài khoản không lên đơn được),
    trang do tài khoản khác mở (409), mã bảo mật lệch (403 code csrf), máy chủ lỗi, mất mạng, hết phiên (bị chuyển về
    trang đăng nhập) — mỗi trường hợp một lời, không bảo tải lại trang; tính được thì vẫn ra số dòng, số sản phẩm, tổng
    tiền; không lỗi JS"""
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
    trang.route(TOM_TAT, lambda r: r.fulfill(status=409, content_type="application/json",
                                             body=json.dumps({"error": NGUOI_DUNG_DOI, "code": "nguoi_dung_doi"})))
    go_lai("15")
    assert "Tài khoản vừa đăng nhập khác người mở trang" in _cho_tom_tat(trang, "Tài khoản vừa đăng nhập khác")

    trang.unroute(TOM_TAT)
    trang.route(TOM_TAT, lambda r: r.fulfill(status=403, content_type="application/json",
                                             body=json.dumps({"error": PHIEN_CSRF, "code": "csrf"})))
    go_lai("16")
    assert "Mã bảo mật" in _cho_tom_tat(trang, "Mã bảo mật")

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
    assert "tải lại trang" not in trang.locator("[data-order-summary]").text_content()
    assert not loi_js, loi_js
