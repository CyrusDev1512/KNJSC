"""Đọc lại chuỗi số do máy gửi — TL-03 · P0-3 (ADR-052).

Số tiền lưu trong JSON dạng chuỗi máy: dấu chấm là thập phân ("0.125"). Trước đây mọi đường đưa chuỗi đó trở lại
(hoàn tác trên lưới, đổi kiểu cột, sửa nhãn cột Tiền) đều đi qua `parse_money` — bộ đọc chữ người Việt gõ, nơi
"0.125" là 125 (chấm ngăn nghìn). Chủ dự án chốt 13.10.2026: tách hai bộ đọc. Chuỗi máy đọc bằng
`parse_stored_number`: dấu chấm luôn là thập phân. Chữ người gõ giữ luật Việt: "1.234" là 1234.
"""
import random
from decimal import Decimal, InvalidOperation

import pytest

from core.exceptions import BusinessError
from core.money import MONEY_MAX_INTEGER_DIGITS, parse_money
from forms_builder.meaning import FieldType
from forms_builder.models import ColumnDef
from forms_builder.services.record_service import parse_value

#: (chuỗi máy, giá trị) — str(kết quả) phải đúng bằng chuỗi vào để ô "không đổi" nhận ra là không đổi
MAY = [("0.125", "0.125"), ("12.345", "12.345"), ("1234.567", "1234.567"), ("150.00", "150.00"),
       ("-0.5", "-0.5"), ("1E-7", "1E-7"), ("9999999999999999.99", "9999999999999999.99"), ("438446060", "438446060")]
#: Chuỗi máy không bao giờ có: nhóm nghìn, phẩy, số mũ dương, chữ — gửi tới là lỗi, không đoán
MAY_TU_CHOI = ["10000000000000000", "1.234,56", "1,5", "1.234.5", "NaN", "Infinity", "1e5x", "1e5", "1E+5",
               "abc", "", " "]
#: (chữ người gõ, giá trị) — luật Việt giữ nguyên (Bước 1 không siết chữ người gõ)
NGUOI = [("1.234", "1234"), ("1.234,56", "1234.56"), ("-5.000", "-5000"), ("1,234.5", "1234.5"),
         ("1 234 ₫", "1234"), ("150.00", "150.00"), ("12.345", "12345"), ("12,345", "12.345"), ("0,125", "0.125")]


def test_bang_chan_ly_doc_so_may_va_nguoi_go():
    """AC-9.7 — Hai bộ đọc số tách bạch: chuỗi máy ("0.125") đọc dấu chấm là thập phân, giữ nguyên dạng chuỗi;
    chuỗi máy sai dạng bị từ chối; chữ người gõ vẫn theo luật Việt ("1.234" = 1234) — TL-03"""
    from core.money import parse_stored_number

    for chuoi, ky_vong in MAY:
        so = parse_stored_number(chuoi)
        assert so == Decimal(ky_vong) and str(so) == ky_vong, chuoi
    for chuoi in MAY_TU_CHOI:
        with pytest.raises((InvalidOperation, BusinessError)):
            parse_stored_number(chuoi)
    assert parse_stored_number(Decimal("0.125")) == Decimal("0.125")
    assert parse_stored_number(5) == Decimal(5) and parse_stored_number(0.5) == Decimal("0.5")
    with pytest.raises(InvalidOperation):
        parse_stored_number(True)
    for chuoi, ky_vong in NGUOI:
        assert parse_money(chuoi) == Decimal(ky_vong), chuoi


def test_khu_hoi_chuoi_may_doc_lai_tu_co_so_du_lieu():
    """AC-9.7 — Mọi số tiền đã lưu đọc lại bằng bộ đọc chuỗi máy ra đúng số và đúng chuỗi đã lưu (5.000 số ngẫu
    nhiên, cả dạng số mũ "1E-7"), nên ô Tiền/Số thập phân ghi lại nguyên trạng — không nhân nghìn (TL-03)"""
    from core.money import parse_stored_number

    rng = random.Random(20261013)
    cot = [ColumnDef(name="Tiền", code="tien", field_type=FieldType.MONEY),
           ColumnDef(name="Số", code="so", field_type=FieldType.DECIMAL)]
    for _ in range(5000):
        nguyen = str(rng.randint(0, 10 ** rng.randint(0, MONEY_MAX_INTEGER_DIGITS) - 1))
        le = "".join(rng.choice("0123456789") for _ in range(rng.randint(0, 10)))
        d = Decimal(rng.choice(["", "-"]) + nguyen + ("." + le if le else ""))
        if rng.random() < 0.05:
            d = Decimal((0, (rng.randint(1, 9),), -rng.randint(7, 12)))     # 1E-7 … dạng str() có số mũ
        s = str(d)
        assert str(parse_stored_number(s)) == s, s
        for c in cot:
            assert parse_value(c, parse_stored_number(s)) == s, (c.field_type, s)
