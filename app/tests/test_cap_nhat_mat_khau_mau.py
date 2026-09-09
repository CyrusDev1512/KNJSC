"""Hồi quy cập nhật đăng nhập mẫu qua launcher, không nạp lại dữ liệu."""
from io import StringIO
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from core.management.commands.cap_nhat_mat_khau_mau import UPDATE_KEY
from core.management.commands.du_lieu_mau import TAI_KHOAN
from core.models import AuditLog
from org.models import UserProfile

pytestmark = pytest.mark.django_db


def account(username, must_change=False):
    user = get_user_model().objects.create_user(username=username, password="old-local")
    return UserProfile.objects.create(user=user, must_change_password=must_change)


def run_update():
    call_command("cap_nhat_mat_khau_mau", stdout=StringIO())


def test_updates_all_samples_preserves_flags_and_other_accounts(settings, client):
    settings.DEBUG = True
    profiles = [account(row[0], row[-1]) for row in TAI_KHOAN]
    other = account("nhan-vien-that")
    other_hash = other.user.password
    run_update()
    for profile, row in zip(profiles, TAI_KHOAN):
        profile.refresh_from_db()
        profile.user.refresh_from_db()
        assert profile.user.check_password("matkhaucuatoi")
        assert not profile.user.check_password("old-local")
        assert profile.must_change_password == row[-1]
        assert profile.session_epoch == 1
    other.user.refresh_from_db()
    assert other.user.password == other_hash
    assert client.login(username="quantri", password="matkhaucuatoi")
    assert AuditLog.objects.filter(target_type=UPDATE_KEY).count() == 12
    assert not AuditLog.objects.filter(detail__contains="matkhaucuatoi").exists()


def test_next_launch_preserves_new_password_and_sessions(settings):
    settings.DEBUG = True
    profile = account("quantri")
    run_update()
    profile.refresh_from_db()
    epoch = profile.session_epoch
    profile.user.set_password("personal-after-update")
    profile.user.save(update_fields=["password"])
    count = AuditLog.objects.count()
    run_update()
    profile.refresh_from_db()
    profile.user.refresh_from_db()
    assert profile.user.check_password("personal-after-update")
    assert profile.session_epoch == epoch
    assert AuditLog.objects.count() == count


def test_production_is_unchanged(settings):
    settings.DEBUG = False
    profile = account("quantri")
    run_update()
    profile.user.refresh_from_db()
    assert profile.user.check_password("old-local")
    assert not AuditLog.objects.filter(target_type=UPDATE_KEY).exists()


def test_empty_database_does_not_block_accounts_created_later(settings):
    settings.DEBUG = True
    run_update()
    assert not get_user_model().objects.exists()
    profile = account("sale.moi", True)
    run_update()
    profile.user.refresh_from_db()
    assert profile.user.check_password("matkhaucuatoi")


def test_failure_rolls_back_passwords_and_completion_markers(settings):
    settings.DEBUG = True
    profile = account("quantri")
    with patch("core.management.commands.cap_nhat_mat_khau_mau.record",
               side_effect=RuntimeError("audit unavailable")):
        with pytest.raises(RuntimeError):
            run_update()
    profile.user.refresh_from_db()
    assert profile.user.check_password("old-local")
    assert not AuditLog.objects.filter(target_type=UPDATE_KEY).exists()
