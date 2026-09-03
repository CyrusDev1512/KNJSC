"""Kiểm thử tài khoản, đăng nhập và hiệu lực phiên."""
import pytest
from django.utils import timezone

from core.constants import AuditAction, Rank
from core.models import AuditLog
from org.services import account_service

pytestmark = pytest.mark.django_db


def test_dang_nhap_dung_mat_khau_thi_vao_duoc(client, nguoi_dung):
    """AC-1.1 — Đăng nhập đúng email và mật khẩu thì vào được hệ thống"""
    tra_loi = client.post("/dang-nhap/", {
        "username": "staff_sale_1", "password": "matkhau-kiem-thu-1",
    })
    assert tra_loi.status_code == 302
    assert AuditLog.objects.filter(action=AuditAction.LOGIN).exists()


def test_dang_nhap_sai_mat_khau_thi_bi_tu_choi(client, nguoi_dung):
    """AC-1.1 — Sai mật khẩu thì không vào được"""
    tra_loi = client.post("/dang-nhap/", {
        "username": "staff_sale_1", "password": "sai-mat-khau",
    })
    assert tra_loi.status_code == 200
    assert AuditLog.objects.filter(action=AuditAction.LOGIN_FAILED).exists()


def test_thong_bao_loi_khong_lo_tai_khoan_co_ton_tai_khong(client, nguoi_dung):
    """AC-1.1 — Thông báo lỗi giống nhau dù email có tồn tại hay không"""
    co = client.post("/dang-nhap/", {"username": "staff_sale_1", "password": "sai"})
    khong = client.post("/dang-nhap/", {"username": "khong_ton_tai", "password": "sai"})
    assert "Tên đăng nhập hoặc mật khẩu không đúng" in co.content.decode()
    assert "Tên đăng nhập hoặc mật khẩu không đúng" in khong.content.decode()


def test_khoa_tam_sau_nam_lan_dang_nhap_sai(client, nguoi_dung, settings):
    """AC-1.2 — Khoá tạm tài khoản 15 phút sau 5 lần đăng nhập sai liên tiếp"""
    for _ in range(settings.LOGIN_MAX_FAILED):
        client.post("/dang-nhap/", {"username": "staff_sale_1", "password": "sai"})

    profile = nguoi_dung["staff_sale_1"].profile
    profile.refresh_from_db()
    assert profile.locked_until is not None
    assert profile.locked_until > timezone.now()

    # Đúng mật khẩu cũng không vào được khi đang bị khoá
    tra_loi = client.post("/dang-nhap/", {
        "username": "staff_sale_1", "password": "matkhau-kiem-thu-1",
    })
    assert tra_loi.status_code == 200
    assert "bị khoá tạm" in tra_loi.content.decode()


def test_dang_nhap_thanh_cong_xoa_bo_dem_sai(client, nguoi_dung):
    """AC-1.2 — Đăng nhập thành công thì bộ đếm sai trở về không"""
    client.post("/dang-nhap/", {"username": "staff_sale_1", "password": "sai"})
    profile = nguoi_dung["staff_sale_1"].profile
    profile.refresh_from_db()
    assert profile.failed_login_count == 1

    client.post("/dang-nhap/", {
        "username": "staff_sale_1", "password": "matkhau-kiem-thu-1",
    })
    profile.refresh_from_db()
    assert profile.failed_login_count == 0


def test_doi_cap_bac_lam_phien_dang_mo_mat_hieu_luc(client, nguoi_dung):
    """AC-1.6 — Đổi quyền thì phiên đang mở mất hiệu lực ngay, không đợi lần sau"""
    client.post("/dang-nhap/", {
        "username": "staff_sale_1", "password": "matkhau-kiem-thu-1",
    })
    assert client.get("/").status_code == 200

    account_service.set_rank(nguoi_dung["staff_sale_1"].profile, Rank.LEADER)

    tra_loi = client.get("/")
    assert tra_loi.status_code == 302
    assert "doi_quyen=1" in tra_loi.headers["Location"]


def test_khoa_tai_khoan_lam_phien_dang_mo_mat_hieu_luc(client, nguoi_dung):
    """AC-1.6 — Khoá tài khoản thì phiên đang mở bị huỷ ngay"""
    client.post("/dang-nhap/", {
        "username": "staff_sale_1", "password": "matkhau-kiem-thu-1",
    })
    assert client.get("/").status_code == 200

    account_service.lock_account(nguoi_dung["staff_sale_1"].profile)
    assert client.get("/").status_code == 302


def test_tao_tai_khoan_moi_buoc_doi_mat_khau(db, departments):
    """AC-1.5 — Tài khoản mới phải đổi mật khẩu ở lần đăng nhập đầu"""
    profile = account_service.create_account(
        username="nhan_vien_moi", email="moi@kimngan.vn", full_name="Nhân Viên Mới",
        rank=Rank.STAFF, department=departments["sale"], password="matkhau-kiem-thu-1",
    )
    assert profile.must_change_password is True
    assert AuditLog.objects.filter(action=AuditAction.CREATE).exists()


def test_buoc_doi_mat_khau_chan_moi_man_hinh_khac(client, db, departments):
    """AC-1.5 — Chưa đổi mật khẩu thì bị đẩy về màn hình đổi mật khẩu"""
    account_service.create_account(
        username="nhan_vien_moi", email="moi@kimngan.vn", full_name="Nhân Viên Mới",
        rank=Rank.STAFF, department=departments["sale"], password="matkhau-kiem-thu-1",
    )
    client.post("/dang-nhap/", {
        "username": "nhan_vien_moi", "password": "matkhau-kiem-thu-1",
    })
    tra_loi = client.get("/")
    assert tra_loi.status_code == 302
    assert "/doi-mat-khau/" in tra_loi.headers["Location"]


def test_dat_lai_mat_khau_khong_ghi_mat_khau_vao_nhat_ky(db, nguoi_dung):
    """Điều cấm 6 — Đặt lại mật khẩu không để mật khẩu lọt vào nhật ký"""
    account_service.reset_password(nguoi_dung["staff_sale_1"].profile, "MatKhauMoi-2026")
    for ban_ghi in AuditLog.objects.all():
        assert "MatKhauMoi-2026" not in ban_ghi.detail
