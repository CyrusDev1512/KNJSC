"""Màu cột và ngưỡng cảnh báo trên Bảng dữ liệu — FR-8.8, Q56.

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
