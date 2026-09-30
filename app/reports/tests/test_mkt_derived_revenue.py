"""ADR-038 — Doanh thu Marketing suy ra từ vận đơn và Hóa đơn/Doanh thu theo nhãn."""
from datetime import date
from decimal import Decimal
from io import BytesIO

import pytest
from openpyxl import load_workbook

from core.identity import employee_code
from forms_builder.models import DataRecord, FormDef, TableDef
from forms_builder.services import record_service
from orders.constants import ACTIVE_WAYBILL_TABLE_CODE
from orders.models import Product, WaybillAssignment, WaybillItem
from orders.services import dispatch_service
from reports import aggregations
from reports.management.commands.configure_erp_reports import configure_source
from reports.models import ReportSource
from reports.services import activity_service
from reports.tests.test_aggregations import bang_mkt  # noqa: F401

pytestmark = pytest.mark.django_db


@pytest.fixture
def mkt_source(bang_mkt, nguoi_dung):
    """Nguồn Marketing cấu hình thật (`configure_erp_reports`): có Hóa đơn, Tệp khách hàng,
    Thị trường, Loại tiền; không còn cột nhập Doanh thu."""
    FormDef.objects.create(table=bang_mkt, department=bang_mkt.department, code="bc_mkt_dr", name="BC MKT")
    configure_source(bang_mkt, "mkt")
    return ReportSource.objects.get(table=bang_mkt)


def _bao_cao(bang, actor, ngay, san_pham, *, mess=10, cpqc="3", don=2, doanh_so="100", hoa_don="8", tep=""):
    values = {"ngay": ngay, "marketer": "x", "san_pham": san_pham, "so_mess": mess, "cpqc": cpqc,
              "so_don": don, "doanh_so": doanh_so, "hoa_don": hoa_don, "thi_truong": "Canada"}
    if tep:
        values["tep_khach_hang"] = tep
    # Ngày của nguồn báo cáo do hệ thống đặt (ADR-032) → truyền ngày hệ thống của bài kiểm
    return record_service.create_record(bang, values, actor=actor, system_day=date.fromisoformat(ngay))


@pytest.fixture
def van_don(nguoi_dung, departments):
    """Vận đơn có chi tiết đã thu tiền, phân công Marketing cho A (staff_mkt) và B (manager_mkt)."""
    dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    table = TableDef.objects.get(code=ACTIVE_WAYBILL_TABLE_CODE)
    sp1 = Product.objects.create(code="sp1", name="SP1")
    sp2 = Product.objects.create(code="sp2", name="SP2")
    A, B = nguoi_dung["staff_mkt"], nguoi_dung["manager_mkt"]

    def don(ngay, marketer, product, paid, *, currency="CAD", market="Canada"):
        row = DataRecord.objects.create(
            table=table, department=table.department, created_by=nguoi_dung["admin"], val_date=ngay,
            data={"ngay": ngay.isoformat(), "quoc_gia": market, "loai_tien": currency,
                  "trang_thai_vc": "Đã lên đơn"})
        if marketer is not None:
            WaybillAssignment.objects.create(record=row, marketing=marketer)
        WaybillItem.objects.create(record=row, product=product, quantity=1, unit_price="100.00", paid_amount=paid)
        return row

    return {
        "table": table, "sp1": sp1, "sp2": sp2, "A": A, "B": B,
        "w1": don(date(2026, 8, 1), A, sp1, "60.00"),
        "w2": don(date(2026, 8, 1), A, sp2, "40.00"),
        "w3": don(date(2026, 8, 2), A, sp1, "25.00"),
        "w4": don(date(2026, 8, 1), B, sp1, "200.00"),
        "w5": don(date(2026, 8, 1), None, sp1, "999.00"),          # chưa phân công Marketing
        "w6": don(date(2026, 7, 31), A, sp1, "500.00"),            # ngoài kỳ
        "w7": don(date(2026, 8, 1), nguoi_dung["staff_sale_1"], sp1, "77.00"),   # người không có báo cáo
    }


def test_doanh_thu_suy_ra_tu_van_don(client, bang_mkt, mkt_source, van_don, nguoi_dung):
    """AC-38.2 — DS Chốt (TT) = tiền đã thu của vận đơn do marketer phụ trách, cùng kỳ theo ngày lên
    đơn, đúng số tiền theo loại tiền của đơn, không quy đổi (ADR-046), đúng ở cách xem ngày, nhân viên,
    sản phẩm, thị trường, team; tổng = tổng dòng; đơn chưa phân công, marketer khác, ngoài kỳ, khác
    sản phẩm không vào; Staff chỉ thấy tiền của mình; Excel và Tổng quan cùng số; lọc Tệp khách hàng thì
    DS Chốt (TT) trống"""
    A, B = van_don["A"], van_don["B"]
    _bao_cao(bang_mkt, A, "2026-08-01", "SP1", hoa_don="8")
    _bao_cao(bang_mkt, A, "2026-08-02", "SP1", hoa_don="5", tep="Filipino")
    _bao_cao(bang_mkt, B, "2026-08-01", "SP2", hoa_don="2")
    manager = B
    ky = dict(start=date(2026, 8, 1), end=date(2026, 8, 2))
    # Báo cáo và vận đơn của bài này đều CAD; số giữ nguyên, không nhân tỉ giá (ADR-046)

    def cells(result):
        # Cách xem Tổng hợp nhóm theo ngày × nhân sự (AC-22.14) nên khoá là cặp (ngày, mã)
        out = {}
        for item in result.rows:
            nhom, raw = aggregations.row_values(item, result)
            khoa = aggregations.format_group(nhom, result)
            if "person_name" in item:
                khoa = (khoa, item["person_name"])
            out[khoa] = dict(zip([c.label for c in result.columns], raw))
        return out

    # Ngày × nhân sự: 01.08 A = 60 + 40, 01.08 B = 200, 02.08 A = 25; tổng 325; tiền của ngày
    # KHÔNG dồn hết cho một người vì doanh thu suy ra khoá theo cặp (ngày, marketer)
    result = activity_service.build(manager, mkt_source, group="day", **ky)
    assert result.ok and "không quy đổi" in result.currency_label and not result.currency_warning
    rows = cells(result)
    assert rows[("01.08.2026", employee_code(A))]["DS Chốt (TT)"] == 100
    assert rows[("01.08.2026", employee_code(B))]["DS Chốt (TT)"] == 200
    assert rows[("02.08.2026", employee_code(A))]["DS Chốt (TT)"] == 25
    # Hóa đơn 8 CAD ÷ tiền đã thu 100 CAD
    assert rows[("01.08.2026", employee_code(A))]["Hóa đơn/DS Chốt (TT)"] == Decimal(8) / Decimal(100)
    totals = dict(zip([c.label for c in result.columns], aggregations.total_values(result)))
    assert totals["DS Chốt (TT)"] == 325 and totals["Hóa đơn/DS Chốt (TT)"] == Decimal(15) / Decimal(325)
    assert [c.kind for c in result.columns if c.label == "DS Chốt (TT)"] == ["derived"]
    # Cột đối soát số đơn đi cùng (ADR-042): w1, w2 của A và w4 của B ngày 01.08; w3 của A ngày 02.08
    assert rows[("01.08.2026", employee_code(A))]["Số đơn (TT)"] == 2 and rows[("01.08.2026", employee_code(B))]["Số đơn (TT)"] == 1
    assert totals["Số đơn (TT)"] == 4

    # Theo nhân viên: nhãn chỉ mã (khoá nối doanh thu suy ra cùng biểu thức); sản phẩm; thị trường; team
    rows = cells(activity_service.build(manager, mkt_source, group="person", **ky))
    assert rows[employee_code(A)]["DS Chốt (TT)"] == 125 and rows[employee_code(B)]["DS Chốt (TT)"] == 200
    rows = cells(activity_service.build(manager, mkt_source, group="product", **ky))
    assert rows["SP1"]["DS Chốt (TT)"] == 285 and rows["SP2"]["DS Chốt (TT)"] == 40
    rows = cells(activity_service.build(manager, mkt_source, group="market", **ky))
    assert rows["Canada"]["DS Chốt (TT)"] == 325
    # Theo team thay Phòng ban (AC-22.20): A và B chưa gán team → một dòng "Chưa có team" = cả kỳ
    rows = cells(activity_service.build(manager, mkt_source, group="team", **ky))
    assert rows["Chưa có team"]["DS Chốt (TT)"] == 325

    # Lọc sản phẩm: chỉ dòng báo cáo SP1 (của A) và tiền SP1 của A
    rows = cells(activity_service.build(manager, mkt_source, group="day", product="SP1", **ky))
    assert rows[("01.08.2026", employee_code(A))]["DS Chốt (TT)"] == 60
    assert rows[("02.08.2026", employee_code(A))]["DS Chốt (TT)"] == 25
    # Lọc thị trường và kỳ hẹp
    rows = cells(activity_service.build(manager, mkt_source, group="day", market="Canada", start=date(2026, 8, 2), end=date(2026, 8, 2)))
    assert list(rows) == [("02.08.2026", employee_code(A))] and rows[("02.08.2026", employee_code(A))]["DS Chốt (TT)"] == 25
    # Staff chỉ thấy tiền của mình
    rows = cells(activity_service.build(A, mkt_source, group="day", **ky))
    assert rows[("01.08.2026", employee_code(A))]["DS Chốt (TT)"] == 100
    assert rows[("02.08.2026", employee_code(A))]["DS Chốt (TT)"] == 25
    # Lọc Tệp khách hàng: phần đối soát trống, các cột khác vẫn có
    rows = cells(activity_service.build(manager, mkt_source, group="day", segment="Filipino", **ky))
    khoa = ("02.08.2026", employee_code(A))
    assert list(rows) == [khoa] and rows[khoa]["DS Chốt (TT)"] is None and rows[khoa]["Số Mess"] == 10

    # Excel và Tổng quan cùng số với màn hình
    client.force_login(manager)
    query = {"nguon": bang_mkt.code, "tu": "2026-08-01", "den": "2026-08-02"}
    page = client.get("/bao-cao/tong-hop/", query)
    assert page.status_code == 200
    screen = aggregations.total_values(page.context["result"])
    sheet = list(load_workbook(BytesIO(client.get("/bao-cao/tong-hop/xuat/", query).content), data_only=True).active.values)
    dong_tong = next(r for r in sheet if r[0] and str(r[0]).startswith("TỔNG CỘNG"))   # khối toàn kỳ (ADR-042)
    # openpyxl đọc số về float: so từng ô với sai số nhỏ, ô trống phải cùng trống
    for excel_cell, screen_cell in zip(dong_tong[-len(screen):], screen):
        if screen_cell is None:
            assert excel_cell is None
        else:
            assert abs(Decimal(str(excel_cell)) - screen_cell) < Decimal("1e-9")
    dashboard = client.get("/", {"mkt_nguon": bang_mkt.code, "tu": query["tu"], "den": query["den"]})
    block = next(b for b in dashboard.context["activity"]["blocks"] if b["kind"] == "mkt")
    # Thẻ Tổng quan: mỗi loại tiền một cột (ADR-046) — ở đây chỉ CAD, số đúng như tiền của đơn
    assert block["data"]["currencies"] == ["CAD"] and dict(block["data"]["metrics"])["DS Chốt (TT)"] == ["325"]


def test_hoa_don_chia_doanh_thu_va_canh_bao_tien(bang_mkt, mkt_source, van_don, nguoi_dung):
    """AC-38.3 — Hóa đơn/DS Chốt (TT) = Hóa đơn ÷ DS Chốt (TT) theo nhãn; thiếu một vế thì trống; vận đơn
    đối soát theo loại tiền của đơn (ADR-046): đơn USD vào dòng USD của marketer, không cộng vào dòng CAD,
    không quy đổi; tổng chung có hai loại tiền thì không cộng tiền; `configure_erp_reports` không tạo cột
    nhập Doanh thu, gỡ trường đó khỏi biểu mẫu, bỏ cột tính từng dòng, chạy lại không đổi"""
    from forms_builder.models import ColumnDef, FieldDef, FormField, FormTableLink

    A = van_don["A"]
    assert not bang_mkt.columns.filter(code="doanh_thu").exists()
    assert not bang_mkt.columns.filter(code="hoa_don_doanh_thu").exists()
    assert "revenue" not in mkt_source.columns and mkt_source.columns["invoice"] == "hoa_don"
    # Bảng cũ có cột nhập Doanh thu (có trường trên biểu mẫu) và cột tính từng dòng:
    # cấu hình lại gỡ trường khỏi biểu mẫu, giữ cột, bỏ cột tính
    cu = ColumnDef.objects.create(table=bang_mkt, code="doanh_thu", name="Doanh thu", field_type="money")
    form = FormDef.objects.get(code="bc_mkt_dr")
    truong = FieldDef.objects.create(department=bang_mkt.department, code="erp_cu_doanh_thu", name="Doanh thu", field_type="money")
    FormTableLink.objects.create(form_field=FormField.objects.create(form=form, field=truong, order=99), column=cu)
    ColumnDef.objects.create(table=bang_mkt, code="hoa_don_doanh_thu", name="Hóa đơn/Doanh thu",
                             field_type="decimal", is_computed=True, compute_op="divide",
                             compute_left="gia_mess", compute_right="cpo", compute_decimals=4)
    assert FormField.objects.filter(form__table=bang_mkt, link__column__code="doanh_thu").exists()
    configure_source(bang_mkt, "mkt")
    configure_source(bang_mkt, "mkt")
    assert bang_mkt.columns.filter(code="doanh_thu").exists()                 # giữ để đọc lịch sử
    assert not FormField.objects.filter(form__table=bang_mkt, link__column__code="doanh_thu").exists()
    assert not bang_mkt.columns.filter(code="hoa_don_doanh_thu").exists()
    assert "revenue" not in ReportSource.objects.get(table=bang_mkt).columns

    # Không có vận đơn trong kỳ → DS Chốt (TT) và tỉ số trống, Số đơn (TT) là 0, Hóa đơn vẫn có
    _bao_cao(bang_mkt, A, "2026-08-05", "SP1", hoa_don="8")
    result = activity_service.build(nguoi_dung["manager_mkt"], mkt_source, start=date(2026, 8, 5), end=date(2026, 8, 5))
    totals = dict(zip([c.label for c in result.columns], aggregations.total_values(result)))
    assert totals["Hóa đơn"] == 8 and totals["DS Chốt (TT)"] is None and totals["Hóa đơn/DS Chốt (TT)"] is None
    assert totals["Số đơn (TT)"] == 0 and totals["Tỉ lệ chốt (TT)"] == 0
    # Có vận đơn: đúng Hóa đơn ÷ DS Chốt (TT), cùng loại tiền CAD
    _bao_cao(bang_mkt, A, "2026-08-01", "SP1", hoa_don="8")
    result = activity_service.build(nguoi_dung["manager_mkt"], mkt_source, start=date(2026, 8, 1), end=date(2026, 8, 1))
    totals = dict(zip([c.label for c in result.columns], aggregations.total_values(result)))
    assert totals["DS Chốt (TT)"] == 100 and totals["Hóa đơn/DS Chốt (TT)"] == Decimal("0.08")
    # Vận đơn USD của cùng marketer: marketer chưa có báo cáo USD ngày đó → không vào dòng CAD, không quy đổi
    row = DataRecord.objects.create(table=van_don["table"], department=van_don["table"].department,
                                    created_by=nguoi_dung["admin"], val_date=date(2026, 8, 1),
                                    data={"ngay": "2026-08-01", "quoc_gia": "Hoa Kỳ", "loai_tien": "USD"})
    WaybillAssignment.objects.create(record=row, marketing=A)
    WaybillItem.objects.create(record=row, product=van_don["sp1"], quantity=1, unit_price="10.00", paid_amount="7.00")
    result = activity_service.build(nguoi_dung["manager_mkt"], mkt_source, start=date(2026, 8, 1), end=date(2026, 8, 1))
    assert not result.currency_warning
    totals = dict(zip([c.label for c in result.columns], aggregations.total_values(result)))
    assert totals["DS Chốt (TT)"] == 100 and totals["CPQC"] == 3 and totals["Số đơn (TT)"] == 2
    # Marketer nộp thêm báo cáo Hoa Kỳ (USD) cùng ngày → đơn USD vào dòng USD; mỗi loại tiền một dòng tổng
    ban_ghi = _bao_cao(bang_mkt, A, "2026-08-01", "SP1", mess=4, cpqc="2", hoa_don="1")
    ban_ghi.data |= {"thi_truong": "Hoa Kỳ", "loai_tien": "USD"}
    ban_ghi.save()
    result = activity_service.build(nguoi_dung["manager_mkt"], mkt_source, start=date(2026, 8, 1), end=date(2026, 8, 1))
    theo_tien = {tien: dict(zip([c.label for c in result.columns], raw)) for tien, raw in aggregations.total_rows(result)}
    assert list(theo_tien) == ["USD", "CAD"]
    assert theo_tien["CAD"]["DS Chốt (TT)"] == 100 and theo_tien["CAD"]["Số đơn (TT)"] == 2 and theo_tien["CAD"]["CPQC"] == 3
    assert theo_tien["USD"]["DS Chốt (TT)"] == 7 and theo_tien["USD"]["Số đơn (TT)"] == 1 and theo_tien["USD"]["CPQC"] == 2
    assert theo_tien["USD"]["Hóa đơn/DS Chốt (TT)"] == Decimal(1) / Decimal(7)
    # Tổng chung: không cộng tiền hai loại, vẫn đếm đủ
    totals = dict(zip([c.label for c in result.columns], aggregations.total_values(result)))
    assert totals["DS Chốt (TT)"] is None and totals["CPQC"] is None and totals["Hóa đơn/DS Chốt (TT)"] is None
    assert totals["Số Mess"] == 14 and totals["Số đơn (TT)"] == 3
