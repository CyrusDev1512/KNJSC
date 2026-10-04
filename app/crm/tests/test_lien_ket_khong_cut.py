"""KN CRM không hiện liên kết dẫn tới trang bị từ chối — AC-40.5, AC-40.6.

Kiểm toàn diện 04.10.2026 bấm qua mọi liên kết theo vai thì thấy: mục "Nhật ký" hiện cho mọi Manager nhưng trang chỉ
Admin mở được (quyết định 25.09, AC-44.2); Manager Marketing không có bảng vận đơn nào (ADR-040) vẫn thấy "Bảng tính"
dẫn tới `/thu-muc/` 404; trang Nhập tệp / Cấp quyền còn nút "+ Tạo bảng" mà trang chủ đã bỏ, form của nó có nút
"Quay lại" sang `/danh-sach-bang/` 404. Không đổi quyền nào — chỉ ẩn liên kết theo đúng quyền đã chốt.
"""
import re

import pytest

from core.constants import Rank
from orders.services import dispatch_service

from .test_waybill_new import order, setup  # noqa: F401 — fixture `setup` dùng chung

pytestmark = pytest.mark.django_db


@pytest.fixture
def he_thong(departments, nguoi_dung, make_user):
    dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    return {**nguoi_dung,
            "manager_vd": make_user("manager_vd", Rank.MANAGER, departments["vd"]),
            "leader_mkt": make_user("leader_mkt", Rank.LEADER, departments["mkt"])}


def _sidebar(html):
    return html.split('id="thanh-ben"')[1].split('<div class="chinh">')[0]


def _lien_ket_trong(html):
    """Mọi href nội bộ trong trang, bỏ đăng xuất và tài nguyên tĩnh."""
    return {h for h in re.findall(r'href="(/[^"#]*)"', html)
            if not h.startswith(("/static/", "/dang-xuat")) and "mau-nhap" not in h}


def test_nhat_ky_chi_admin_thay(client, he_thong):
    """AC-40.5 — Mục "Nhật ký" trên thanh bên KN CRM chỉ hiện cho Admin, đúng như trang Nhật ký chỉ Admin mở được (AC-44.2); Manager không thấy mục, gọi thẳng vẫn bị 403"""
    for ai in ("manager_vd", "manager_sale", "manager_mkt"):
        client.force_login(he_thong[ai])
        ben = _sidebar(client.get("/").content.decode())
        assert 'href="/nhat-ky/"' not in ben, f"{ai} thấy mục Nhật ký"
        assert client.get("/nhat-ky/").status_code == 403
    client.force_login(he_thong["admin"])
    ben = _sidebar(client.get("/").content.decode())
    assert 'href="/nhat-ky/"' in ben
    assert client.get("/nhat-ky/").status_code == 200


def test_khong_co_bang_van_don_thi_khong_co_lien_ket_bang_tinh(client, he_thong):
    """AC-40.6 — Người không có bảng vận đơn nào trong phạm vi (Marketing) không thấy "Bảng tính" ở thanh bên và trang chủ KN CRM; người có bảng vận đơn vẫn thấy và mở được; trang Nhập tệp, Cấp quyền không còn nút "+ Tạo bảng" (ADR-040)"""
    client.force_login(he_thong["manager_mkt"])
    html = client.get("/").content.decode()
    assert 'href="/thu-muc/"' not in html and "Mở Bảng tính" not in html
    assert client.get("/thu-muc/").status_code == 404        # quyền không đổi

    client.force_login(he_thong["staff_vd"])
    html = client.get("/").content.decode()
    assert 'href="/thu-muc/"' in _sidebar(html) and "Mở Bảng tính" in html
    assert client.get("/thu-muc/").status_code == 200

    for ai, trang in (("manager_vd", "/nhap-tep/"), ("manager_vd", "/cap-quyen/"),
                      ("leader_mkt", "/nhap-tep/"), ("admin", "/cap-quyen/")):
        client.force_login(he_thong[ai])
        kq = client.get(trang)
        assert kq.status_code == 200
        assert "+ Tạo bảng" not in kq.content.decode() and 'href="/bang/moi/"' not in kq.content.decode(), (ai, trang)


@pytest.mark.parametrize("ai", ["staff_vd", "manager_vd", "staff_sale_1", "leader_sale_1", "manager_sale",
                                "staff_mkt", "leader_mkt", "manager_mkt", "admin"])
def test_moi_lien_ket_tren_trang_chu_mo_duoc(client, he_thong, ai):
    """AC-40.6 — Với mọi vai, bấm từng liên kết trên trang chủ KN CRM (thanh bên và nội dung) và trên các trang của thanh bên không gặp 403 hay 404"""
    client.force_login(he_thong[ai])
    trang_chu = client.get("/")
    assert trang_chu.status_code == 200
    cap_1 = _lien_ket_trong(trang_chu.content.decode())
    da_mo, hong = {}, []
    for lk in sorted(cap_1):
        kq = client.get(lk)
        da_mo[lk] = kq
        if kq.status_code in (403, 404):
            hong.append((lk, kq.status_code))
    for lk in sorted(_lien_ket_trong(_sidebar(trang_chu.content.decode()))):
        kq = da_mo[lk]
        if kq.status_code == 200 and "text/html" in kq.get("Content-Type", ""):
            for con in sorted(_lien_ket_trong(kq.content.decode()) - set(da_mo)):
                da_mo[con] = trang = client.get(con)
                if trang.status_code in (403, 404):
                    hong.append((f"{lk} → {con}", trang.status_code))
    assert not hong, f"{ai} gặp liên kết hỏng: {hong}"




def _dich_cua_nut(client, duong, mau):
    kq = client.get(duong)
    assert kq.status_code == 200, duong
    return re.search(mau, kq.content.decode()).group(1)


def test_nut_ve_cua_len_don_va_don_goc_khong_dan_toi_404(client, setup, nguoi_dung):
    """AC-40.6 — Sale chưa có đơn nào (chưa thấy bảng vận đơn) mở Lên đơn: nút ← về trang mở được, không về thư mục 404; người đã có đơn và Admin vẫn về thư mục, nút "Quay lại" của đơn gốc cũng mở được"""
    nut_ve = r'class="bt-ve" href="([^"]+)"'
    client.force_login(nguoi_dung["staff_sale_2"])
    ve = _dich_cua_nut(client, "/van-don/len-don/", nut_ve)
    assert client.get(ve).status_code == 200, ve
    for ai in ("staff_sale_1", "admin"):
        client.force_login(nguoi_dung[ai])
        don = order(setup, nguoi_dung[ai])
        assert _dich_cua_nut(client, "/van-don/len-don/", nut_ve) == "/thu-muc/"
        quay_lai = _dich_cua_nut(client, f"/van-don/don-goc/{don.code}/", r'<a class="nut" href="([^"]+)">Quay lại</a>')
        assert client.get(quay_lai).status_code == 200, (ai, quay_lai)
