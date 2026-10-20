"""Lọc số trên lưới thật: nhận số Việt, không treo tải khi bộ lọc sai."""
import pytest
from playwright.sync_api import expect

from forms_builder.tests.test_kieu_loc_sap_va_ngay import typed_table  # noqa: F401

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet]


def test_loc_tien_va_bao_loi_khong_treo(live_server, trang, dang_nhap, settings, typed_table, nguoi_dung):
    """AC-10.16 — Áp dụng số Việt thực sự thu hẹp; số mũ quá lớn trả JSON lỗi và thoát trạng thái tải."""
    table, rows = typed_table
    table.workflow = "waybill"; table.save(update_fields=["workflow"])
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.BANGTINH_URL = ""
    settings.GRID_ONLY_TABLES = set()
    dang_nhap(trang, nguoi_dung["admin"])
    trang.goto(f"{live_server.url}/bang-tinh/{table.code}/")
    trang.click('[data-filter="tien"]')
    trang.locator("#hop-loc summary").click()
    trang.locator("#loc-tu-tien").fill("1.000")
    with trang.expect_response(lambda r: "/du-lieu/" in r.url) as data:
        trang.locator("#hop-loc button[type=submit]").click()
    assert data.value.status == 200
    assert [r["id"] for r in data.value.json()["rows"]] == [rows[0].pk]
    trang.click('[data-filter="tien"]')
    trang.locator("#hop-loc summary").click()
    trang.locator("#loc-tu-tien").fill("1e200000")
    with trang.expect_response(lambda r: "/du-lieu/" in r.url) as data:
        trang.locator("#hop-loc button[type=submit]").click()
    assert data.value.status == 400
    assert "Bộ lọc cột" in data.value.json()["error"]
    expect(trang.locator("#mg-message")).to_contain_text("Bộ lọc cột")
    expect(trang.locator("#bt-trang-thai")).to_have_text("Không tải được dữ liệu")
