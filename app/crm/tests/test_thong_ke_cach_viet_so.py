"""Thống kê KN CRM viết số như mọi màn hình ERP — AC-22.27 (săn lỗi 06.10.2026, đối soát số liệu).

Đối soát tháng 9 trên hệ thống thật: Báo cáo tổng hợp, Excel, Bảng dữ liệu và Thống kê CRM ra **cùng con số** đến từng
đồng, nhưng Thống kê CRM viết "48311822000" và "387581" trong khi ERP viết "48.311.822.000" — người đối chiếu hai màn
hình phải đếm chữ số. Nhãn điểm biểu đồ còn hiện số Mess là "13026,00".
"""
from datetime import date

import pytest

from .test_executive_statistics import add_row, executive_tables  # noqa: F401 — fixture dùng chung

pytestmark = pytest.mark.django_db


def test_thong_ke_co_dau_cham_ngan_nghin(client, executive_tables, nguoi_dung):  # noqa: F811
    """AC-22.27 — Thống kê CRM hiện số có dấu chấm ngăn nghìn, phẩy thập phân, số nguyên không kèm ",00": doanh số 48311822000 → "48.311.822.000" """
    _, sale, _ = executive_tables
    user = nguoi_dung["manager_sale"]
    add_row(sale, user, date(2026, 9, 11),
            {"nguoi_ban": "Lan", "so_don": 2, "doanh_thu": "2500001", "loai_tien": "VND"}, revenue=2500001, seller="Lan")
    add_row(sale, user, date(2026, 9, 12),
            {"nguoi_ban": "Lan", "so_don": 1000, "doanh_thu": "48311822000", "loai_tien": "VND"},
            revenue=48311822000, seller="Lan")
    client.force_login(user)
    html = client.get("/thong-ke/", {"nguon": sale.code, "tu": "2026-09-11", "den": "2026-09-12"}).content.decode()
    assert "48.314.322.001" in html          # tổng doanh số
    assert "1.002" in html                   # tổng số đơn
    assert "48314322001" not in html
    assert "1002,00" not in html and "1.002,00" not in html
