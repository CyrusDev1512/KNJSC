"""Ô ngày trong tệp Excel lưu dạng số (số ngày kể từ 30/12/1899) vẫn nhập được — AC-7.16 (06.10.2026).

Ô ngày mất định dạng (dán giá trị, cột để General) openpyxl đọc ra số, vd 45000 thay vì 15/03/2023; trước đây cột
Ngày từ chối cả dòng "không đúng kiểu Ngày". Chỉ đổi khi ô là **số thật** của Excel trong cột kiểu Ngày; chữ "45000"
gõ tay vẫn bị từ chối như cũ, không đoán.
"""
from datetime import date

import pytest

from core.exceptions import BusinessError
from forms_builder.meaning import FieldType
from forms_builder.models import ColumnDef
from forms_builder.services.record_service import parse_value


def _cot():
    return ColumnDef(name="Ngày", code="ngay", field_type=FieldType.DATE)


def test_so_serial_excel_thanh_ngay():
    """AC-7.16 — Cột Ngày nhận số serial của Excel: 45000 → 2023-03-15, 45000.75 (có giờ) → 2023-03-15, 1 → 1899-12-31"""
    assert parse_value(_cot(), 45000) == "2023-03-15" == date(2023, 3, 15).isoformat()
    assert parse_value(_cot(), 45000.75) == "2023-03-15"
    assert parse_value(_cot(), 1) == "1899-12-31"


def test_chu_so_va_so_vo_ly_van_bi_tu_choi():
    """AC-7.16 — Chữ "45000", số âm, số 0 và số quá lớn ở cột Ngày vẫn bị từ chối với lời tiếng Việt; True/False không
    bị coi là số"""
    for gia_tri in ("45000", -5, 0, 10**7, True):
        with pytest.raises(BusinessError, match="Ngày"):
            parse_value(_cot(), gia_tri)
