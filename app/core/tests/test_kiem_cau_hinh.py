"""Cấu hình VPS sai thì phát hành dừng lại, không âm thầm mất phiên hay chạy chế độ gỡ lỗi — AC-1.11 (06.10.2026).

- ERP và CRM ở hai tên miền mà chưa đặt `SESSION_COOKIE_DOMAIN`/`CSRF_COOKIE_DOMAIN` là tên miền cha: cookie phiên chỉ
  thuộc một tên miền, sang tên miền kia là phải đăng nhập lại — người dùng thấy như "đổi URL là mất quyền".
  `deploy/production/compose.yml` chưa đặt hai biến này.
- Dịch vụ `bangtinh` thiếu `BANGTINH_GOC=prod` thì lặng lẽ lấy cấu hình dev (DEBUG bật, cookie không Secure).
"""
import os
import subprocess
import sys

import pytest
from django.core.management import call_command
from django.core.management.base import SystemCheckError

from core.checks import kiem_phien_chung


def _vps(settings, **them):
    settings.DEBUG = False
    settings.MAIN_APP_URL = "https://erp.vi-du.vn/"
    settings.BANGTINH_URL = "https://crm.vi-du.vn/"
    settings.CSRF_TRUSTED_ORIGINS = ["https://erp.vi-du.vn", "https://crm.vi-du.vn"]
    settings.SESSION_COOKIE_DOMAIN = None
    settings.CSRF_COOKIE_DOMAIN = None
    for k, v in them.items():
        setattr(settings, k, v)


def test_hai_ten_mien_thieu_cookie_domain_la_loi(settings):
    """AC-1.11 — ERP, CRM ở hai tên miền mà chưa đặt tên miền cha cho cookie: kiểm cấu hình báo lỗi tiếng Việt, `check --deploy` dừng"""
    _vps(settings)
    loi = kiem_phien_chung(None)
    assert loi and loi[0].id == "core.E001" and "SESSION_COOKIE_DOMAIN" in loi[0].msg
    with pytest.raises(SystemCheckError):
        call_command("check", "--deploy")


def test_cookie_domain_dung_thi_dat(settings):
    """AC-1.11 — Tên miền cha phủ được cả hai tên miền (`.vi-du.vn`) thì không báo; tên miền cha sai (`.khac.vn`) vẫn báo"""
    _vps(settings, SESSION_COOKIE_DOMAIN=".vi-du.vn", CSRF_COOKIE_DOMAIN=".vi-du.vn")
    assert kiem_phien_chung(None) == []
    _vps(settings, SESSION_COOKIE_DOMAIN=".khac.vn", CSRF_COOKIE_DOMAIN=".vi-du.vn")
    assert [e.id for e in kiem_phien_chung(None)] == ["core.E001"]


def test_may_local_va_mot_ten_mien_khong_bao(settings):
    """AC-1.11 — Máy local (DEBUG) hoặc ERP, CRM chung một tên miền thì không cần tên miền cha"""
    _vps(settings, DEBUG=True)
    assert kiem_phien_chung(None) == []
    _vps(settings, BANGTINH_URL="https://erp.vi-du.vn/crm/", CSRF_TRUSTED_ORIGINS=["https://erp.vi-du.vn"])
    assert kiem_phien_chung(None) == []


def _nap_bangtinh(**env):
    moi = {k: v for k, v in os.environ.items() if k not in ("BANGTINH_GOC", "DJANGO_ALLOWED_HOSTS")}
    moi.update(env, DJANGO_SETTINGS_MODULE="knjsc.settings.bangtinh")
    return subprocess.run([sys.executable, "-c", "import django; django.setup(); from django.conf import settings; print(settings.DEBUG)"],
                          env=moi, capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def test_bangtinh_tren_ten_mien_that_thieu_bangtinh_goc_thi_dung():
    """AC-1.11 — Dịch vụ CRM được cho chạy ở tên miền thật (DJANGO_ALLOWED_HOSTS) mà thiếu BANGTINH_GOC=prod: dừng khởi động với lời nói rõ, không lặng lẽ chạy cấu hình dev; máy local vẫn chạy dev như cũ"""
    kq = _nap_bangtinh(DJANGO_ALLOWED_HOSTS="crm.vi-du.vn")
    assert kq.returncode != 0 and "BANGTINH_GOC" in kq.stderr
    kq = _nap_bangtinh(DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1")
    assert kq.returncode == 0 and kq.stdout.strip() == "True"
