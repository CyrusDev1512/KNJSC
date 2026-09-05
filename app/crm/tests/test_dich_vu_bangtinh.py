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
    """AC-11.7 — Ở dịch vụ Bảng tính: gốc chuyển tới lưới, lưới sửa được, các màn hình khác không tồn tại"""
    dong = record_service.create_record(
        bang_vd, {"ma_don": "DH-1", "ten_khach": "A", "so_dien_thoai": "0911"},
        actor=nguoi_dung["staff_vd"],
    )
    client.force_login(nguoi_dung["staff_vd"])
    with DICH_VU_BANGTINH:
        kq = client.get("/")
        assert kq.status_code == 302 and kq["Location"] == "/bang-tinh/"
        kq = client.get("/bang-tinh/")
        assert kq.status_code == 200 and kq.context["chi_xem"] is False
        html = kq.content.decode()
        assert 'class="o-sua' in html
        # Thanh bên: có Bảng tính (liên kết trong); các mục của dịch vụ chính
        # không vẽ vì đường dẫn không tồn tại ở đây (nút "Bảng dữ liệu" trên
        # lưới là liên kết ngoài về dịch vụ chính, không tính)
        assert 'class="nav-muc" href="/bang-tinh/"' in html
        for vang in ('href="/bang/"', 'href="/len-don/"', 'href="/bieu-mau/"', 'href="/bao-cao-ngay/"'):
            assert vang not in html, f"dịch vụ bangtinh không được có mục {vang}"
        assert client.post(f"/bang-tinh/van_don/o/{dong.pk}/ghi_chu/", {"gia_tri": "sửa ở Bảng tính"}).status_code == 200
        assert client.get("/bang/").status_code == 404
        assert client.get("/len-don/").status_code == 404
        assert client.get("/tac-vu/").status_code == 200, "tải tệp xuất lớn vẫn cần trang tác vụ"
    dong.refresh_from_db()
    assert dong.data["ghi_chu"] == "sửa ở Bảng tính"


def test_dich_vu_chinh_co_lien_ket_ngoai_toi_bang_tinh(client, bang_vd, nguoi_dung, settings):
    """AC-11.4 — Ở dịch vụ chính, mục Bảng tính trên thanh bên trỏ ra địa chỉ dịch vụ riêng, và chỉ Vận đơn với Admin thấy"""
    settings.BANGTINH_URL = "http://localhost:8021/bang-tinh/"
    client.force_login(nguoi_dung["staff_vd"])
    html = client.get("/").content.decode()
    assert 'href="http://localhost:8021/bang-tinh/"' in html
    client.force_login(nguoi_dung["admin"])
    assert 'href="http://localhost:8021/bang-tinh/"' in client.get("/").content.decode()
    client.force_login(nguoi_dung["staff_sale_1"])
    assert "8021/bang-tinh" not in client.get("/").content.decode()
