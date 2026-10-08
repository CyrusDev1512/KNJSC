"""Nút Xoá dòng trên lưới Vận đơn — chỉ Admin (AC-21.18, AC-21.19, ADR-049, chủ dự án 08.10.2026)."""
import pytest

from crm.tests.test_waybill_new import order, setup  # noqa: F401  (fixture dùng lại)
from forms_builder.models import DataRecord
from orders.models import Order

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]


@pytest.fixture
def kn_crm(settings):
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.BANGTINH_URL = ""
    return settings


def _so_dong(trang):
    return trang.locator("#mg-count").inner_text().split(" ")[0]


def test_admin_xoa_hai_dong_roi_hoan_tac(live_server, trang, dang_nhap, kn_crm, setup, nguoi_dung):
    """AC-21.18 — Admin chọn hai dòng (bấm số dòng, Shift+bấm), menu "…" → Xoá dòng đang chọn → hộp xác nhận nêu số
    dòng, con trỏ ở Huỷ → Xoá dòng: tổng giảm 2, hai đơn gốc bị bỏ; Ctrl+Z khôi phục cả hai, tổng về như cũ; không lỗi JS"""
    dons = [order(setup, nguoi_dung["staff_sale_1"]) for _ in range(3)]
    loi_js = []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(trang, nguoi_dung["admin"])
    trang.goto(f"{live_server.url}/bang-tinh/van_don/")
    trang.wait_for_selector(".mg-cell[data-code='ma_don']")
    assert _so_dong(trang) == "3"

    trang.locator("[data-select-row='0']").click()
    trang.locator("[data-select-row='1']").click(modifiers=["Shift"])
    trang.click("#mg-more-button")
    trang.click("#mg-delete-rows")
    hop = trang.locator("#mg-xoa-dong")
    hop.wait_for(state="visible")
    assert "2" in trang.locator("#mg-xoa-dong-so").inner_text()
    assert trang.evaluate("() => document.activeElement.dataset.choice") == "cancel"
    hop.locator("[data-choice='delete']").click()
    trang.wait_for_function("() => document.getElementById('mg-count').innerText.startsWith('1 ')")
    assert Order.objects.count() == 1
    assert DataRecord.objects.filter(pk__in=[d.record_id for d in dons]).count() == 1

    trang.locator("#mg-viewport, .mg-viewport").first.focus()
    trang.keyboard.press("Control+z")
    trang.wait_for_function("() => document.getElementById('mg-count').innerText.startsWith('3 ')")
    assert Order.objects.count() == 3
    assert not loi_js, loi_js


def test_staff_khong_co_nut_xoa_dong(live_server, trang, dang_nhap, kn_crm, setup, nguoi_dung):
    """AC-21.19 — Nhân viên Vận đơn mở lưới: menu "…" không có mục Xoá dòng, trang không có hộp xác nhận xoá dòng"""
    order(setup, nguoi_dung["staff_sale_1"])
    dang_nhap(trang, nguoi_dung["staff_vd"])
    trang.goto(f"{live_server.url}/bang-tinh/van_don/")
    trang.wait_for_selector(".mg-cell[data-code='ma_don']")
    trang.click("#mg-more-button")
    assert trang.locator("#mg-delete-rows").count() == 0
    assert trang.locator("#mg-xoa-dong").count() == 0
