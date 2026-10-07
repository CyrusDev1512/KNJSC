"""Chuyển trang ở danh sách ERP không tải lại cả trang — AC-10.19 (chủ dự án 07.10.2026).

Thanh phân trang dùng chung trước đây là liên kết thường: mỗi lần bấm trang 2 hay đổi "Mỗi trang" là tải lại cả trang
(trang trắng, menu và bộ lọc vẽ lại). Nay `phan-trang.js` chỉ thay vùng danh sách, URL đổi theo, Back quay về trang
trước cũng tại chỗ.
"""
import pytest

from core.constants import Rank

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]


def test_nhan_su_chuyen_trang_tai_cho_giu_bo_loc(live_server, trang, dang_nhap, nguoi_dung, departments, make_user):
    """AC-10.19 — Nhân sự lọc "Nhân viên": bấm trang 2 thì chỉ vùng danh sách đổi (trang không tải lại: biến JS đặt trước
    vẫn còn), URL có `trang=2` và giữ `cap_bac`; ô lọc vẫn chọn đúng; đổi "Mỗi trang" thành 50 cũng tại chỗ, về trang 1;
    Back trả lại trang trước tại chỗ; không lỗi JS"""
    for i in range(30):
        make_user(f"nv_tr_{i:02d}", Rank.STAFF, departments["sale"])
    loi_js = []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(trang, nguoi_dung["admin"])
    trang.goto(live_server.url + "/nhan-su/?cap_bac=staff")
    trang.evaluate("() => { window.__chuaTaiLai = 1; }")
    dong_dau = trang.locator("[data-vung-trang=ds] tbody tr").first.inner_text()

    trang.locator("[data-vung-trang=ds] .phan-trang a", has_text="2").first.click()
    trang.wait_for_function("() => location.search.includes('trang=2')")
    trang.wait_for_function("(cu) => document.querySelector('[data-vung-trang=ds] tbody tr').innerText !== cu", arg=dong_dau)
    assert trang.evaluate("() => window.__chuaTaiLai") == 1, "trang bị tải lại"
    assert "cap_bac=staff" in trang.url
    assert trang.locator("select[name=cap_bac]").input_value() == "staff"

    trang.locator("[data-vung-trang=ds] .phan-trang select").select_option("50")
    trang.wait_for_function("() => location.search.includes('moi_trang=50') && !location.search.includes('trang=2')")
    trang.wait_for_function("() => document.querySelectorAll('[data-vung-trang=ds] tbody tr').length > 25")
    assert trang.evaluate("() => window.__chuaTaiLai") == 1

    trang.go_back()
    trang.wait_for_function("() => location.search.includes('trang=2')")
    trang.wait_for_function("() => document.querySelectorAll('[data-vung-trang=ds] tbody tr').length <= 25")
    assert trang.evaluate("() => window.__chuaTaiLai") == 1
    assert not loi_js, loi_js
