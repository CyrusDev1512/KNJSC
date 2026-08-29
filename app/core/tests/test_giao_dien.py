"""Kiểm thử giao diện ở mức tệp — bắt những lỗi mà kiểm thử HTTP không thấy.

Django không quan tâm lớp CSS trong template có tồn tại thật hay không: gõ sai
tên lớp thì trang vẫn trả về 200 và mọi bài kiểm thử vẫn xanh, chỉ có người
dùng nhìn thấy giao diện hỏng.

Đã xảy ra thật: bốn màn hình dùng lớp `.luoi-2cot` chưa bao giờ được định
nghĩa, nên hiện một cột thay vì hai suốt từ Giai đoạn 3 tới Giai đoạn 5 mà
218 bài kiểm thử vẫn xanh. Backlog K15.

Tệp này không cần cơ sở dữ liệu — nó đọc tệp, không chạy Django.
"""
import re
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent.parent
THU_MUC_TEMPLATE = GOC / "templates"
CAC_TEP_CSS = [GOC / "static" / "css" / "main.css", GOC / "static" / "css" / "tokens.css"]

#: Lớp chỉ dùng làm móc cho JavaScript, cố ý không có kiểu dáng.
#: Thêm vào đây phải kèm lý do, không phải chỗ để giấu lỗi gõ sai.
MOC_JAVASCRIPT = {
    "bo-dong", "dong-sp", "o-gia", "o-sl", "o-sp", "o-thanh-tien",   # bảng dòng sản phẩm
    "o-trong-bang",                                                   # ô sửa trên bảng
    "truong-muc",                                                     # danh sách trường
}

#: Mảnh cú pháp Django lọt vào thuộc tính class khi có điều kiện bên trong
CU_PHAP_DJANGO = re.compile(r"^(%\}|\{%|if|elif|else|endif|endfor|for|or|and|not|==|!=)$")


def _lop_trong_tep(duong_dan):
    """Mọi tên lớp xuất hiện trong thuộc tính class của một tệp."""
    noi_dung = duong_dan.read_text(encoding="utf-8")
    lop = set()
    for cum in re.findall(r'class="([^"]*)"', noi_dung):
        for ten in cum.split():
            ten = ten.strip()
            if not ten or ten.startswith("{") or ten.startswith("'"):
                continue
            if "." in ten or "{" in ten or "}" in ten:
                continue
            if CU_PHAP_DJANGO.match(ten):
                continue
            lop.add(ten)
    return lop


def _lop_da_khai():
    """Mọi tên lớp đã khai trong các tệp kiểu dáng dùng chung."""
    da_khai = set()
    for tep in CAC_TEP_CSS:
        da_khai |= set(re.findall(r"\.([a-zA-Z][\w-]*)", tep.read_text(encoding="utf-8")))
    return da_khai


def _lop_khai_trong_template(duong_dan):
    """Lớp khai ngay trong khối <style> của chính template đó."""
    noi_dung = duong_dan.read_text(encoding="utf-8")
    khoi = re.findall(r"<style>(.*?)</style>", noi_dung, re.DOTALL)
    return set(re.findall(r"\.([a-zA-Z][\w-]*)", " ".join(khoi)))


CAC_TEMPLATE = sorted(THU_MUC_TEMPLATE.rglob("*.html"))


def test_co_template_de_kiem():
    """Bài quét chỉ có nghĩa khi thật sự tìm thấy template"""
    assert len(CAC_TEMPLATE) >= 10


@pytest.mark.parametrize("tep", CAC_TEMPLATE, ids=lambda p: p.name)
def test_moi_lop_css_dung_trong_template_deu_ton_tai(tep):
    """K15 — Lớp CSS gõ trong template phải có thật trong tệp kiểu dáng

    Bài này đỏ nếu ai đó gõ sai tên lớp hoặc dùng lớp chưa được định nghĩa.
    Không có nó thì giao diện hỏng âm thầm, vì Django trả 200 như thường.
    """
    thieu = sorted(
        _lop_trong_tep(tep)
        - _lop_da_khai()
        - _lop_khai_trong_template(tep)
        - MOC_JAVASCRIPT
    )
    assert not thieu, (
        f"{tep.relative_to(GOC)} dùng lớp chưa được định nghĩa: {', '.join(thieu)}. "
        "Khai trong static/css/main.css, hoặc thêm vào MOC_JAVASCRIPT nếu chỉ "
        "dùng cho JavaScript."
    )
