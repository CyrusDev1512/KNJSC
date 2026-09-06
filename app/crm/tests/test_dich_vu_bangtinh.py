"""Dịch vụ `bangtinh` — cùng mã, cấu hình thu hẹp (ADR-009, backlog Q38).

Dựng lại đúng cấu hình của `knjsc/settings/bangtinh.py` bằng override: URLconf
thu hẹp, bảng vận đơn sửa được, mục Bảng tính trên thanh bên là liên kết trong.
"""
import pytest
from django.test import override_settings

from forms_builder.services import record_service
from orders.services import dispatch_service

pytestmark = pytest.mark.django_db

DICH_VU_BANGTINH = override_settings(
    ROOT_URLCONF="knjsc.urls_bangtinh", GRID_ONLY_TABLES=set(), BANGTINH_URL="",
)


@pytest.fixture
def bang_vd(departments, nguoi_dung):
    return dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])


def test_dich_vu_bangtinh_chi_co_bang_tinh_va_dang_nhap(client, bang_vd, nguoi_dung):
    """AC-11.7 — Ở app KN CRM: gốc là trang chủ, lưới sửa được, các màn hình khác không tồn tại"""
    dong = record_service.create_record(
        bang_vd, {"ma_don": "DH-1", "ten_khach": "A", "so_dien_thoai": "0911"},
        actor=nguoi_dung["staff_vd"],
    )
    client.force_login(nguoi_dung["staff_vd"])
    with DICH_VU_BANGTINH:
        kq = client.get("/")
        html_goc = kq.content.decode()
        assert kq.status_code == 200 and "KN CRM" in html_goc and 'id="thanh-ben"' in html_goc
        kq = client.get("/bang-tinh/")
        assert kq.status_code == 200 and kq.context["chi_xem"] is False
        html = kq.content.decode()
        assert 'class="o-sua' in html
        # Thanh bên: có Bảng tính (liên kết trong); các mục của dịch vụ chính
        # không vẽ vì đường dẫn không tồn tại ở đây (nút "Bảng dữ liệu" trên
        # lưới là liên kết ngoài về dịch vụ chính, không tính)
        assert 'class="nav-muc" href="/"\n             \n             aria-current="page">KN CRM</a>' in html or 'href="/"' in html
        assert ">KN CRM</a>" in html and 'href="/"' in html      # liên kết trong về trang chủ
        for vang in ('href="/bang/"', 'href="/len-don/"', 'href="/bieu-mau/"', 'href="/bao-cao-ngay/"'):
            assert vang not in html, f"dịch vụ bangtinh không được có mục {vang}"
        assert client.post(f"/bang-tinh/van_don/o/{dong.pk}/ghi_chu/", {"gia_tri": "sửa ở Bảng tính"}).status_code == 200
        assert client.get("/bang/").status_code == 404
        assert client.get("/len-don/").status_code == 404
        assert client.get("/tac-vu/").status_code == 200, "tải tệp xuất lớn vẫn cần trang tác vụ"
    dong.refresh_from_db()
    assert dong.data["ghi_chu"] == "sửa ở Bảng tính"


def test_erp_chi_con_lien_ket_sang_kn_crm(client, bang_vd, nguoi_dung, settings):
    """AC-11.30 — Ở KN ERP mục KN CRM trên thanh bên của mọi bộ phận là liên kết ngoài mở tab mới, lưới không tồn tại ở ERP, Bảng dữ liệu có nút mở đúng bảng trong KN CRM; ở KN CRM mục này là liên kết trong cùng tab"""
    settings.ROOT_URLCONF = "knjsc.urls"                     # KN ERP
    settings.BANGTINH_URL = "http://localhost:8021/"
    lien_ket = 'href="http://localhost:8021/"\n             target="_blank" rel="noopener"'
    for ma in ("staff_vd", "staff_sale_1", "staff_mkt", "admin"):
        client.force_login(nguoi_dung[ma])
        html = client.get("/").content.decode()
        assert lien_ket in html, f"{ma} không thấy mục KN CRM mở tab mới"
        assert ">KN CRM<" in html
    client.force_login(nguoi_dung["staff_vd"])
    assert client.get("/bang-tinh/").status_code == 404, "lưới không còn ở ERP"
    assert client.get("/bang-tinh/van_don/").status_code == 404
    html = client.get("/bang/van_don/").content.decode()
    assert 'href="http://localhost:8021/bang-tinh/van_don/" target="_blank" rel="noopener">Mở trong KN CRM</a>' in html

    # Ở chính KN CRM: mục là liên kết trong, không mở tab mới
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.BANGTINH_URL = ""
    html = client.get("/bang-tinh/").content.decode()
    assert ">KN CRM</a>" in html and 'href="/"' in html and "target=\"_blank\"" not in html
