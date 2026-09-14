from io import StringIO

import pytest
from django.core.management import call_command

from forms_builder.models import DataRecord, TableDef


pytestmark = pytest.mark.django_db


EXPECTED_COLUMN_CODES = [
    "ngay",
    "dia_chi",
    "thanh_pho",
    "bang",
    "quoc_gia",
    "zipcode",
    "so_dien_thoai",
    "san_pham",
    "so_luong",
    "gia_tien",
    "loai_tien",
    "pttt",
    "nguoi_ban",
    "phu_trach_cskh",
    "phu_trach_mkt",
    "phu_trach_vd",
    "ma_don",
    "trang_thai_vc",
    "ngay_tt",
    "ten_khach",
    "so_tien_tt",
    "bill",
    "ghi_chu",
    "trang_thai_tt",
    "pttt_thuc_te",
    "doi_soat",
]


def test_lenh_tao_bang_van_don_khoi_phuc_van_don_db_tren_may_sach(db):
    """AC-18.9 — Máy sạch luôn có Vận đơn DB đúng 26 cột và chạy lại không trùng."""
    output = StringIO()

    call_command("tao_bang_van_don", stdout=output)
    assert TableDef.all_objects.filter(code="van_don_db").count() == 1
    table = TableDef.all_objects.get(code="van_don_db")
    assert table.records.count() == 0
    row = DataRecord.all_objects.create(
        table=table,
        department=table.department,
        data={"ma_don": "DB-001"},
    )

    call_command("tao_bang_van_don", stdout=output)

    assert table.name == "Vận đơn DB"
    assert table.department.code == "van-don"
    assert table.is_shared is False
    assert list(table.columns.order_by("order", "id").values_list("code", flat=True)) == (
        EXPECTED_COLUMN_CODES
    )
    assert list(table.records.values_list("pk", "data")) == [
        (row.pk, {"ma_don": "DB-001"})
    ]
    assert "van_don_db" in output.getvalue()

    payment_codes = EXPECTED_COLUMN_CODES[18:23]
    assert payment_codes == ["ngay_tt", "ten_khach", "so_tien_tt", "bill", "ghi_chu"]
    assert table.columns.get(code="ngay_tt").name == "Ngày thanh toán"
    assert table.columns.get(code="ma_don").is_key is True
    assert table.columns.get(code="loai_tien").required is True
