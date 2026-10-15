"""Kịch bản đo tải `tests/perf/locustfile.py` chỉ ghi vào dòng giả `PERF-*` — TL-102 (đợt P0, 14.10.2026).

P0-16 đã khoá `do_hieu_nang` chỉ ghi dòng `PERF-*`; `locustfile.py` thì vai Vận đơn sửa ô trên mọi dòng mở được (đổi
trạng thái giao của vận đơn thật) và vai Sale lên đơn thật. Máy ảo không cài `locust`, nên bài nạp tệp với một mô-đun
`locust` giả và gọi thẳng từng việc với một client ghi lại yêu cầu.
"""
import importlib.util
import sys
import types
from pathlib import Path

import pytest

TEP = Path(__file__).resolve().parent / "perf" / "locustfile.py"


class _KetQua:
    text = ""

    def __init__(self, du_lieu=None, ma=200):
        self.status_code, self._du_lieu = ma, du_lieu or {}

    def json(self):
        return self._du_lieu


class _Client:
    """Client giả: ghi lại mọi GET/POST; GET trả `tra_ve`."""

    base_url = "http://may-thu"

    def __init__(self, tra_ve=None):
        self.goi, self.tra_ve, self.cookies = [], tra_ve or {}, {}

    def get(self, duong, params=None, **kw):
        self.goi.append(("GET", duong, params or {}))
        return _KetQua(self.tra_ve)

    def post(self, duong, data=None, json=None, **kw):
        self.goi.append(("POST", duong, json if json is not None else data))
        return _KetQua({"rows": []})


@pytest.fixture
def kich_ban(monkeypatch):
    gia = types.ModuleType("locust")
    gia.HttpUser = object
    gia.between = lambda *a: None
    gia.task = lambda *a: (a[0] if a and callable(a[0]) else (lambda f: f))
    gia.events = types.SimpleNamespace(quitting=types.SimpleNamespace(add_listener=lambda f: f))
    monkeypatch.setitem(sys.modules, "locust", gia)
    spec = importlib.util.spec_from_file_location("locustfile_tl102", TEP)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _dong(id_, ma_don):
    return {"id": id_, "cells": {"ma_don": {"value": ma_don},
                                 "trang_thai_vc": {"value": "Đang giao", "editable": True}}}


def test_vai_van_don_chi_mo_va_sua_dong_perf(kich_ban, monkeypatch):
    """TL-102 · Vai Vận đơn của locustfile.py chỉ lọc dòng `PERF-*` khi mở lưới và chỉ sửa ô của dòng `PERF-*`: có dòng
    vận đơn thật trong tay cũng không gửi lượt ghi nào vào đó"""
    u = object.__new__(kich_ban.NguoiVanDon)
    u.client = _Client(tra_ve={"rows": [_dong(1, "DH001"), _dong(2, "PERF-000002")]})
    u.mo_luoi()
    assert u.client.goi[0][2].get("f_ma_don__bat_dau") == "PERF-", u.client.goi[0]

    u.client = _Client()
    u.o = [_dong(1, "DH001")]
    for _ in range(20):
        u.sua_o()
    assert not [g for g in u.client.goi if g[0] == "POST"], "sửa ô vào vận đơn thật"

    u.o = [_dong(1, "DH001"), _dong(2, "PERF-000002")]
    for _ in range(20):
        u.sua_o()
    ghi = [g for g in u.client.goi if g[0] == "POST"]
    assert ghi and {c["id"] for g in ghi for c in g[2]["cells"]} == {2}


def test_vai_sale_khong_len_don_that_tru_khi_bat_co(kich_ban, monkeypatch):
    """TL-102 · Vai Sale của locustfile.py không lên đơn thật (đơn mới không mang mã `PERF-*`, `seed_perf --xoa` không
    dọn được) trừ khi người đo bật cờ `KNJSC_TAI_LEN_DON=1` cho máy thử"""
    u = object.__new__(kich_ban.NguoiSale)
    u.client = _Client()
    monkeypatch.delenv("KNJSC_TAI_LEN_DON", raising=False)
    u.len_don()
    assert not [g for g in u.client.goi if g[0] == "POST"]
    monkeypatch.setenv("KNJSC_TAI_LEN_DON", "1")
    u.len_don()
    assert [g for g in u.client.goi if g[0] == "POST" and g[1] == "/len-don/"]
