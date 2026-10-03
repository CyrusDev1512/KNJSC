"""Thống kê KN CRM sau khi form Marketing bỏ Sản phẩm — ADR-048 (03.10.2026)."""
from datetime import date

import pytest

from crm.tests.test_executive_statistics import add_row, executive_tables  # noqa: F401

pytestmark = pytest.mark.django_db


def test_mkt_khong_con_bieu_do_theo_san_pham(client, executive_tables, nguoi_dung):  # noqa: F811
    """AC-48.6 — Thống kê KN CRM nguồn Marketing không còn biểu đồ "Đóng góp theo sản phẩm" (báo cáo mới không có
    sản phẩm, cột "Chưa có sản phẩm" sẽ chiếm hết); biểu đồ theo Marketer vẫn còn; nguồn Sale vẫn có biểu đồ theo
    sản phẩm"""
    marketing, sale, _ = executive_tables
    add_row(marketing, nguoi_dung["manager_mkt"], date(2026, 9, 11),
            {"marketer": "A", "so_mess": 10, "cpqc": "100", "so_don": 1, "doanh_so": "1000"},
            revenue=1000, seller="A", product="")
    add_row(sale, nguoi_dung["manager_sale"], date(2026, 9, 11),
            {"nguoi_ban": "Lan", "so_don": 2, "doanh_thu": "200", "loai_tien": "USD"},
            revenue=200, seller="Lan", product="SP1")
    client.force_login(nguoi_dung["admin"])
    mkt = client.get("/thong-ke/", {"nguon": marketing.code, "tu": "2026-09-11", "den": "2026-09-11"})
    tieu_de = [c["title"] for c in mkt.context["dashboard"]["charts"]]
    assert "Đóng góp theo sản phẩm" not in tieu_de and "Đóng góp theo Marketer" in tieu_de
    ban = client.get("/thong-ke/", {"nguon": sale.code, "tu": "2026-09-11", "den": "2026-09-11"})
    assert "Đóng góp theo sản phẩm" in [c["title"] for c in ban.context["dashboard"]["charts"]]
