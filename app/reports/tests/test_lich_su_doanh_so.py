"""Doanh số ở Lịch sử báo cáo đọc được ngay — AC-4.11 (kiểm toàn diện 04.10.2026).

Trước đây danh sách Lịch sử in thẳng số máy: "Doanh số: 45000000,00" — không dấu chấm ngăn nghìn, ",00" thừa, không
biết tiền gì. Nay cùng cách viết số với Báo cáo tổng hợp, kèm loại tiền của dòng báo cáo.
"""
from datetime import date

import pytest
from django.core.management import call_command

from forms_builder.models import FormDef
from orders.models import Product
from reports.services import daily_service
from reports.tests.test_aggregations import bang_mkt  # noqa: F401
from reports.tests.test_mkt_derived_revenue import mkt_source  # noqa: F401

pytestmark = pytest.mark.django_db


def _nop(form, raw, actor):
    fields = list(form.ordered_fields())
    values = {f.field.code: raw.get(f.link.column.code, "") for f in fields}
    return daily_service.submit(form, values, report_date=date(2026, 8, 1), actor=actor, fields=fields)


def _doanh_so(client, actor):
    client.force_login(actor)
    html = client.get("/bao-cao/lich-su/").content.decode()
    return [d.split("</span>")[0] for d in html.split("<span>Doanh số: ")[1:]]


def test_doanh_so_o_lich_su_co_dau_cham_va_loai_tien(client, departments, nguoi_dung, bang_mkt, mkt_source):  # noqa: F811
    """AC-4.11 — Lịch sử báo cáo hiện Doanh số theo cách viết Việt Nam kèm loại tiền: báo cáo Sale Canada 1250000 → "1.250.000 CAD", số lẻ giữ đúng (720,5 USD); báo cáo Marketing 45000000 → "45.000.000 VND"; không còn ",00" thừa"""
    Product.objects.create(code="p", name="Sản phẩm P")
    call_command("configure_erp_reports")
    sale = FormDef.objects.get(code="bc_sale_ngay")
    _nop(sale, {"ngay": "2026-08-01", "san_pham": "Sản phẩm P", "thi_truong": "Canada", "so_mess": "10",
                "so_don": "2", "doanh_so": "1250000"}, nguoi_dung["staff_sale_1"])
    _nop(sale, {"ngay": "2026-08-01", "san_pham": "Sản phẩm P", "thi_truong": "Hoa Kỳ", "so_mess": "10",
                "so_don": "2", "doanh_so": "720.50"}, nguoi_dung["staff_sale_1"])
    assert sorted(_doanh_so(client, nguoi_dung["staff_sale_1"])) == ["1.250.000 CAD", "720,5 USD"]

    mkt = mkt_source.table.forms.get()
    _nop(mkt, {"ngay": "2026-08-01", "marketer": "x", "san_pham": "SP1", "so_mess": "10", "cpqc": "3000000",
               "so_don": "2", "doanh_so": "45000000"}, nguoi_dung["staff_mkt"])
    assert _doanh_so(client, nguoi_dung["staff_mkt"]) == ["45.000.000 VND"]
