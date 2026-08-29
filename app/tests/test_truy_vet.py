"""Truy vết hai chiều giữa `docs/04` và mã kiểm thử.

`docs/04` mục 12 điều 1 nói điều kiện hoàn thành phase 1 là *"toàn bộ tiêu chí
đánh dấu Tự động đều có bài kiểm thử và đều đạt"*. Tệp này biến điều kiện đó
thành mã chạy được, thay vì phải rà bằng mắt mỗi lần.

Hai chiều:

- **Tài liệu ra mã** — mỗi tiêu chí Tự động phải có ít nhất một bài kiểm
- **Mã về tài liệu** — mã tiêu chí ghi trong docstring phải có thật trong `docs/04`

Bài kiểm ghi mã quy tắc (BR, FR, ADR, Q, quy tắc) thay vì mã tiêu chí là **cố
ý và hợp lệ** — chúng kiểm quy tắc nghiệp vụ hoặc quyết định kiến trúc, không
phải tiêu chí nghiệm thu. Chỉ mã bắt đầu bằng `AC-` mới bị soi ở đây.
"""
import re
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent

#: Thư mục tài liệu nằm khác chỗ tuỳ cách chạy: trong container nó được gắn ở
#: `/docs`, chạy thẳng trên máy thì nó là thư mục anh em của `app/`.
CAC_NOI_CO_THE = [
    GOC.parent / "docs" / "04-tieu-chi-nghiem-thu.md",
    Path("/docs") / "04-tieu-chi-nghiem-thu.md",
]
TEP_TIEU_CHI = next((p for p in CAC_NOI_CO_THE if p.exists()), CAC_NOI_CO_THE[0])

#: Tiêu chí Tự động chưa làm được, kèm lý do và giai đoạn.
#:
#: **Đây là danh sách việc còn lại, không phải chỗ giấu lỗi.** Thêm mã vào đây
#: phải ghi rõ vì sao chưa làm được và chờ giai đoạn nào. Rỗng dần theo tiến độ.
HOAN = {
    "AC-5.1": "Báo cáo tổng hợp — Giai đoạn 6",
    "AC-5.2": "Báo cáo tổng hợp — Giai đoạn 6",
    "AC-5.3": "Báo cáo tổng hợp — Giai đoạn 6",
    "AC-5.4": "Báo cáo tổng hợp — Giai đoạn 6",
    "AC-5.5": "Báo cáo tổng hợp — Giai đoạn 6",
    "AC-7.1": "Cần seed_perf.py sinh 50.000 bản ghi — Giai đoạn 8",
    "AC-7.5": "Nhập tệp Excel — Giai đoạn 7",
    "AC-7.6": "Nhập tệp Excel — Giai đoạn 7",
    "AC-7.7": "Xuất rồi nhập lại tệp Excel — Giai đoạn 7",
    "AC-7.8": "Giới hạn kích thước tệp tải lên — Giai đoạn 7",
    "AC-7.9": "Kiểm định dạng tệp tải lên — Giai đoạn 7",
    "AC-10.6": "Sao lưu tự động — Giai đoạn 8",
}

DONG_TIEU_CHI = re.compile(
    r"^\|\s*(AC-\d+\.\d+)\s*\|(.+?)\|(.+?)\|\s*(Tự động|Thủ công)\s*\|", re.MULTILINE
)
#: Chỉ nhận mã nằm **ngay đầu docstring**, đúng quy ước `docs/04`:
#:
#:     """AC-3.1 — Staff chỉ xem được dữ liệu do chính mình tạo"""
#:
#: Nhắc tới mã ở giữa lời giải thích thì không tính là đã kiểm — đó là chú
#: thích, không phải lời khẳng định bài này kiểm tiêu chí đó.
MA_TRONG_DOCSTRING = re.compile(r'"""(AC-\d+\.\d+)\b')


def _tieu_chi():
    """Đọc `docs/04`, trả về `{mã: (nội dung, loại)}`."""
    if not TEP_TIEU_CHI.exists():
        return {}
    noi_dung = TEP_TIEU_CHI.read_text(encoding="utf-8")
    return {
        ma: (mo_ta.strip(), loai)
        for ma, mo_ta, _, loai in DONG_TIEU_CHI.findall(noi_dung)
    }


def _ma_trong_bai_kiem():
    """Mọi mã tiêu chí xuất hiện trong docstring của bài kiểm."""
    thay = {}
    for tep in GOC.rglob("test_*.py"):
        if tep.name == Path(__file__).name:      # không tự đếm chính mình
            continue
        for ma in MA_TRONG_DOCSTRING.findall(tep.read_text(encoding="utf-8")):
            thay.setdefault(ma, []).append(tep.name)
    return thay


TIEU_CHI = _tieu_chi()
DA_KIEM = _ma_trong_bai_kiem()


def test_doc_duoc_tai_lieu_tieu_chi():
    """Bài truy vết chỉ có nghĩa khi đọc được `docs/04`"""
    assert TEP_TIEU_CHI.exists(), f"Không tìm thấy {TEP_TIEU_CHI}"
    assert len(TIEU_CHI) >= 40, f"Chỉ đọc được {len(TIEU_CHI)} tiêu chí, chắc chắn thiếu"


def test_moi_tieu_chi_tu_dong_deu_co_bai_kiem():
    """docs/04 mục 12 điều 1 — Mọi tiêu chí Tự động đều có bài kiểm thử

    Đây là điều kiện hoàn thành phase 1, viết thành mã chạy được. Đỏ nghĩa là
    có tiêu chí đã hứa tự động hoá nhưng chưa ai viết bài kiểm.
    """
    thieu = {
        ma: mo_ta for ma, (mo_ta, loai) in TIEU_CHI.items()
        if loai == "Tự động" and ma not in DA_KIEM and ma not in HOAN
    }
    assert not thieu, (
        "Tiêu chí Tự động chưa có bài kiểm nào:\n"
        + "\n".join(f"  {ma} — {mo_ta}" for ma, mo_ta in sorted(thieu.items()))
        + "\n\nViết bài kiểm, hoặc thêm vào HOAN kèm lý do và giai đoạn."
    )


def test_ma_tieu_chi_trong_bai_kiem_deu_co_that():
    """Quy ước `docs/04` — Mã ghi trong docstring phải có thật trong tài liệu

    Đỏ nghĩa là ai đó gõ sai mã, hoặc bịa ra mã không tồn tại. Chuyện này đã
    xảy ra: mã `AC-7.8` từng bị dùng cho cột tính sẵn, trong khi tài liệu định
    nghĩa nó là giới hạn kích thước tệp.
    """
    bia = {ma: sorted(set(tep)) for ma, tep in DA_KIEM.items() if ma not in TIEU_CHI}
    assert not bia, (
        "Bài kiểm ghi mã tiêu chí không có trong docs/04:\n"
        + "\n".join(f"  {ma} — trong {', '.join(tep)}" for ma, tep in sorted(bia.items()))
    )


def test_danh_sach_hoan_khong_chua_tieu_chi_da_lam():
    """Danh sách hoãn phải rỗng dần — làm xong rồi thì gỡ khỏi HOAN

    Không có bài này thì HOAN cứ phình ra và che mất tiêu chí đã có bài kiểm.
    """
    da_lam = sorted(ma for ma in HOAN if ma in DA_KIEM)
    assert not da_lam, (
        "Các tiêu chí này đã có bài kiểm rồi, gỡ khỏi HOAN đi: " + ", ".join(da_lam)
    )


def test_danh_sach_hoan_deu_la_ma_co_that():
    """HOAN chỉ chứa mã có thật, không chứa mã gõ sai"""
    bia = sorted(ma for ma in HOAN if ma not in TIEU_CHI)
    assert not bia, f"HOAN chứa mã không có trong docs/04: {', '.join(bia)}"


@pytest.mark.parametrize("ma", sorted(HOAN))
def test_moi_tieu_chi_hoan_deu_ghi_ly_do(ma):
    """Mỗi mã hoãn phải ghi rõ vì sao và chờ giai đoạn nào"""
    ly_do = HOAN[ma]
    assert len(ly_do) > 10 and ("Giai đoạn" in ly_do or "backlog" in ly_do), (
        f"{ma} hoãn nhưng lý do không rõ: {ly_do!r}"
    )
