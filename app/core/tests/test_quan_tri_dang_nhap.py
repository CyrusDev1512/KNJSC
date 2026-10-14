"""Trang quản trị Django `/quan-tri/` dùng chung cửa đăng nhập của hệ thống — TL-93 · P0-8.

Trước đây `/quan-tri/login/` là form đăng nhập riêng của Django: không qua khoá tạm 5 lần sai (FR-1.2), không
ghi nhật ký đăng nhập, đăng nhập sai, đăng xuất, không ghi mốc phiên (P4) — một cửa dò mật khẩu Admin không
giới hạn. Nay `/quan-tri/login/` chỉ chuyển về `/dang-nhap/?next=/quan-tri/`, không bao giờ kiểm mật khẩu;
người đã đăng nhập mà không phải quản trị viên nhận 403 có nhật ký (chủ dự án chốt 13.10.2026).
"""
import pytest
from django.utils import timezone

from core.constants import AuditAction, Rank
from core.models import AuditLog
from org.services import account_service

pytestmark = pytest.mark.django_db

MAT_KHAU = "matkhau-kiem-thu-1"


@pytest.fixture
def quan_tri(nguoi_dung):
    """Quản trị viên có quyền vào trang quản trị Django như tài khoản thật (`set_rank` bật is_staff, ADR-044)."""
    admin = nguoi_dung["admin"]
    account_service.set_rank(admin.profile, Rank.ADMIN)
    admin.refresh_from_db()
    return admin


def _so_nhat_ky(user, action):
    return AuditLog.objects.filter(actor=user, action=action).count()


def test_quan_tri_login_khong_con_kiem_mat_khau(client, quan_tri, settings):
    """AC-1.2 — /quan-tri/login/ không còn là cửa dò mật khẩu: sai bao nhiêu lần rồi đúng cũng chỉ được chuyển về
    /dang-nhap/, không có phiên, không đếm lần sai ở đây (TL-93)"""
    for i in range(settings.LOGIN_MAX_FAILED + 1):
        r = client.post("/quan-tri/login/?next=/quan-tri/",
                        {"username": "quan_tri", "password": f"sai-{i}", "next": "/quan-tri/"})
        assert r.status_code == 302 and r["Location"].startswith("/dang-nhap/"), r.status_code
    r = client.post("/quan-tri/login/", {"username": "quan_tri", "password": MAT_KHAU, "next": "/quan-tri/"})

    assert r.status_code == 302 and r["Location"].startswith("/dang-nhap/")
    assert "_auth_user_id" not in client.session
    assert client.get("/quan-tri/").status_code == 302
    assert _so_nhat_ky(quan_tri, AuditAction.LOGIN) == 0
    quan_tri.profile.refresh_from_db()
    assert quan_tri.profile.failed_login_count == 0


def test_quan_tri_dang_khoa_tam_khong_vao_duoc(client, quan_tri, settings):
    """AC-1.2 — Quản trị viên sai 5 lần thì bị khoá như mọi người: đang khoá nhập đúng ở /quan-tri/login/ cũng
    không vào được trang quản trị; hết khoá thì vào lại /quan-tri/ qua /dang-nhap/ (TL-93)"""
    for i in range(settings.LOGIN_MAX_FAILED):
        client.post("/dang-nhap/", {"username": "quan_tri", "password": f"sai-{i}"})
    quan_tri.profile.refresh_from_db()
    assert quan_tri.profile.locked_until and quan_tri.profile.locked_until > timezone.now()

    client.post("/quan-tri/login/", {"username": "quan_tri", "password": MAT_KHAU, "next": "/quan-tri/"})
    assert "_auth_user_id" not in client.session
    assert client.get("/quan-tri/").status_code == 302

    quan_tri.profile.locked_until = timezone.now() - timezone.timedelta(minutes=1)
    quan_tri.profile.save(update_fields=["locked_until"])
    r = client.post("/dang-nhap/?next=/quan-tri/", {"username": "quan_tri", "password": MAT_KHAU})
    assert r.status_code == 302 and r["Location"] == "/quan-tri/"
    assert client.get("/quan-tri/").status_code == 200


def test_quan_tri_chua_dang_nhap_ve_cua_dang_nhap_chung(client, quan_tri):
    """AC-1.1 — Chưa đăng nhập mở /quan-tri/ thì về trang đăng nhập chung /dang-nhap/?next=/quan-tri/; quản trị
    viên đã đăng nhập mở /quan-tri/login/ thì vào thẳng trang quản trị (TL-93)"""
    r = client.get("/quan-tri/")
    assert r.status_code == 302 and r["Location"] == "/quan-tri/login/?next=/quan-tri/"
    r = client.get(r["Location"])
    assert r.status_code == 302 and r["Location"] == "/dang-nhap/?next=/quan-tri/"

    client.force_login(quan_tri)
    r = client.get("/quan-tri/login/")
    assert r.status_code == 302 and r["Location"] == "/quan-tri/"


def test_quan_tri_qua_cua_dang_nhap_chung_co_nhat_ky_va_moc_phien(client, quan_tri):
    """AC-1.6 — Vào trang quản trị qua /dang-nhap/ thì có nhật ký đăng nhập và mốc phiên (đổi quyền là phiên mất
    hiệu lực, P4); nút đăng xuất của trang quản trị ghi đúng một dòng đăng xuất (TL-93)"""
    r = client.post("/dang-nhap/?next=/quan-tri/", {"username": "quan_tri", "password": MAT_KHAU})
    assert r.status_code == 302 and r["Location"] == "/quan-tri/"
    assert client.get("/quan-tri/").status_code == 200
    assert _so_nhat_ky(quan_tri, AuditAction.LOGIN) == 1
    quan_tri.profile.refresh_from_db()
    assert client.session["auth_epoch"] == quan_tri.profile.session_epoch

    r = client.post("/quan-tri/logout/")
    assert r.status_code == 302
    assert _so_nhat_ky(quan_tri, AuditAction.LOGOUT) == 1
    assert "_auth_user_id" not in client.session


@pytest.mark.parametrize("duong", ["/quan-tri/logout/", "/dang-xuat/"])
def test_dang_xuat_bang_get_khong_ghi_nhat_ky_gia(client, quan_tri, duong):
    """AC-1.6 — Đăng xuất chỉ nhận POST: GET (gõ địa chỉ, trình duyệt tải trước) trả 405, không đăng xuất và không
    ghi dòng đăng xuất giả vào nhật ký không sửa được (BR-6, TL-93)"""
    client.force_login(quan_tri)
    assert client.get(duong).status_code == 405
    assert _so_nhat_ky(quan_tri, AuditAction.LOGOUT) == 0
    assert "_auth_user_id" in client.session


@pytest.mark.parametrize("rank", list(Rank))
def test_trang_quan_tri_django_chi_admin(client, make_user, departments, rank):
    """AC-44.2 — Chỉ quản trị viên vào trang quản trị Django; vai khác đã đăng nhập bị 403 có nhật ký, không phải
    form đăng nhập quản trị, không vòng chuyển hướng; ai đã đăng nhập cũng đăng xuất được ở nút của trang (TL-93)"""
    user = make_user("nguoi_thu", rank, None if rank in (Rank.ADMIN, Rank.CEO) else departments["sale"])
    if rank == Rank.ADMIN:
        account_service.set_rank(user.profile, Rank.ADMIN)
    client.force_login(user)

    r = client.get("/quan-tri/")
    if rank == Rank.ADMIN:
        assert r.status_code == 200
    else:
        assert r.status_code == 302 and r["Location"].startswith("/quan-tri/login/")
        truoc = _so_nhat_ky(user, AuditAction.DENIED)
        assert client.get(r["Location"]).status_code == 403
        assert _so_nhat_ky(user, AuditAction.DENIED) == truoc + 1

    assert client.post("/quan-tri/logout/").status_code == 302
    assert "_auth_user_id" not in client.session and _so_nhat_ky(user, AuditAction.LOGOUT) == 1


def test_kn_crm_khong_co_trang_quan_tri(client, settings):
    """AC-1.12 — KN CRM (8021) không có trang quản trị Django: /quan-tri/login/ là 404 (bài khoá, TL-93)"""
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    assert client.get("/quan-tri/login/").status_code == 404
