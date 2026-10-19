"""Manager đọc đơn toàn công ty qua giao diện CRM/ERP, không nhận quyền sửa hay Quản trị."""
import pytest
from playwright.sync_api import expect

from crm.tests.test_waybill_new import setup, order  # noqa: F401

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet]


@pytest.mark.parametrize("page_fixture", ["trang", "trang_dien_thoai"])
def test_manager_mkt_doc_duoc_van_don_crm_erp(request, live_server, dang_nhap, settings, setup, nguoi_dung, page_fixture):
    """AC-3.4/AC-3.7 — Manager Marketing chưa lên đơn đọc được đơn Sale; không có trình sửa hay Quản trị."""
    page = request.getfixturevalue(page_fixture)
    item = order(setup, nguoi_dung["staff_sale_1"])
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.BANGTINH_URL = ""
    dang_nhap(page, nguoi_dung["manager_mkt"])
    page.goto(live_server.url + "/thu-muc/")
    expect(page.get_by_text(setup[0].name, exact=True).first).to_be_visible()
    page.goto(live_server.url + "/bang-tinh/van_don/")
    cell = page.locator(f".mg-cell[data-id='{item.record_id}'][data-code='ma_don']")
    expect(cell).to_have_text(item.code)
    # Chọn ô vẫn được, sửa thì không: quyền đọc mới không mở editor.
    cell.dblclick()
    expect(page.locator("#mg-editor")).to_be_hidden()
    settings.ROOT_URLCONF = "knjsc.urls"
    page.goto(live_server.url + "/bang/van_don/")
    expect(page.locator("table.bang-luoi")).to_contain_text(item.code)
    expect(page.get_by_role("button", name="Quản trị", exact=True)).to_have_count(0)
    expect(page.locator('a[href="/nhat-ky/"]')).to_have_count(0)
