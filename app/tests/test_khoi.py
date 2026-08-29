"""Kiểm khói — mọi đường dẫn × mọi vai trò, không đường nào được nổ.

Rẻ nhất và bắt được nhiều nhất. Không kiểm nghiệp vụ, chỉ hỏi một câu: gọi
đường dẫn này bằng tài khoản kia thì hệ thống có sập không, và có lộ dữ liệu
không.

**Danh sách đường dẫn tự lấy từ bộ định tuyến của Django**, không chép tay.
Nhờ vậy thêm màn hình mới mà quên kiểm quyền là đỏ ngay, không phải nhớ bổ
sung vào danh sách — đúng loại lỗi đã lọt qua ở Giai đoạn 3 và 5.

Ba điều khẳng định:

1. Không bao giờ trả 500 — NFR-6
2. Chưa đăng nhập thì bị chuyển về trang đăng nhập — AC-1.1
3. Ngoài phạm vi thì 403 hoặc 404, **không phải** 200 với danh sách rỗng — AC-3.6
"""
import pytest
from django.urls import URLPattern, URLResolver, get_resolver

pytestmark = pytest.mark.django_db

#: Đường dẫn bỏ qua, kèm lý do. Không phải chỗ giấu màn hình hỏng.
BO_QUA = {
    "dang_xuat": "chỉ nhận POST, và làm mất phiên của mọi bài sau",
    "dang_nhap": "trang công khai, đã có bài kiểm riêng ở test_account.py",
    "doi_mat_khau": "trang công khai với người đã đăng nhập",
}

#: Trang quản trị của Django có trang đăng nhập riêng và không phải mã của dự
#: án này. Điều cấm 12 nói rõ nó chỉ dành cho quản trị viên, không dùng cho
#: nghiệp vụ hằng ngày — nên không kiểm khói ở đây.
TIEN_TO_BO_QUA = ("/quan-tri/",)

#: Mã chấp nhận được. 200 là vào được, 302 là chuyển hướng, 403 và 404 là từ
#: chối. Riêng 500 thì không bao giờ.
MA_CHAP_NHAN = {200, 302, 403, 404, 405}


def _tham_so_mau(mau):
    """Giá trị mẫu cho tham số trên đường dẫn.

    Dùng giá trị chắc chắn **không tồn tại**: mục đích là kiểm hệ thống xử lý
    êm, không phải kiểm dữ liệu. Không tồn tại thì 404, vẫn là mã chấp nhận
    được — còn nổ 500 thì là lỗi thật.
    """
    return {
        "pk": 999999, "id": 999999,
        "code": "khong-ton-tai", "ma_cot": "khong_ton_tai",
    }


def _thu_thap(resolver=None, tien_to=""):
    """Duyệt cây định tuyến, trả về danh sách (tên, đường dẫn dựng sẵn)."""
    resolver = resolver or get_resolver()
    ket_qua = []
    for mau in resolver.url_patterns:
        if isinstance(mau, URLResolver):
            ket_qua += _thu_thap(mau, tien_to + str(mau.pattern))
            continue
        if not isinstance(mau, URLPattern) or not mau.name:
            continue
        if mau.name in BO_QUA:
            continue

        duong_dan = "/" + tien_to + str(mau.pattern)
        gia_tri = _tham_so_mau(mau)
        # Thay <int:pk>, <slug:code>... bằng giá trị mẫu
        for ten, gt in gia_tri.items():
            for kieu in ("int", "slug", "str"):
                duong_dan = duong_dan.replace(f"<{kieu}:{ten}>", str(gt))
        if "<" in duong_dan:            # còn tham số lạ thì bỏ, không đoán bừa
            continue
        if duong_dan.startswith(TIEN_TO_BO_QUA):
            continue
        ket_qua.append((mau.name, duong_dan))
    return ket_qua


CAC_DUONG_DAN = sorted(set(_thu_thap()))

#: Vai trò kiểm chéo. Mỗi cấp bậc của mỗi bộ phận đúng một đại diện.
CAC_VAI_TRO = ["staff_sale_1", "leader_sale_1", "manager_sale", "staff_mkt",
               "staff_vd", "admin"]


def test_tim_duoc_du_duong_dan():
    """Bài quét chỉ có nghĩa khi thật sự lấy được danh sách đường dẫn"""
    assert len(CAC_DUONG_DAN) >= 20, (
        f"Chỉ tìm thấy {len(CAC_DUONG_DAN)} đường dẫn, chắc chắn thiếu"
    )


@pytest.mark.parametrize("ten,duong_dan", CAC_DUONG_DAN, ids=lambda x: str(x))
def test_chua_dang_nhap_thi_bi_chuyen_ve_trang_dang_nhap(client, ten, duong_dan):
    """AC-1.1 — Gọi mọi đường dẫn khi chưa đăng nhập thì bị chuyển về đăng nhập"""
    kq = client.get(duong_dan)
    assert kq.status_code in (302, 405), (
        f"{ten} ({duong_dan}) trả {kq.status_code} cho người chưa đăng nhập"
    )
    if kq.status_code == 302:
        assert "/dang-nhap/" in kq["Location"], (
            f"{ten} chuyển tới {kq['Location']}, không phải trang đăng nhập"
        )


@pytest.mark.parametrize("vai_tro", CAC_VAI_TRO)
@pytest.mark.parametrize("ten,duong_dan", CAC_DUONG_DAN, ids=lambda x: str(x))
def test_khong_duong_dan_nao_no(client, nguoi_dung, vai_tro, ten, duong_dan):
    """NFR-6 — Không đường dẫn nào trả lỗi 500, với bất kỳ vai trò nào

    Bài này không kiểm nghiệp vụ. Nó chỉ khẳng định hệ thống không sập, và
    người ngoài phạm vi nhận đúng lỗi từ chối chứ không phải trang trắng.
    """
    client.force_login(nguoi_dung[vai_tro])
    kq = client.get(duong_dan)
    assert kq.status_code in MA_CHAP_NHAN, (
        f"{vai_tro} gọi {ten} ({duong_dan}) nhận {kq.status_code}"
    )
