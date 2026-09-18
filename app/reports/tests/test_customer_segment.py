"""ADR-038 — Tệp khách hàng: cột Chọn một của bảng báo cáo Marketing, bộ lọc `tep`."""
from datetime import date

import pytest

from core.exceptions import BusinessError
from forms_builder.models import ColumnDef, FormDef, FormField
from forms_builder.services import record_service
from reports.constants import CUSTOMER_SEGMENT_COLUMN, CUSTOMER_SEGMENT_DEFAULTS
from reports.management.commands.configure_erp_reports import configure_source
from reports.models import ReportSource
from reports.services import activity_service
from reports.tests.test_aggregations import bang_mkt  # noqa: F401

pytestmark = pytest.mark.django_db


def test_tep_khach_hang(client, bang_mkt, nguoi_dung):
    """AC-38.4 — Cột Tệp khách hàng với danh sách mặc định có trên bảng và biểu mẫu Marketing; nộp giá trị
    ngoài danh sách bị từ chối; lọc `tep` đúng giá trị, `__missing__` = chưa có, giá trị lạ → 400;
    Leader/Manager Marketing thêm giá trị ngay ô chọn, Staff bị từ chối; phụ đề Excel ghi tệp"""
    from io import BytesIO
    from openpyxl import load_workbook

    form = FormDef.objects.create(table=bang_mkt, department=bang_mkt.department, code="bc_mkt_tep", name="BC MKT")
    configure_source(bang_mkt, "mkt")
    column = ColumnDef.objects.get(table=bang_mkt, code=CUSTOMER_SEGMENT_COLUMN)
    assert column.field_type == "choice" and column.options == list(CUSTOMER_SEGMENT_DEFAULTS)
    assert FormField.objects.filter(form=form, link__column=column).exists()
    source = ReportSource.objects.get(table=bang_mkt)
    assert source.columns["segment"] == CUSTOMER_SEGMENT_COLUMN
    assert activity_service.segment_options(source) == list(CUSTOMER_SEGMENT_DEFAULTS)

    staff, manager = nguoi_dung["staff_mkt"], nguoi_dung["manager_mkt"]
    base = {"ngay": "2026-08-01", "marketer": "x", "san_pham": "SP1", "so_mess": 10, "cpqc": "3",
            "so_don": 2, "doanh_so": "100", "thi_truong": "Canada"}
    ngay = date(2026, 8, 1)   # ngày của nguồn báo cáo do hệ thống đặt (ADR-032)
    co_tep = record_service.create_record(bang_mkt, {**base, CUSTOMER_SEGMENT_COLUMN: "Filipino"}, actor=staff, system_day=ngay)
    khong_tep = record_service.create_record(bang_mkt, base, actor=staff, system_day=ngay)
    assert co_tep.data[CUSTOMER_SEGMENT_COLUMN] == "Filipino" and CUSTOMER_SEGMENT_COLUMN not in khong_tep.data
    with pytest.raises(BusinessError):
        record_service.create_record(bang_mkt, {**base, CUSTOMER_SEGMENT_COLUMN: "Klingon"}, actor=staff, system_day=ngay)

    ky = dict(start=date(2026, 8, 1), end=date(2026, 8, 31))
    assert activity_service.build(manager, source, segment="Filipino", **ky).totals["so_dong"] == 1
    assert activity_service.build(manager, source, segment="__missing__", **ky).totals["so_dong"] == 1
    assert activity_service.build(manager, source, **ky).totals["so_dong"] == 2
    with pytest.raises(BusinessError):
        activity_service.build(manager, source, segment="Klingon", **ky)

    client.force_login(manager)
    query = {"nguon": bang_mkt.code, "tu": "2026-08-01", "den": "2026-08-31"}
    page = client.get("/bao-cao/tong-hop/", {**query, "tep": "Filipino"})
    assert page.status_code == 200 and page.context["result"].totals["so_dong"] == 1
    assert page.context["segments"] == list(CUSTOMER_SEGMENT_DEFAULTS)
    assert '<option selected>Filipino</option>' in page.content.decode()
    assert client.get("/bao-cao/tong-hop/", {**query, "tep": "Klingon"}).status_code == 400
    sheet = list(load_workbook(BytesIO(client.get("/bao-cao/tong-hop/xuat/", {**query, "tep": "Filipino"}).content),
                               data_only=True).active.values)
    assert "Tệp khách hàng: Filipino" in sheet[1][0]

    # Thêm giá trị ngay ô chọn: Manager Marketing được, Staff bị từ chối
    url = f"/bang/{bang_mkt.code}/cot/{CUSTOMER_SEGMENT_COLUMN}/lua-chon/"
    assert client.post(url, {"nhan_moi": "Thai"}).status_code == 200
    assert "Thai" in ColumnDef.objects.get(pk=column.pk).options
    client.force_login(staff)
    assert client.post(url, {"nhan_moi": "Khmer"}).status_code == 403
    assert "Khmer" not in ColumnDef.objects.get(pk=column.pk).options
