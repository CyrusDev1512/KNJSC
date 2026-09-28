"""Ô ngày tự chèn dấu "/" khi gõ — `docs/04` AC-32.1, chủ dự án 28.09.2026.

Mọi ô ngày ERP/CRM dùng chung `static/js/date-inputs.js` (ADR-032: nhập `DD/MM/YYYY`).
Trước đây gõ `03 09 2026` hay `03092026` bị báo sai định dạng; nay ô tự thành
`03/09/2026`. Phải kiểm bằng phím thật: việc chèn "/" chạy theo sự kiện gõ của trình duyệt.
"""
import pytest

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]

O = "#bc-tu"


def _go(trang, chu, xoa=True):
    """Xoá ô rồi gõ từng phím như người dùng; trả (chữ hiển thị, giá trị ISO, hợp lệ)."""
    o = trang.locator(O)
    o.click()
    if xoa:
        trang.keyboard.press("Control+a")
        trang.keyboard.press("Delete")
    trang.keyboard.type(chu, delay=30)
    return trang.evaluate(
        """s => { const o = document.querySelector(s);
                  return [HTMLInputElement.prototype.__lookupGetter__('value').call(o), o.value, o.validity.valid]; }""",
        O)


def test_o_ngay_tu_chen_dau_gach(live_server, trang, dang_nhap, nguoi_dung):
    """AC-32.1 — Ô ngày tự chèn "/" sau 2 số ngày và 2 số tháng; dấu cách, chấm, gạch ngang đổi
    thành "/"; gõ liền 8 số thành DD/MM/YYYY; rời ô thì thêm số 0 cho ngày tháng một chữ số;
    Backspace không bị chèn lại "/"; giá trị gửi đi vẫn là ISO"""
    loi_js = []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(trang, nguoi_dung["admin"])
    trang.goto(f"{live_server.url}/")
    trang.wait_for_selector(O)

    assert _go(trang, "03 09 2026") == ["03/09/2026", "2026-09-03", True]
    assert _go(trang, "03092026") == ["03/09/2026", "2026-09-03", True]
    assert _go(trang, "03.09.2026") == ["03/09/2026", "2026-09-03", True]
    assert _go(trang, "03-09-2026") == ["03/09/2026", "2026-09-03", True]
    assert _go(trang, "03")[0] == "03/", "đủ 2 số ngày phải tự chèn /"
    assert _go(trang, "0309")[0] == "03/09/", "đủ 2 số tháng phải tự chèn /"

    # Backspace xoá "/" vừa chèn thì giữ nguyên, không chèn lại
    _go(trang, "03")
    trang.keyboard.press("Backspace")
    assert trang.evaluate("s => HTMLInputElement.prototype.__lookupGetter__('value')"
                          ".call(document.querySelector(s))", O) == "03"

    # Ngày tháng một chữ số: rời ô thì thêm số 0
    _go(trang, "3/9/2026")
    trang.keyboard.press("Tab")
    assert trang.evaluate("s => [HTMLInputElement.prototype.__lookupGetter__('value')"
                          ".call(document.querySelector(s)), document.querySelector(s).value]", O) \
        == ["03/09/2026", "2026-09-03"]

    # Ngày sai vẫn bị báo, không tự "sửa" thành ngày khác
    assert _go(trang, "31022026")[2] is False
    assert not loi_js, loi_js
