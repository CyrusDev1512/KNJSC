"""Panel Bộ lọc của lưới tải khi mở; đổi bộ lọc chỉ lấy chip — AC-10.20 (07.10.2026).

Trước đây mở lưới Vận đơn là máy chủ đếm sẵn số dòng theo sản phẩm, thị trường, marketer trên cả bảng (ba lượt GROUP BY)
cho panel Bộ lọc đang ẩn; đổi bộ lọc thì lưới tải lại cả trang HTML chỉ để chép panel và chip. Nay trang lưới không đếm,
mảnh `bo-loc/` trả chip (và panel khi `panel=1`).
"""
import pytest
from django.test.utils import CaptureQueriesContext
from django.db import connection

from forms_builder.services import record_service
from orders.services import dispatch_service

pytestmark = pytest.mark.django_db


@pytest.fixture
def bang_vd(nguoi_dung, settings):
    settings.GRID_ONLY_TABLES = set()
    bang = dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    for i, (qg, tien) in enumerate([("Canada", "CAD"), ("Canada", "CAD"), ("Hoa Kỳ", "USD")]):
        record_service.create_record(bang, {"ma_don": f"BL-{i}", "ngay": "2026-10-07", "ten_khach": f"K{i}",
                                            "so_dien_thoai": f"090{i}", "quoc_gia": qg, "loai_tien": tien},
                                     actor=nguoi_dung["staff_vd"])
    return bang


def test_mo_luoi_khong_dem_san_cho_panel(client, bang_vd, nguoi_dung):
    """AC-10.20 — Trang lưới không có dữ liệu panel (không đếm theo thị trường, sản phẩm); panel là chỗ trống chờ tải"""
    client.force_login(nguoi_dung["staff_vd"])
    with CaptureQueriesContext(connection) as q:
        r = client.get("/bang-tinh/van_don/")
    assert r.status_code == 200 and "ben" not in r.context
    html = r.content.decode()
    assert 'id="mg-filters-body"' in html and "Đang tải bộ lọc" in html and "Áp dụng Thị trường" not in html
    assert not any("GROUP BY" in x["sql"] and "quoc_gia" in x["sql"] for x in q.captured_queries)


def test_manh_bo_loc_tra_chip_va_panel(client, bang_vd, nguoi_dung):
    """AC-10.20 — `bo-loc/?panel=1` trả panel có số đếm theo thị trường và chip đang lọc; không `panel` thì chỉ chip,
    không đếm"""
    client.force_login(nguoi_dung["staff_vd"])
    r = client.get("/bang-tinh/van_don/bo-loc/?f_quoc_gia__trong=Canada&panel=1")
    html = r.content.decode()
    assert r.status_code == 200 and 'id="mg-chips"' in html and 'id="mg-filters-body"' in html
    assert "Canada (2)" in html and "Áp dụng Thị trường" in html
    assert {gt: n for gt, _, n, _ in r.context["ben"]["assignment_filters"][0]["items"]}["Canada"] == 2
    with CaptureQueriesContext(connection) as q:
        r = client.get("/bang-tinh/van_don/bo-loc/?f_quoc_gia__trong=Canada")
    html = r.content.decode()
    assert 'id="mg-chips"' in html and 'id="mg-filters-body"' not in html and "Canada" in html
    assert not any("GROUP BY" in x["sql"] for x in q.captured_queries)


@pytest.mark.parametrize("vai, ma", [("staff_vd", 200), ("staff_kt", 200), ("admin", 200)])
def test_manh_bo_loc_theo_vai(client, bang_vd, nguoi_dung, vai, ma):
    """AC-10.20 — Mảnh bộ lọc theo đúng quyền xem bảng: các vai xem được lưới thì 200"""
    client.force_login(nguoi_dung[vai])
    assert client.get("/bang-tinh/van_don/bo-loc/?panel=1").status_code == ma


def test_manh_bo_loc_tu_choi(client, bang_vd, nguoi_dung):
    """AC-10.20 — Chưa đăng nhập thì về trang đăng nhập; bảng không có hay ngoài phạm vi thì 404"""
    assert client.get("/bang-tinh/van_don/bo-loc/").status_code == 302
    client.force_login(nguoi_dung["staff_vd"])
    assert client.get("/bang-tinh/khong_co/bo-loc/").status_code == 404
