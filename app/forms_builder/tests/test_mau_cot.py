"""Màu cột và ngưỡng cảnh báo trên Bảng dữ liệu — FR-8.8, Q60.

Bước 1 kiểm phần định nghĩa trong Sửa cột; phần hiển thị kiểm ở các bài
thêm sau trong cùng tệp.
"""
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from forms_builder.forms import ColumnForm
from forms_builder.meaning import FieldType
from forms_builder.models import AlertOp, ColumnDef, ComputeOp, Highlight, TableDef
from forms_builder.services import table_service

pytestmark = pytest.mark.django_db


@pytest.fixture
def bang_mkt(departments, nguoi_dung):
    bang = TableDef.objects.create(
        name="Chi phí Ads", code="chi_phi_ads",
        department=departments["mkt"], created_by=nguoi_dung["manager_mkt"],
    )
    ColumnDef.objects.create(table=bang, name="Marketer", code="marketer", field_type=FieldType.TEXT, order=0)
    ColumnDef.objects.create(table=bang, name="CPQC", code="cpqc", field_type=FieldType.MONEY, order=1)
    ColumnDef.objects.create(table=bang, name="Số đơn", code="so_don", field_type=FieldType.INTEGER, order=2)
    return bang


def test_nguong_chi_nhan_cot_so(bang_mkt):
    """AC-8.9 — Ngưỡng cảnh báo chỉ đặt được cho cột kiểu số, và phải đủ cả chiều lẫn ngưỡng"""
    chu = ColumnDef(
        table=bang_mkt, name="Ghi chú", code="ghi_chu", field_type=FieldType.TEXT,
        alert_op=AlertOp.GT, alert_value=Decimal("100"),
    )
    with pytest.raises(ValidationError) as loi:
        chu.full_clean()
    assert "alert_op" in loi.value.message_dict

    thieu_nguong = ColumnDef(
        table=bang_mkt, name="CPO", code="cpo", field_type=FieldType.MONEY, alert_op=AlertOp.GT,
    )
    with pytest.raises(ValidationError) as loi:
        thieu_nguong.full_clean()
    assert "alert_value" in loi.value.message_dict

    # Cột tính sẵn kiểu tiền đặt được ngưỡng — đúng chỗ CPO trong ảnh của người dùng
    cpo = table_service.add_column(
        bang_mkt, name="CPO", code="cpo", field_type=FieldType.MONEY,
        is_computed=True, compute_op=ComputeOp.DIVIDE,
        compute_left="cpqc", compute_right="so_don", compute_decimals=0,
        alert_op=AlertOp.GT, alert_value=Decimal("1500000"), highlight=Highlight.DO,
    )
    cpo.refresh_from_db()
    assert cpo.alert_op == AlertOp.GT and cpo.alert_value == Decimal("1500000")
    assert cpo.highlight == Highlight.DO


def test_sua_cot_luu_mau_va_nguong(bang_mkt, nguoi_dung):
    """AC-8.9 — Manager đặt màu cột và ngưỡng trong Sửa cột, lưu và mở lại thấy đúng"""
    cot = bang_mkt.columns.get(code="cpqc")
    form = ColumnForm({
        "name": "CPQC", "code": "cpqc", "field_type": FieldType.MONEY, "meaning": "",
        "order": 1, "compute_decimals": 2, "highlight": Highlight.VANG,
        "alert_op": AlertOp.LT, "alert_value": "50000",
    }, instance=cot, table=bang_mkt)
    assert form.is_valid(), form.errors
    table_service.update_column(
        ColumnDef.objects.get(pk=cot.pk), form.cleaned_data, actor=nguoi_dung["manager_mkt"],
    )
    cot.refresh_from_db()
    assert (cot.highlight, cot.alert_op, cot.alert_value) == (
        Highlight.VANG, AlertOp.LT, Decimal("50000.00"))

    # Bỏ cảnh báo: gửi rỗng cả hai
    form = ColumnForm({
        "name": "CPQC", "code": "cpqc", "field_type": FieldType.MONEY, "meaning": "",
        "order": 1, "compute_decimals": 2, "highlight": "", "alert_op": "", "alert_value": "",
    }, instance=ColumnDef.objects.get(pk=cot.pk), table=bang_mkt)
    assert form.is_valid(), form.errors
    table_service.update_column(ColumnDef.objects.get(pk=cot.pk), form.cleaned_data)
    cot.refresh_from_db()
    assert cot.highlight == "" and cot.alert_op == "" and cot.alert_value is None


# ══ Hiển thị: lớp CSS của cột và ô ═══════════════════════════════════

def test_lop_css_theo_nguong(bang_mkt):
    """AC-8.9 — Ô vượt ngưỡng mang lớp đỏ, ô đạt mang lớp xanh, ô trống hay không phải số thì không tô"""
    from forms_builder import styling

    cot = ColumnDef(
        table=bang_mkt, name="CPO", code="cpo", field_type=FieldType.MONEY,
        alert_op=AlertOp.GT, alert_value=Decimal("100"), highlight=Highlight.VANG,
    )
    assert styling.alert_class(cot, "150") == "o-vuot-nguong"
    assert styling.alert_class(cot, "100") == "o-dat-nguong"
    assert styling.alert_class(cot, "50") == "o-dat-nguong"
    assert styling.alert_class(cot, "") == "" and styling.alert_class(cot, None) == ""
    assert styling.alert_class(cot, "chữ") == ""

    cot.alert_op = AlertOp.LT
    assert styling.alert_class(cot, "50") == "o-vuot-nguong"
    assert styling.alert_class(cot, "150") == "o-dat-nguong"

    assert styling.column_class(cot) == "cot-nen-vang"
    assert styling.cell_class(cot, "150") == "cot-nen-vang o-dat-nguong"
    assert styling.cell_class(cot, "") == "cot-nen-vang"        # ô trống: chỉ màu cột

    cot.alert_op, cot.alert_value, cot.highlight = "", None, ""
    assert styling.cell_class(cot, "150") == ""


def test_manager_dat_mau_va_nguong_roi_bang_hien_dung(client, bang_mkt, nguoi_dung):
    """AC-8.9 — Manager đặt màu cột và ngưỡng trong Sửa cột; tiêu đề và ô mang màu, ô vượt ngưỡng đỏ, ô đạt xanh, ô trống không tô"""
    from forms_builder.services import record_service

    ql = nguoi_dung["manager_mkt"]
    cot = bang_mkt.columns.get(code="cpqc")
    client.force_login(ql)
    kq = client.post(f"/bang/chi_phi_ads/cot/?cot={cot.pk}", {
        "name": "CPQC", "code": "cpqc", "field_type": FieldType.MONEY, "meaning": "",
        "order": 1, "compute_decimals": 2,
        "highlight": Highlight.VANG, "alert_op": AlertOp.GT, "alert_value": "100",
    })
    assert kq.status_code in (200, 302), kq.content[:300]
    cot.refresh_from_db()
    assert (cot.highlight, cot.alert_op, cot.alert_value) == (Highlight.VANG, AlertOp.GT, Decimal("100"))

    record_service.create_record(bang_mkt, {"marketer": "A", "cpqc": "150", "so_don": 1}, actor=ql)
    record_service.create_record(bang_mkt, {"marketer": "B", "cpqc": "50", "so_don": 1}, actor=ql)
    record_service.create_record(bang_mkt, {"marketer": "C", "so_don": 1}, actor=ql)

    html = client.get("/bang/chi_phi_ads/").content.decode()
    assert '<table class="bang bang-luoi">' in html
    assert '<th class="sap-xep cot-nen-vang' in html
    assert html.count('class="cot-nen-vang o-vuot-nguong"') == 1
    assert html.count('class="cot-nen-vang o-dat-nguong"') == 1
    assert html.count('class="cot-nen-vang"') == 1                # ô trống: chỉ màu cột
    assert 'class="o-sua' not in html                            # chỉ xem — ADR-014


def test_bao_cao_xem_mang_lop_mau(client, bang_mkt, departments, nguoi_dung):
    """AC-8.9 — Màn hình xem báo cáo cũng mang màu cột và lớp cảnh báo của bảng đích"""
    from datetime import date

    from forms_builder.models import FieldDef
    from forms_builder.services import form_service, table_service
    from reports.services import daily_service

    ql = nguoi_dung["manager_mkt"]
    table_service.update_column(
        bang_mkt.columns.get(code="cpqc"),
        {"highlight": Highlight.DO, "alert_op": AlertOp.LT, "alert_value": Decimal("1000")}, actor=ql,
    )
    bm = form_service.create_form(
        name="Chi phí ngày", code="chi_phi_ngay", department=departments["mkt"], table=bang_mkt, actor=ql)
    for ma in ("marketer", "cpqc", "so_don"):
        cot = bang_mkt.columns.get(code=ma)
        truong = FieldDef.objects.create(
            name=cot.name, code=ma, field_type=cot.field_type, department=departments["mkt"])
        form_service.add_field(bm, truong, column=cot, actor=ql)
    bao_cao = daily_service.submit(
        bm, {"marketer": "A", "cpqc": "500", "so_don": "2"}, report_date=date(2026, 9, 1), actor=ql)

    client.force_login(ql)
    html = client.get(f"/bao-cao/{bao_cao.pk}/").content.decode()
    assert '<table class="bang bang-luoi">' in html
    assert 'class="cot-nen-do o-vuot-nguong phai tien"' in html


def test_lop_luoi_va_mau_co_that_trong_css():
    """FR-8.9 — Các lớp do styling sinh ra và lớp lưới đều có thật trong main.css (bài quét template không thấy được chúng)"""
    import re
    from pathlib import Path

    from forms_builder import styling

    css = (Path(__file__).resolve().parents[2] / "static" / "css" / "main.css").read_text(encoding="utf-8")
    da_khai = set(re.findall(r"\.([a-zA-Z][\w-]*)", css))
    can = {"bang-luoi", styling.ALERT_HIT, styling.ALERT_OK, *styling.HIGHLIGHT_CLASSES.values()}
    assert can <= da_khai, can - da_khai
