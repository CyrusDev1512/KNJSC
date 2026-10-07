"""Lưới Vận đơn: panel Bộ lọc tải khi mở, đổi lọc không tải lại trang, hỏi 8 giây không kiểm quyền thừa — AC-10.20,
AC-10.22 (07.10.2026)."""
import pytest

from crm.tests.test_waybill_new import order, setup  # noqa: F401  (fixture dùng lại)
from forms_builder.services import record_service

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]


@pytest.fixture
def kn_crm(settings):
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.BANGTINH_URL = ""
    return settings


def test_panel_tai_khi_mo_va_doi_loc_chi_lay_manh(live_server, trang, dang_nhap, kn_crm, setup, nguoi_dung):
    """AC-10.20 — Mở lưới: panel Bộ lọc chưa tải (không gọi `bo-loc/`); bấm Bộ lọc thì tải panel đúng một lần, có nhóm
    Thị trường; Áp dụng một bộ lọc thì chỉ gọi mảnh `bo-loc/`, không tải lại trang lưới, chip hiện đúng; không lỗi JS"""
    order(setup, nguoi_dung["staff_sale_1"])
    loi_js, goi = [], []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    trang.on("request", lambda r: goi.append(r.url))
    dang_nhap(trang, nguoi_dung["staff_vd"])
    trang.goto(f"{live_server.url}/bang-tinh/van_don/")
    trang.wait_for_selector(".mg-cell[data-code='ma_don']")
    assert not [u for u in goi if "/bo-loc/" in u]
    trang.evaluate("() => { window.__chuaTaiLai = 1; }")
    trang.click("#mg-filters-button")
    trang.wait_for_selector("#mg-filters-body form")
    assert len([u for u in goi if "/bo-loc/" in u and "panel=1" in u]) == 1
    assert "Thị trường" in trang.locator("#mg-filters").inner_text()
    trang.click("#mg-filters-button"); trang.click("#mg-filters-button")      # đóng, mở lại: không tải lại panel
    assert len([u for u in goi if "/bo-loc/" in u and "panel=1" in u]) == 1

    truoc = len(goi)
    o = trang.locator("#mg-filters input[name=f_trang_thai_tt__trong]").first
    o.check()
    o.evaluate("o => o.form.requestSubmit()")
    trang.wait_for_function("() => location.search.includes('f_trang_thai_tt__trong')")
    trang.wait_for_function("() => document.getElementById('mg-chips').innerText.trim().length > 0")
    moi = goi[truoc:]
    assert any("/bo-loc/" in u for u in moi)
    assert not any(u.split("?")[0].endswith("/bang-tinh/van_don/") for u in moi), "tải lại trang lưới"
    assert trang.evaluate("() => window.__chuaTaiLai") == 1
    assert not loi_js, loi_js


def test_hoi_8_giay_chi_kiem_quyen_khi_moc_doi(live_server, trang, dang_nhap, kn_crm, setup, nguoi_dung):
    """AC-10.22 — Lưới mở mà không ai sửa gì: các lượt hỏi 8 giây không gửi danh sách dòng đi kiểm quyền (trước đây
    mỗi lượt một lần); có người sửa một dòng thì lượt hỏi kế tiếp kiểm quyền và tải lại phần đang xem"""
    don = order(setup, nguoi_dung["staff_sale_1"])
    goi = []
    trang.on("request", lambda r: goi.append(r.url))
    dang_nhap(trang, nguoi_dung["staff_vd"])
    trang.goto(f"{live_server.url}/bang-tinh/van_don/")
    trang.wait_for_selector(".mg-cell[data-code='ma_don']")
    trang.wait_for_timeout(8_500)                                   # lượt hỏi đầu: ghi mốc, kiểm quyền một lần
    dem = lambda: (len([u for u in goi if "/moi-nhat/" in u]), len([u for u in goi if "/quyen-dong/" in u]))
    hoi0, quyen0 = dem()
    trang.wait_for_timeout(16_500)                                  # thêm hai lượt hỏi, không ai sửa gì
    hoi1, quyen1 = dem()
    assert hoi1 - hoi0 >= 2 and quyen1 == quyen0, (hoi0, quyen0, hoi1, quyen1)

    record_service.update_cell(don.record, "ghi_chu", "người khác sửa", actor=nguoi_dung["admin"])
    trang.wait_for_timeout(8_500)
    assert dem()[1] > quyen1, "mốc đổi mà không kiểm quyền"
