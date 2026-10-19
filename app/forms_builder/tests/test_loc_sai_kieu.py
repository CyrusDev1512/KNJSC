"""Bộ lọc cột trên URL sai kiểu bị từ chối, không lỗi 500 — AC-10.16 (bổ sung 19.10.2026).

Fuzz Bảng dữ liệu: `?f_ngay=-1`, `?f_ngay=2026-13-45`, `?f_doanh_thu=aaa` là **lỗi 500** (`ValidationError` khi ép
về ngày hay số cho cột tách `val_date`, `val_revenue`). `apply_filters` vốn hứa "tham số do người dùng gõ, không tin
được — sai thì bỏ qua", nhưng chỉ bắt `ValueError`, `TypeError`, `FieldError`.
"""
import pytest

from forms_builder.services import record_service

from .test_nhap_xuat import bang_sale  # noqa: F401 — fixture dùng chung

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("tham_so", ["f_ngay=-1", "f_ngay=2026-13-45", "f_ngay=NaN", "f_ngay__lon_bang=abc",
                                     "f_doanh_thu=aaa", "f_doanh_thu__nho_bang=1e309", "f_so_luong=x"])
def test_loc_sai_kieu_chan_khong_500(client, bang_sale, nguoi_dung, tham_so):  # noqa: F811
    """AC-10.16 — Không âm thầm bỏ bộ lọc: đọc trả lỗi rõ, xuất từ chối tạo file và có lời báo."""
    quan_ly = nguoi_dung["manager_sale"]
    record_service.create_record(bang_sale, {"ngay": "2026-08-01", "khach": "A", "doanh_thu": "1", "so_luong": 1},
                                 actor=quan_ly)
    client.force_login(quan_ly)
    response = client.get(f"/bang/don_sale/?{tham_so}")
    assert response.status_code == 400
    assert "Bộ lọc cột" in response.content.decode()
    exported = client.get(f"/bang/don_sale/xuat/?{tham_so}", follow=True)
    assert exported.redirect_chain
    assert "Bộ lọc cột" in exported.content.decode()
    assert "spreadsheet" not in exported["Content-Type"]


def test_trang_cot_ma_cot_la_404_khong_500(client, bang_sale, nguoi_dung):  # noqa: F811
    """AC-10.16 — Trang Cột của bảng với `?cot=` không phải số: 404, không lỗi 500"""
    client.force_login(nguoi_dung["manager_sale"])
    assert client.get("/bang/don_sale/cot/?cot=abc").status_code == 404
    assert client.get("/bang/don_sale/cot/").status_code == 200
