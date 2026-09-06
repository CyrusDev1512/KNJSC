"""Màn hình điện thoại 390px — AC-10.4, AC-11.11 (phần máy đo được).

Máy chỉ đo được một điều chắc chắn: **trang không tràn ngang** — thanh cuộn
ngang của cả trang là dấu hiệu bố cục vỡ. Bấm được, đọc được vẫn là việc
người kiểm bằng tay; ảnh chụp lưu ở `storage/e2e/` để đối chiếu.
"""
import pytest

from forms_builder.services import record_service
from orders.services import dispatch_service

from .conftest import chup

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]

#: (tên, đường dẫn, vai, URLconf) — lưới nằm ở app KN CRM (ADR-012)
ERP, CRM = "knjsc.urls", "knjsc.urls_bangtinh"
MAN_HINH = [
    ("tong-quan", "/", "staff_vd", ERP),
    ("bang-du-lieu", "/bang/van_don/", "staff_vd", ERP),
    ("bang-tinh", "/bang-tinh/", "staff_vd", CRM),
    ("len-don", "/len-don/", "staff_sale_1", ERP),
    ("bao-cao-ngay", "/bao-cao-ngay/", "staff_mkt", ERP),
    ("nhap-tep", "/bang/van_don/nhap/", "admin", ERP),
]


@pytest.fixture
def du_lieu(departments, nguoi_dung):
    bang = dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    for i in range(3):
        record_service.create_record(bang, {
            "ma_don": f"DH-{i}", "ngay": "2026-08-01", "ten_khach": f"Khách {i}",
            "so_dien_thoai": f"09{i}", "trang_thai_vc": "Đang giao",
        }, actor=nguoi_dung["staff_vd"])
    return bang


@pytest.mark.parametrize("ten,duong_dan,vai,urlconf", MAN_HINH, ids=[m[0] for m in MAN_HINH])
def test_khong_tran_ngang_tren_dien_thoai(live_server, trang_dien_thoai, dang_nhap, du_lieu,
                                          nguoi_dung, settings, ten, duong_dan, vai, urlconf):
    """AC-10.4 — Trên màn hình 390px mỗi màn hình chính không tràn ngang, và có ảnh chụp để đối chiếu"""
    settings.ROOT_URLCONF = urlconf
    settings.GRID_ONLY_TABLES = set() if urlconf == CRM else settings.GRID_ONLY_TABLES
    page = trang_dien_thoai
    dang_nhap(page, nguoi_dung[vai])
    page.goto(live_server.url + duong_dan)
    page.wait_for_load_state("networkidle")
    assert page.locator("h1").count() >= 1
    do = page.evaluate("({rong: document.documentElement.scrollWidth, khung: window.innerWidth})")
    assert do["rong"] <= do["khung"] + 1, f"{duong_dan} tràn ngang: {do}"
    chup(page, f"dien-thoai-{ten}")
