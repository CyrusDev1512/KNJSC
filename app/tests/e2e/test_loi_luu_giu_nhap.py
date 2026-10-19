"""TL-06/19/20: lỗi không được xoá nháp hoặc báo Đã lưu, ô lỗi và trạng thái luôn đọc được."""
import re
import pytest
from playwright.sync_api import expect

from crm.tests.test_bang_tinh_luu_o import bang_sale, _dong  # noqa: F401
from crm.tests.test_waybill_new import setup, order  # noqa: F401

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet]


@pytest.fixture
def kn_crm(settings):
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.BANGTINH_URL = ""
    settings.GRID_ONLY_TABLES = set()


def test_403_roi_kiem_quyen_500_giu_nhap_de_thu_lai(live_server, trang, dang_nhap, kn_crm, bang_sale, nguoi_dung):
    """AC-11.19 — Kiểm quyền lỗi mạng không chứng minh mất quyền; còn nháp và thử lại ghi đúng giá trị."""
    row = _dong(bang_sale, nguoi_dung["staff_sale_1"], khach="Trước sửa")
    dang_nhap(trang, nguoi_dung["admin"])
    trang.goto(f"{live_server.url}/bang-tinh/{bang_sale.code}/")
    trang.route("**/luu-json/", lambda r: r.fulfill(status=403, json={"error": "Lượt ghi bị từ chối"}))
    trang.route("**/quyen-dong/", lambda r: r.fulfill(status=500, json={"error": "Tạm thời không kiểm được quyền"}))
    trang.dblclick(f".mg-cell[data-id='{row.pk}'][data-code='khach']")
    trang.locator("#mg-input input").fill("Nháp còn quyền")
    with trang.expect_response("**/quyen-dong/"):
        trang.keyboard.press("Enter")
    expect(trang.locator("#bt-trang-thai")).to_have_text("Lỗi lưu")
    expect(trang.locator("#mg-message").get_by_role("button", name="Thử lại", exact=True)).to_be_visible()
    trang.unroute("**/luu-json/"); trang.unroute("**/quyen-dong/")
    with trang.expect_response("**/luu-json/") as response:
        trang.locator("#mg-message").get_by_role("button", name="Thử lại", exact=True).click()
    assert response.value.status == 200
    row.refresh_from_db()
    assert row.data["khach"] == "Nháp còn quyền"


def test_o_sai_duoc_danh_dau_va_trang_thai_mobile(live_server, trang, dang_nhap, kn_crm, bang_sale, nguoi_dung):
    """AC-11.19 — Server chỉ ra ô sai: aria-invalid/title, tên cột dễ hiểu; điện thoại không giấu lỗi lưu."""
    row = _dong(bang_sale, nguoi_dung["staff_sale_1"], khach="Khách thử", doanh_thu="10")
    dang_nhap(trang, nguoi_dung["admin"])
    trang.goto(f"{live_server.url}/bang-tinh/{bang_sale.code}/")
    cell = trang.locator(f".mg-cell[data-id='{row.pk}'][data-code='doanh_thu']")
    cell.dblclick()
    trang.locator("#mg-input input").fill("số không hợp lệ")
    with trang.expect_response("**/luu-json/") as response:
        trang.keyboard.press("Enter")
    assert response.value.status == 400
    expect(cell).to_have_attribute("aria-invalid", "true")
    expect(cell).to_have_attribute("title", re.compile(".+"))
    expect(trang.locator("#mg-message")).to_contain_text("Doanh thu")
    trang.set_viewport_size({"width":390,"height":844})
    expect(trang.locator("#bt-trang-thai")).to_be_visible()
    expect(trang.locator("#bt-trang-thai")).to_have_text("Lỗi lưu")


def test_xoa_dong_bi_tu_choi_khong_bao_da_luu(live_server, trang, dang_nhap, kn_crm, setup, nguoi_dung):
    """AC-21.18 — Xoá bị 400 giữ nguyên dòng, thanh trạng thái phải báo lỗi."""
    row = order(setup, nguoi_dung["staff_sale_1"]).record
    dang_nhap(trang, nguoi_dung["admin"])
    trang.goto(f"{live_server.url}/bang-tinh/{setup[0].code}/")
    trang.locator("[data-select-row='0']").click()
    trang.click("#mg-more-button"); trang.click("#mg-delete-rows")
    trang.route("**/luu-json/", lambda r: r.fulfill(status=400, json={"error":"Chưa xoá được dòng"}))
    with trang.expect_response("**/luu-json/"):
        trang.locator("#mg-xoa-dong [data-choice='delete']").click()
    expect(trang.locator("#bt-trang-thai")).to_have_text("Lỗi lưu")
    row.refresh_from_db()
    assert row.deleted_at is None
