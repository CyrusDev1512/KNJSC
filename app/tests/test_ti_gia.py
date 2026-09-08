"""Tỉ giá đọc từ môi trường — `EXCHANGE_RATES_VND`, backlog N11.

Số sai lặng lẽ ("25.400" thành 25,4) là số sai vào sổ sao — sổ chỉ ghi thêm,
không xoá — nên định dạng phải được kiểm ngay lúc khởi động.
"""
from decimal import Decimal

import pytest

from knjsc.settings.base import env_rates


def test_ti_gia_doc_tu_moi_truong(monkeypatch):
    """docs/05 B10 — `EXCHANGE_RATES_VND` đọc dạng `USD=25400,CAD=18500` (số nguyên VND); sai định dạng thì báo rõ ngay lúc khởi động thay vì đưa số sai vào bảng xếp hạng"""
    monkeypatch.setenv("TI_GIA_THU", "usd=26000, cad=18000")
    assert env_rates("TI_GIA_THU", {"USD": Decimal("1"), "PHP": Decimal("440")}) == {
        "USD": Decimal("26000"), "CAD": Decimal("18000"), "PHP": Decimal("440"), "VND": Decimal("1"),
    }
    monkeypatch.delenv("TI_GIA_THU")
    assert env_rates("TI_GIA_THU", {"USD": Decimal("25400")})["USD"] == Decimal("25400")
    for xau in ("USD=25.400", "USD=25,400", "USD=abc", "USD", "USD=0", "U$D=1", "USD=-5"):
        monkeypatch.setenv("TI_GIA_THU", xau)
        with pytest.raises(RuntimeError):
            env_rates("TI_GIA_THU", {})
