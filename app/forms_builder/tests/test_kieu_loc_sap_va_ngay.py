"""TL-04/09/10/32/120: lọc có kiểu, thứ tự ổn định, cột ngày chỉ mục nhận ngày giờ."""
from datetime import date
from decimal import Decimal

import pytest

from core.exceptions import BusinessError
from forms_builder import query
from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, DataRecord, TableDef
from forms_builder.services import record_service

pytestmark = pytest.mark.django_db


def test_loc_khoang_khong_nhan_chi_ky_hieu_tien():
    """AC-7.3 — Ký hiệu tiền không có con số phải báo lỗi bộ lọc, không gây lỗi ORM."""
    column = ColumnDef(name='Tiền', field_type='money')
    with pytest.raises(query.InvalidFilter):
        query._filter_value(column, 'val_revenue', '$', 'gte')


@pytest.fixture
def typed_table(nguoi_dung, departments):
    table = TableDef.objects.create(name="Bảng kiểu kiểm thử", code="typed-test",
                                   created_by=nguoi_dung["manager_sale"], department=departments["sale"])
    for code, kind, meaning in (("tien", FieldType.MONEY, ""), ("so", FieldType.DECIMAL, ""),
                               ("ngay", FieldType.DATE, Meaning.DATE), ("khach", FieldType.TEXT, "")):
        ColumnDef.objects.create(table=table, code=code, name=code, field_type=kind, meaning=meaning)
    rows = [record_service.create_record(table, {"tien": Decimal(v), "so": Decimal(v),
            "ngay": f"2026-10-{19+i:02d}", "khach": "Cùng tên"}, actor=nguoi_dung["manager_sale"])
            for i, v in enumerate(("1234.5", "50", "999"))]
    return table, rows


@pytest.mark.parametrize("code", ["tien", "so"])
def test_json_so_sap_xep_va_loc_khoang_theo_gia_tri(typed_table, code):
    """AC-7.3 — Tiền/số thập phân trong JSON so bằng numeric, không so chuỗi hoặc đổi khoảng thành bằng."""
    table, rows = typed_table
    qs, _ = query.build(DataRecord.objects.all(), table, sort=code, filters={code+"__lon_bang": "100"})
    assert list(qs.values_list("pk", flat=True)) == [rows[2].pk, rows[0].pk]


@pytest.mark.parametrize("filters,index", [({"tien__lon_bang": "1.000"}, 0),
                                         ({"ngay": "20/10/2026"}, 1),
                                         ({"so": "1.234,5"}, 0)])
def test_loc_dung_dinh_dang_nguoi_dung(typed_table, filters, index):
    """AC-10.16 — Chuỗi Việt trên bộ lọc phải thực sự lọc, không âm thầm lấy cả bảng."""
    table, rows = typed_table
    qs, _ = query.build(DataRecord.objects.all(), table, filters=filters)
    assert list(qs.values_list("pk", flat=True)) == [rows[index].pk]


@pytest.mark.parametrize("value", ["abc", "1e200000", "NaN", "Infinity"])
def test_loc_so_sai_bi_chan(typed_table, value):
    """AC-10.16 — Từ chối bộ lọc số sai trước SQL, không bỏ lọc hoặc trả HTML 500."""
    with pytest.raises(BusinessError):
        query.build(DataRecord.objects.all(), typed_table[0], filters={"tien__lon_bang": value})


def test_sap_bang_khong_van_don_co_khoa_phan_trang(typed_table):
    """AC-7.3 — Hai giá trị trùng phải có thứ tự ID ổn định qua phân trang ERP."""
    qs, _ = query.build(DataRecord.objects.all(), typed_table[0], sort="khach")
    assert qs.query.order_by[-1] in ("pk", "id")
    assert list(qs.values_list("pk", flat=True)) == [r.pk for r in typed_table[1]]


def test_ngay_gio_mang_nhan_ngay_khong_loi(typed_table, nguoi_dung):
    """AC-8.2 — Ngày giờ giữ nguyên JSON; chỉ mục Ngày lấy ngày theo múi giờ Việt Nam."""
    table, _ = typed_table
    table.columns.filter(code="ngay").update(field_type=FieldType.DATETIME)
    row = record_service.create_record(table, {"ngay": "2026-10-19T18:30:00+00:00"}, actor=nguoi_dung["manager_sale"])
    row.refresh_from_db()
    assert row.val_date == date(2026, 10, 20)
    assert row.data["ngay"] == "2026-10-19T18:30:00+00:00"


def test_danh_sach_so_may_khong_nhan_nghin_va_so_rat_nho_khong_lam_tron(typed_table):
    """AC-9.7 — Chọn giá trị 0.125 từ bộ lọc danh sách phải giữ 0,125; không lượng tử hoá khi CAST."""
    table, rows = typed_table
    for row, value in zip(rows, ("0.125", "1E-7", "NaN")):
        DataRecord.objects.filter(pk=row.pk).update(data={"tien": value})
    qs, _ = query.build(DataRecord.objects.all(), table, filters={"tien__trong": ["0.125"]})
    assert list(qs.values_list("pk", flat=True)) == [rows[0].pk]
    qs, _ = query.build(DataRecord.objects.all(), table, filters={"tien__lon_bang": "0"}, sort="tien")
    assert list(qs.values_list("pk", flat=True)) == [rows[1].pk, rows[0].pk]


def test_json_luu_cu_khong_hop_le_khong_lam_hong_loc(typed_table):
    """AC-10.16 — Chữ cũ/ô rỗng trong cột tiền không làm CAST lỗi hoặc lọt vào khoảng số."""
    table, rows = typed_table
    for row, value in zip(rows, ("abc", "", "999")):
        DataRecord.objects.filter(pk=row.pk).update(data={"tien": value})
    qs, _ = query.build(DataRecord.objects.all(), table, filters={"tien__lon_bang": "100"}, sort="tien")
    assert list(qs.values_list("pk", flat=True)) == [rows[2].pk]
