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
CAC_TEP_CSS = [
    GOC / "static" / "css" / "main.css", GOC / "static" / "css" / "tokens.css",
    GOC / "static" / "css" / "bang-tinh.css",
]

#: Lớp chỉ dùng làm móc cho JavaScript, cố ý không có kiểu dáng.
#: Thêm vào đây phải kèm lý do, không phải chỗ để giấu lỗi gõ sai.
MOC_JAVASCRIPT = {
    "bo-dong", "dong-sp", "o-gia", "o-sl", "o-sp", "o-thanh-tien",   # bảng dòng sản phẩm
    "o-trong-bang",                                                   # ô sửa trên bảng
    "truong-muc",                                                     # danh sách trường
    # Bảng tính (ADR-010): nút và ô chỉ để JS bắt, không có kiểu riêng
    "bt-tat-ca", "bt-them-dong", "bt-loc-o", "bt-an-cot", "bt-thu-ben",
    "bt-dinh-dang", "o-moi-nhap", "bt-dd", "bt-mo-mau", "bt-mau-bo", "bt-thu-muc-moi", "bt-dat-lai-cot",
    # Bảng tính theo mẫu KN Demo (ADR-011): nút ⋯ mở hộp "việc khác" — kiểu
    # dáng lấy từ .bt-tb, lớp này chỉ để JS biết mở hộp nào
    "bt-khac",
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


# ══ TRẢI NGHIỆM DÙNG ═══════════════════════════════════════════════
#
# Những lỗi dưới đây Django không bao giờ báo: trang vẫn trả 200, chỉ người
# dùng thấy giao diện khó dùng hoặc hỏng. Kiểm ở mức tệp vì không có thư viện
# trình duyệt nào trong dự án.

#: Trang không cần khối nội dung riêng, kèm lý do
KHONG_CAN_NOI_DUNG = {
    "base.html": "chính là bộ khung, không phải trang",
    "base_tran.html": "bộ khung trần cho trang chưa đăng nhập",
}

#: Loại ô nhập không cần nhãn
KHONG_CAN_NHAN = {"hidden", "submit", "button", "checkbox", "radio"}


def _mo_ta_tep(tep):
    return str(tep.relative_to(GOC))


@pytest.mark.parametrize("tep", CAC_TEMPLATE, ids=lambda p: p.name)
def test_moi_o_nhap_deu_co_nhan(tep):
    """NFR-7 — Mọi ô nhập phải có nhãn đi kèm

    Ô không nhãn thì người dùng không biết gõ gì vào, và trình đọc màn hình
    cũng không đọc được. Nhãn nối bằng `for` trỏ tới `id` của ô.
    """
    noi_dung = tep.read_text(encoding="utf-8")
    co_nhan = set(re.findall(r'<label[^>]*\bfor="([^"]+)"', noi_dung))

    thieu = []
    for the in re.findall(r"<(?:input|select|textarea)\b[^>]*>", noi_dung):
        loai = re.search(r'\btype="([^"]+)"', the)
        if loai and loai.group(1) in KHONG_CAN_NHAN:
            continue
        if "aria-label" in the or "{{ truong" in the:
            continue                        # Django tự sinh nhãn ở vòng lặp form
        ma = re.search(r'\bid="([^"]+)"', the)
        if ma is None or ma.group(1) not in co_nhan:
            thieu.append(the[:70])

    assert not thieu, (
        f"{_mo_ta_tep(tep)} có ô nhập không nhãn:\n  " + "\n  ".join(thieu)
    )


@pytest.mark.parametrize("tep", CAC_TEMPLATE, ids=lambda p: p.name)
def test_moi_bang_deu_co_tieu_de_cot(tep):
    """NFR-7 — Mọi bảng phải có tiêu đề cột

    Bảng không có `<thead>` thì người dùng không biết cột nào là gì, và dòng
    đầu tiên bị đọc nhầm thành tiêu đề.
    """
    noi_dung = tep.read_text(encoding="utf-8")
    so_bang = noi_dung.count("<table")
    so_dau = noi_dung.count("<thead")
    assert so_bang == 0 or so_dau >= so_bang, (
        f"{_mo_ta_tep(tep)} có {so_bang} bảng nhưng chỉ {so_dau} khối tiêu đề cột"
    )


@pytest.mark.parametrize("tep", CAC_TEMPLATE, ids=lambda p: p.name)
def test_moi_trang_deu_co_tieu_de_rieng(tep):
    """NFR-7 — Mỗi trang có tiêu đề riêng trên thẻ trình duyệt

    Mở nhiều thẻ mà tiêu đề giống nhau thì không biết thẻ nào là thẻ nào.
    """
    if tep.name in KHONG_CAN_NOI_DUNG or tep.name.startswith("_"):
        return
    noi_dung = tep.read_text(encoding="utf-8")
    if "{% extends" not in noi_dung:
        return                              # mảnh ghép, không phải trang
    assert "{% block tieu_de %}" in noi_dung, (
        f"{_mo_ta_tep(tep)} chưa đặt tiêu đề trang"
    )


@pytest.mark.parametrize("tep", CAC_TEMPLATE, ids=lambda p: p.name)
def test_moi_bieu_mau_gui_di_deu_co_the_chong_gia_mao(tep):
    """FR-3.6 — Mọi biểu mẫu gửi đi phải có thẻ chống giả mạo

    Thiếu thẻ thì Django chặn ở máy chủ và người dùng nhận lỗi 403 khó hiểu.
    """
    noi_dung = tep.read_text(encoding="utf-8")
    so_gui = len(re.findall(r'<form[^>]*method="post"', noi_dung, re.IGNORECASE))
    so_the = noi_dung.count("{% csrf_token %}")
    assert so_gui == 0 or so_the >= so_gui, (
        f"{_mo_ta_tep(tep)} có {so_gui} biểu mẫu gửi đi nhưng chỉ {so_the} thẻ chống giả mạo"
    )


@pytest.mark.parametrize("tep", CAC_TEMPLATE, ids=lambda p: p.name)
def test_nut_khong_hoan_tac_duoc_deu_bao_mau(tep):
    """NFR-7 — Nút xoá, bỏ, thu quyền phải mang lớp cảnh báo

    Bấm nhầm những nút này thì không hoàn tác được, nên chúng phải trông khác
    nút thường.
    """
    noi_dung = tep.read_text(encoding="utf-8")
    nguy_hiem = ("Xoá", ">Bỏ", "Bỏ ", ">Thu<", "Thu quyền", "Khoá")

    thieu = []
    for the in re.findall(r"<button\b[^>]*>[^<]*", noi_dung):
        if not any(tu in the for tu in nguy_hiem):
            continue
        if "nut-nguy" not in the:
            thieu.append(the.strip()[:70])

    assert not thieu, (
        f"{_mo_ta_tep(tep)} có nút không hoàn tác được nhưng chưa báo màu:\n  "
        + "\n  ".join(thieu)
    )


#: Lớp bổ nghĩa và lớp gốc bắt buộc đi kèm.
#:
#: Những lớp này **không tự đứng một mình được** — chúng chỉ chỉnh một thuộc
#: tính của lớp gốc. Dùng thiếu lớp gốc thì trình duyệt bỏ qua lặng lẽ, trang
#: vẫn trả 200, chỉ bố cục sai.
#:
#: Đã xảy ra thật: `bm-hang-2` dùng một mình ở bốn chỗ nên ô nhập xếp dọc
#: thay vì hai cột, suốt từ Giai đoạn 4 tới Giai đoạn 5.
LOP_BO_NGHIA = {
    "luoi-2": "luoi", "luoi-3": "luoi", "luoi-4": "luoi",
    "luoi-3cot": "luoi", "luoi-phu": "luoi",
    "bm-hang-2": "bm-hang",
    "nut-chinh": "nut", "nut-nho": "nut", "nut-nguy": "nut", "nut-nav": "nut",
    "chip-tot": "chip", "chip-xau": "chip", "chip-nhat": "chip",
    "chip-nhan": "chip", "chip-cho": "chip",
}


@pytest.mark.parametrize("tep", CAC_TEMPLATE, ids=lambda p: p.name)
def test_lop_bo_nghia_luon_di_kem_lop_goc(tep):
    """NFR-7 — Lớp bổ nghĩa phải đi kèm lớp gốc, không đứng một mình

    Thiếu lớp gốc thì trình duyệt bỏ qua và bố cục sai âm thầm — Django vẫn
    trả 200 nên không bài kiểm nào khác thấy.
    """
    noi_dung = tep.read_text(encoding="utf-8")

    thieu = []
    for cum in re.findall(r'class="([^"]*)"', noi_dung):
        cac_lop = set(cum.split())
        for bo_nghia, goc in LOP_BO_NGHIA.items():
            if bo_nghia in cac_lop and goc not in cac_lop:
                thieu.append(f'class="{cum}" — thiếu .{goc}')

    assert not thieu, (
        f"{_mo_ta_tep(tep)} dùng lớp bổ nghĩa thiếu lớp gốc:\n  "
        + "\n  ".join(sorted(set(thieu)))
    )
