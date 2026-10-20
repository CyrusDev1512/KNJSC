"""Lưới tiền không nhân nghìn khi hoàn tác, chép dán — TL-03 · P0-3 (ADR-052), trình duyệt thật ở KN CRM.

Số tiền lưu dạng chuỗi máy "0.125". Trước đây ô sửa hiện nguyên "0.125", Ctrl+Z gửi lại "0.125" như chữ người gõ,
chép một ô rồi dán cũng vậy — máy chủ đọc theo luật Việt (chấm ngăn nghìn) thành 125.
"""
from decimal import Decimal

import pytest

from crm.tests.test_bang_tinh_luu_o import _dong, bang_sale  # noqa: F401 — fixture bảng có cột Tiền sửa được
from forms_builder.models import DataRecord

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]

#: Bắt nội dung Ctrl+C: Chromium không đầu không cho đọc bộ nhớ tạm thật
CHEP = """(() => {
  window.__chep = null;
  navigator.clipboard.write = async items => { for (const it of items) window.__chep = await (await it.getType('text/plain')).text(); };
  navigator.clipboard.writeText = async t => { window.__chep = t; };
})();"""


@pytest.fixture
def kn_crm(settings):
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.BANGTINH_URL = ""
    settings.GRID_ONLY_TABLES = set()
    return settings


def _o(pk):
    return f".mg-cell[data-code='doanh_thu'][data-id='{pk}']"


def _tien(pk):
    return DataRecord.objects.get(pk=pk).data.get("doanh_thu")


def _luu(trang):
    return trang.expect_response(lambda r: "/luu-json/" in r.url and r.request.method == "POST", timeout=20_000)


def _dan(trang, chu):
    trang.evaluate("""t => { const dt = new DataTransfer(); dt.setData('text/plain', t);
        document.getElementById('mg-viewport').dispatchEvent(new ClipboardEvent('paste', {bubbles: true, clipboardData: dt})); }""",
                   chu)


def test_hoan_tac_dan_tu_luoi_va_o_sua_khong_nhan_nghin(live_server, trang, dang_nhap, kn_crm, bang_sale,  # noqa: F811
                                                       nguoi_dung):
    """AC-9.7 — Ô sửa tiền hiện "0,125" và Enter không sửa thì không gửi gì; sửa rồi Ctrl+Z trả đúng 0,125; chép ô
    tiền ra "0,125" và dán vào ô khác giữ 0,125; dán chữ ngoài "1.234" vẫn theo luật Việt là 1234; không lỗi JS (TL-03)"""
    nv = nguoi_dung["staff_sale_1"]
    d1 = _dong(bang_sale, nv, khach="A", doanh_thu=Decimal("0.125"))     # số thật, lưu chuỗi máy "0.125"
    d2 = _dong(bang_sale, nv, khach="B", doanh_thu="7")
    loi_js, luu = [], []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    trang.on("request", lambda r: luu.append(r.url) if "/luu-json/" in r.url else None)
    trang.add_init_script(script=CHEP)
    dang_nhap(trang, nv)
    trang.goto(f"{live_server.url}/bang-tinh/{bang_sale.code}/")
    trang.wait_for_selector(_o(d1.pk))

    # (1) Ô sửa hiện kiểu Việt; Enter không sửa thì không có lượt lưu nào
    trang.dblclick(_o(d1.pk))
    o_nhap = trang.locator("#mg-input input")
    assert o_nhap.input_value() == "0,125"
    trang.keyboard.press("Enter")
    trang.wait_for_timeout(2_500)
    assert luu == [] and _tien(d1.pk) == "0.125"

    # (2) Sửa thành 5 rồi Ctrl+Z: trả đúng 0,125
    trang.dblclick(_o(d1.pk))
    o_nhap.fill("5")
    with _luu(trang):
        trang.keyboard.press("Enter")
    assert _tien(d1.pk) == "5"
    trang.click(_o(d1.pk))
    with _luu(trang):
        trang.keyboard.press("Control+z")
    assert _tien(d1.pk) == "0.125"

    # (3) Chép ô tiền rồi dán vào dòng khác
    trang.click(_o(d1.pk))
    trang.keyboard.press("Control+c")
    trang.wait_for_function("() => window.__chep !== null")
    chep = trang.evaluate("() => window.__chep")
    assert chep == "0,125"
    trang.click(_o(d2.pk))
    with _luu(trang):
        _dan(trang, chep)
    assert _tien(d2.pk) == "0.125"

    # (4) Chữ dán từ ngoài vẫn là chữ người gõ: luật Việt
    trang.click(_o(d2.pk))
    with _luu(trang):
        _dan(trang, "1.234")
    assert _tien(d2.pk) == "1234"
    assert not loi_js, loi_js
