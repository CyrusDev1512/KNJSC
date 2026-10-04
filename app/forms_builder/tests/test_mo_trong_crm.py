"""Bảng dữ liệu KN ERP chỉ dẫn sang KN CRM khi CRM phục vụ bảng đó — AC-40.7 (kiểm toàn diện 04.10.2026).

Từ ADR-040 KN CRM chỉ phục vụ bảng vận đơn: bảng thường và bảng báo cáo Sale/MKT mở ở CRM là 404. Nút "Mở trong
KN CRM" và câu "Sửa số liệu ở KN CRM" trên Bảng dữ liệu vẫn hiện cho mọi bảng nên dẫn người dùng tới trang lỗi.
"""
import pytest

from forms_builder.tests.test_man_hinh_bang import bang_sale  # noqa: F401
from orders.services import dispatch_service
from reports.tests.test_aggregations import bang_mkt  # noqa: F401
from reports.tests.test_mkt_derived_revenue import mkt_source  # noqa: F401

pytestmark = pytest.mark.django_db

NUT = 'rel="noopener">Mở trong KN CRM</a>'


def test_chi_bang_van_don_co_nut_mo_trong_kn_crm(client, settings, nguoi_dung, bang_sale, bang_mkt, mkt_source):  # noqa: F811
    """AC-40.7 — Bảng dữ liệu của bảng vận đơn có nút "Mở trong KN CRM" trỏ đúng lưới; bảng thường và bảng báo cáo Marketing (CRM không phục vụ, ADR-040) không còn nút hay liên kết nào sang KN CRM, vẫn ghi rõ là bảng chỉ để xem"""
    settings.BANGTINH_URL = "http://crm.test/"
    dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    client.force_login(nguoi_dung["admin"])

    html = client.get("/bang/van_don/").content.decode()
    assert NUT in html and 'href="http://crm.test/bang-tinh/van_don/"' in html

    for ma in ("don_sale", bang_mkt.code):
        kq = client.get(f"/bang/{ma}/")
        assert kq.status_code == 200, ma
        html = kq.content.decode()
        assert "Bảng này chỉ để xem" in html, ma
        assert NUT not in html and "http://crm.test/bang-tinh/" not in html, ma
