"""Dò mật khẩu bằng nhiều yêu cầu cùng lúc không vượt được giới hạn 5 lần — AC-1.9 (săn lỗi 06.10.2026).

Đo trên hệ thống thật: 40 lần đăng nhập sai gửi **cùng lúc** vào một tài khoản thì cả 40 lần đều được máy chủ thử mật
khẩu (trả "không đúng"), không lần nào bị chặn — vì mọi yêu cầu đều đọc "chưa bị khoá" trước khi yêu cầu nào kịp ghi
khoá, và bộ đếm cộng kiểu đọc-rồi-ghi nên mất lượt. Kẻ dò được 40 lần mỗi 15 phút thay vì 5, càng nhiều luồng càng
nhiều. Nay mỗi lần thử giữ chỗ trong bộ đếm (khoá dòng) **trước** khi kiểm mật khẩu.
"""
import threading

import pytest
from django.db import connection
from django.test import Client

from core.constants import AuditAction
from core.models import AuditLog


@pytest.mark.django_db(transaction=True)
def test_dang_nhap_sai_cung_luc_khong_vuot_gioi_han(nguoi_dung, settings):
    """AC-1.9 — 20 lần đăng nhập sai gửi cùng lúc vào một tài khoản: máy chủ thử mật khẩu nhiều nhất 5 lần, các lần còn lại báo đang bị khoá tạm; tài khoản bị khoá"""
    so_luong = 20
    cho = threading.Barrier(so_luong)
    ket_qua = []

    def thu(i):
        try:
            client = Client()
            cho.wait()
            r = client.post("/dang-nhap/", {"username": "staff_sale_1", "password": f"sai-{i}"})
            noi_dung = r.content.decode()
            ket_qua.append("khoa" if "bị khoá tạm" in noi_dung else ("sai" if "không đúng" in noi_dung else r.status_code))
        finally:
            connection.close()

    luong = [threading.Thread(target=thu, args=(i,)) for i in range(so_luong)]
    [t.start() for t in luong]
    [t.join() for t in luong]
    assert len(ket_qua) == so_luong
    assert ket_qua.count("sai") <= settings.LOGIN_MAX_FAILED, ket_qua
    assert ket_qua.count("khoa") >= so_luong - settings.LOGIN_MAX_FAILED
    profile = nguoi_dung["staff_sale_1"].profile
    profile.refresh_from_db()
    assert profile.locked_until is not None


@pytest.mark.django_db
def test_lan_thu_thu_nam_dung_mat_khau_van_vao_duoc(client, nguoi_dung, settings):
    """AC-1.9 — Giữ chỗ trước khi kiểm mật khẩu không đổi luật cũ: sai 4 lần rồi lần thứ 5 đúng mật khẩu vẫn vào được, bộ đếm và khoá trở về không; chỉ ghi nhật ký "Khoá tạm" khi thật sự khoá"""
    for _ in range(settings.LOGIN_MAX_FAILED - 1):
        client.post("/dang-nhap/", {"username": "staff_sale_1", "password": "sai"})
    r = client.post("/dang-nhap/", {"username": "staff_sale_1", "password": "matkhau-kiem-thu-1"})
    assert r.status_code == 302
    profile = nguoi_dung["staff_sale_1"].profile
    profile.refresh_from_db()
    assert profile.failed_login_count == 0 and profile.locked_until is None
    assert not AuditLog.objects.filter(action=AuditAction.PERMISSION, detail__startswith="Khoá tạm").exists()


@pytest.mark.django_db
def test_bao_khoa_dung_so_phut(client, nguoi_dung, settings):
    """AC-1.9 — Đang bị khoá thì lời báo nói đúng số phút còn lại (15), không phải 1"""
    for _ in range(settings.LOGIN_MAX_FAILED):
        client.post("/dang-nhap/", {"username": "staff_sale_1", "password": "sai"})
    r = client.post("/dang-nhap/", {"username": "staff_sale_1", "password": "sai"})
    assert f"thử lại sau {settings.LOGIN_LOCK_MINUTES} phút" in r.content.decode()
