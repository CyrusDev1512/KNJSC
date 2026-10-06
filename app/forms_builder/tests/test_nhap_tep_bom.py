"""Tệp nhập nhỏ mà giải nén ra khổng lồ bị từ chối trước khi đọc — AC-7.15 (săn lỗi bảo mật 06.10.2026).

Đo được: tệp .xlsx 220 KB (một dòng 2 triệu ô) qua đủ kiểm tra cũ (dưới 10 MB, đúng chữ ký Excel) rồi làm máy chủ
ăn 1,85 GB RAM và 68 giây CPU khi đọc — VPS 4 GB cho năm container là sập. Nay trước khi openpyxl đọc: tổng dung
lượng giải nén có trần, và mỗi dòng của sheet được đếm ô bằng cách đọc dòng chảy (không nạp cả dòng) — quá trần cột
thì từ chối ngay. CSV cũng có trần cột. Tệp thật (vài chục cột, vài nghìn dòng) không bị ảnh hưởng.
"""
import io
import time
import zipfile

import pytest
from openpyxl import Workbook

from core import excel
from core.constants import IMPORT_MAX_COLUMNS
from core.exceptions import BusinessError


def _xlsx_mot_dong(so_o):
    """Tệp .xlsx thật nhưng dòng 1 có `so_o` ô — dựng thẳng XML, tệp nén rất nhỏ."""
    wb = Workbook()
    wb.active.append(["A"])
    goc = io.BytesIO()
    wb.save(goc)
    src = zipfile.ZipFile(io.BytesIO(goc.getvalue()))
    out = io.BytesIO()
    o = b'<c t="inlineStr"><is><t>x</t></is></c>'
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == "xl/worksheets/sheet1.xml":
                data = (b'<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/'
                        b'spreadsheetml/2006/main"><sheetData><row r="1">' + o * so_o + b"</row></sheetData></worksheet>")
            z.writestr(item, data)
    return io.BytesIO(out.getvalue())


def _xlsx_that(so_cot=40, so_dong=500):
    wb = Workbook()
    for r in range(so_dong):
        wb.active.append([f"Ô {r}-{c}" for c in range(so_cot)])
    b = io.BytesIO()
    wb.save(b)
    b.seek(0)
    return b


def test_xlsx_mot_dong_qua_nhieu_o_bi_tu_choi_ngay():
    """AC-7.15 — Tệp .xlsx có dòng vượt trần cột (bom: tệp nhỏ, một dòng hàng trăm nghìn ô) bị từ chối với lời tiếng Việt trước khi đọc vào bộ nhớ, trong vài giây"""
    t = time.time()
    with pytest.raises(BusinessError, match="cột"):
        excel.read_table(_xlsx_mot_dong(300_000), "xlsx", max_rows=10)
    assert time.time() - t < 10


def test_xlsx_giai_nen_qua_lon_bi_tu_choi(monkeypatch):
    """AC-7.15 — Tổng dung lượng giải nén vượt trần thì từ chối, kể cả khi số cột hợp lệ"""
    monkeypatch.setattr(excel, "XLSX_MAX_UNCOMPRESSED_BYTES", 50_000)
    with pytest.raises(BusinessError, match="giải nén"):
        excel.read_table(_xlsx_that(so_cot=10, so_dong=2_000), "xlsx", max_rows=10)


def test_csv_dong_qua_nhieu_cot_bi_tu_choi():
    """AC-7.15 — CSV có dòng vượt trần cột cũng bị từ chối"""
    csv = io.BytesIO(("," * (IMPORT_MAX_COLUMNS + 5) + "\n").encode())
    with pytest.raises(BusinessError, match="cột"):
        excel.read_table(csv, "csv", max_rows=10)


def test_tep_that_van_doc_duoc():
    """AC-7.15 — Tệp .xlsx thật 40 cột × 500 dòng và CSV thường vẫn đọc được như cũ"""
    kq = excel.read_table(_xlsx_that(), "xlsx", max_rows=1_000)
    assert len(kq.rows) == 500 and len(kq.rows[0]) == 40
    kq = excel.read_table(io.BytesIO("Tên,SĐT\nA,1\n".encode()), "csv", max_rows=10)
    assert kq.rows[0] == ["Tên", "SĐT"]
