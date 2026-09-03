"""Nhập hàng loạt vào bảng động — nền của nhập tệp Excel và sinh dữ liệu đo.

Kiểm ở mức dịch vụ: đúng số dòng, dòng lỗi không chặn dòng sau, cột tách và
cột tính sẵn được điền dù đi qua `bulk_create` (không gọi `save()`), và cả
lượt chỉ tốn vài lệnh truy vấn cộng đúng một dòng nhật ký.
"""
from decimal import Decimal

import pytest

from core.constants import AuditAction
from core.exceptions import BusinessError
from core.models import AuditLog
from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, ComputeOp, DataRecord, TableDef
from forms_builder.services import record_service

pytestmark = pytest.mark.django_db


@pytest.fixture
def bang(departments, nguoi_dung):
    b = TableDef.objects.create(
        name="Đơn hàng", code="don_bulk",
        department=departments["sale"], created_by=nguoi_dung["manager_sale"],
    )
    cot = [
        ("Ngày", "ngay", FieldType.DATE, Meaning.DATE, False),
        ("Khách hàng", "khach", FieldType.TEXT, Meaning.CUSTOMER, True),
        ("Doanh thu", "doanh_thu", FieldType.MONEY, Meaning.REVENUE, False),
        ("Số lượng", "so_luong", FieldType.INTEGER, "", False),
    ]
    for i, (ten, ma, kieu, nhan, bat_buoc) in enumerate(cot):
        ColumnDef.objects.create(
            table=b, name=ten, code=ma, field_type=kieu, meaning=nhan,
            required=bat_buoc, order=i,
        )
    ColumnDef.objects.create(
        table=b, name="Giá đơn vị", code="gia_dv", field_type=FieldType.MONEY, order=4,
        is_computed=True, compute_op=ComputeOp.DIVIDE,
        compute_left="doanh_thu", compute_right="so_luong", compute_decimals=2,
    )
    return b


def _dong(n, tu=1):
    return [
        {"ngay": "2026-08-01", "khach": f"K{i}", "doanh_thu": str(100 * i), "so_luong": i}
        for i in range(tu, tu + n)
    ]


def test_nhap_1000_dong_it_truy_van_mot_nhat_ky(bang, nguoi_dung, django_assert_max_num_queries):
    """AC-10.2 — Nhập 1.000 dòng tốn không quá 10 lệnh truy vấn và một dòng nhật ký

    Không có `bulk_create` thì 1.000 dòng là 1.000 INSERT cộng 1.000 dòng
    nhật ký — vừa chậm (NFR-3) vừa che mất mọi thứ khác trong nhật ký.
    """
    cot = list(bang.columns.all())
    truoc = AuditLog.objects.filter(action=AuditAction.IMPORT).count()
    with django_assert_max_num_queries(10):
        kq = record_service.create_records_bulk(
            bang, _dong(1000), actor=nguoi_dung["manager_sale"], columns=cot,
        )
    assert kq.created == 1000 and kq.errors == []
    assert DataRecord.objects.filter(table=bang).count() == 1000
    assert AuditLog.objects.filter(action=AuditAction.IMPORT).count() == truoc + 1
    assert "1000 dòng" in AuditLog.objects.filter(action=AuditAction.IMPORT).latest("created_at").detail


def test_dong_loi_khong_chan_dong_hop_le(bang, nguoi_dung):
    """AC-7.6 — Tệp Excel có dòng lỗi thì các dòng hợp lệ vẫn được nhập, dòng lỗi được liệt kê"""
    dong = _dong(5)
    dong[1]["doanh_thu"] = "abc"          # tiền không đọc được
    del dong[3]["khach"]                  # thiếu cột bắt buộc
    kq = record_service.create_records_bulk(
        bang, dong, actor=nguoi_dung["manager_sale"], row_numbers=[4, 5, 6, 7, 8],
    )
    assert kq.created == 3
    assert [so for so, _ in kq.errors] == [5, 7]
    assert "Doanh thu" in kq.errors[0][1]
    assert "Khách hàng" in kq.errors[1][1]
    assert DataRecord.objects.filter(table=bang).count() == 3


def test_cot_tach_va_cot_tinh_duoc_dien_du_bulk(bang, nguoi_dung):
    """FR-7.2 — Sau khi nhập hàng loạt vẫn lọc được theo cột tách và cột tính sẵn có số

    `bulk_create` không gọi `save()`, nên nếu quên gọi tay `sync_indexed_columns`
    thì màn hình vẫn hiện đúng mà lọc và thống kê sai âm thầm.
    """
    record_service.create_records_bulk(bang, _dong(3), actor=nguoi_dung["manager_sale"])
    assert DataRecord.objects.filter(table=bang, val_customer="K2").count() == 1
    assert DataRecord.objects.filter(table=bang, val_revenue=Decimal("200")).count() == 1
    bg = DataRecord.objects.get(table=bang, val_customer="K2")
    assert bg.data["gia_dv"] == "100.00"
    assert bg.department_id == bang.department_id


def test_ep_kieu_so_tu_excel():
    """FR-7.5 — Số thật từ Excel nhận nguyên trạng, không đi qua tập quán dấu chấm

    Bản đầu đưa `1234.567` qua `parse_money` và nhận về 1.234.567 — sai 1.000 lần.
    """
    tien = ColumnDef(name="Tiền", code="t", field_type=FieldType.MONEY)
    so = ColumnDef(name="Số", code="s", field_type=FieldType.INTEGER)
    chu = ColumnDef(name="Chữ", code="c", field_type=FieldType.TEXT)
    assert record_service.parse_value(tien, 1234.567) == "1234.567"
    assert record_service.parse_value(tien, 218.0) == "218.0"
    assert record_service.parse_value(tien, "1.234,56") == "1234.56"   # chuỗi vẫn theo tập quán VN
    assert record_service.parse_value(so, 3.0) == 3
    assert record_service.parse_value(so, "1.000") == 1000
    assert record_service.parse_value(chu, 7788599010.0) == "7788599010"
    with pytest.raises(BusinessError):
        record_service.parse_value(so, 3.5)
