"""Bộ lọc cột trên URL sai kiểu bị bỏ qua, không lỗi 500 — AC-10.16 (săn lỗi 06.10.2026, fuzz).

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
def test_loc_sai_kieu_bo_qua_khong_500(client, bang_sale, nguoi_dung, tham_so):  # noqa: F811
    """AC-10.16 — Bộ lọc cột ngày, tiền, số nguyên nhận giá trị sai kiểu trên URL: trang vẫn mở (200), bộ lọc đó bị bỏ qua — cả ở Bảng dữ liệu lẫn Xuất tệp"""
    quan_ly = nguoi_dung["manager_sale"]
    record_service.create_record(bang_sale, {"ngay": "2026-08-01", "khach": "A", "doanh_thu": "1", "so_luong": 1},
                                 actor=quan_ly)
    client.force_login(quan_ly)
    assert client.get(f"/bang/don_sale/?{tham_so}").status_code == 200
    assert client.get(f"/bang/don_sale/xuat/?{tham_so}").status_code == 200


def test_trang_cot_ma_cot_la_404_khong_500(client, bang_sale, nguoi_dung):  # noqa: F811
    """AC-10.16 — Trang Cột của bảng với `?cot=` không phải số: 404, không lỗi 500"""
    client.force_login(nguoi_dung["manager_sale"])
    assert client.get("/bang/don_sale/cot/?cot=abc").status_code == 404
    assert client.get("/bang/don_sale/cot/").status_code == 200
