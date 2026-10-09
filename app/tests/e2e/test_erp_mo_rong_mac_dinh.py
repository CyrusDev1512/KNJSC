"""ERP mở lên ở chế độ mở rộng, không nền ảnh — AC-10.17 (chủ dự án 07.10.2026).

Trước đây nút "Mở rộng giao diện ERP" mặc định tắt: lần đầu mở ERP là khung bo góc trên ảnh nền. Chủ dự án muốn ngược
lại: mặc định mở rộng (không nền ảnh, không viền, không lề); ai thích nền thì bấm nút, máy đó nhớ lựa chọn. Vẫn chỉ là bố
cục trong tab, không bật Fullscreen API (trình duyệt không cho tự bật khi chưa có thao tác của người dùng).
"""
import pytest

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]

MO_RONG = "() => document.documentElement.classList.contains('sp-erp-immersive')"
NEN = "() => getComputedStyle(document.body, '::before').content"


def test_erp_mac_dinh_mo_rong_khong_nen_va_nho_lua_chon(live_server, trang, dang_nhap, nguoi_dung):
    """AC-10.17 — Máy chưa từng chọn: mở ERP là chế độ mở rộng, không ảnh nền, nút ở trạng thái bật, không Fullscreen API;
    bấm nút thì hiện nền và tải lại vẫn có nền; bấm lần nữa thì về mở rộng; trang đăng nhập không đổi"""
    trang.goto(live_server.url + "/dang-nhap/")
    assert not trang.evaluate(MO_RONG), "trang đăng nhập không dùng khung ERP"
    dang_nhap(trang, nguoi_dung["staff_sale_1"])
    assert trang.evaluate("() => localStorage.getItem('knjsc-erp-immersive')") is None
    assert trang.evaluate(MO_RONG)
    assert trang.evaluate(NEN) == "none"
    nut = trang.locator("#sp-erp-fullscreen")
    assert nut.get_attribute("aria-pressed") == "true"
    assert not trang.evaluate("() => Boolean(document.fullscreenElement)")

    nut.click()
    assert not trang.evaluate(MO_RONG) and trang.evaluate(NEN) != "none"
    trang.reload()
    assert not trang.evaluate(MO_RONG), "tắt mở rộng phải được nhớ"
    assert trang.locator("#sp-erp-fullscreen").get_attribute("aria-pressed") == "false"

    trang.locator("#sp-erp-fullscreen").click()
    trang.reload()
    assert trang.evaluate(MO_RONG)
