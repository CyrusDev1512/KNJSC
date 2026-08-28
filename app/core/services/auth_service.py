"""Quy tắc đăng nhập.

FR-1.1 đăng nhập bằng email và mật khẩu.
FR-1.2 khoá tạm tài khoản 15 phút sau 5 lần đăng nhập sai liên tiếp.

Đếm số lần sai theo tài khoản chứ không theo địa chỉ IP: người dùng nội bộ
hay dùng chung một đường mạng, đếm theo IP sẽ khoá nhầm cả phòng.
"""
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from ..audit import record
from ..constants import AuditAction


def _profile_of(user):
    return getattr(user, "profile", None) if user is not None else None


def find_user(username):
    """Tìm tài khoản theo tên đăng nhập hoặc email. Không có thì trả None."""
    User = get_user_model()
    return (
        User.objects.filter(username__iexact=username).first()
        or User.objects.filter(email__iexact=username).first()
    )


def lock_remaining(user):
    """Còn bị khoá bao nhiêu giây. Trả 0 nếu không bị khoá."""
    profile = _profile_of(user)
    if profile is None or not profile.locked_until:
        return 0
    con_lai = (profile.locked_until - timezone.now()).total_seconds()
    return max(0, int(con_lai))


def is_locked(user):
    return lock_remaining(user) > 0


def note_failed_login(username, request=None):
    """Ghi nhận một lần đăng nhập sai. Khoá tài khoản nếu đủ số lần.

    Trả về số lần sai còn lại trước khi bị khoá, hoặc None nếu không có
    tài khoản nào tên như vậy. Không được để lộ tài khoản có tồn tại hay
    không ra giao diện.
    """
    user = find_user(username)
    record(
        AuditAction.LOGIN_FAILED,
        actor=user,
        actor_label=username[:150],
        detail="Đăng nhập thất bại",
        request=request,
    )
    profile = _profile_of(user)
    if profile is None:
        return None

    gioi_han = getattr(settings, "LOGIN_MAX_FAILED", 5)
    phut_khoa = getattr(settings, "LOGIN_LOCK_MINUTES", 15)

    profile.failed_login_count += 1
    if profile.failed_login_count >= gioi_han:
        profile.locked_until = timezone.now() + timedelta(minutes=phut_khoa)
        profile.failed_login_count = 0
        profile.save(update_fields=["failed_login_count", "locked_until"])
        record(
            AuditAction.PERMISSION, actor=user, target=profile,
            detail=f"Khoá tạm {phut_khoa} phút do sai mật khẩu {gioi_han} lần",
            request=request,
        )
        return 0

    profile.save(update_fields=["failed_login_count"])
    return gioi_han - profile.failed_login_count


def note_successful_login(user, request=None):
    """Xoá bộ đếm và ghi nhật ký sau khi đăng nhập thành công."""
    profile = _profile_of(user)
    if profile is not None:
        profile.failed_login_count = 0
        profile.locked_until = None
        profile.last_login_at = timezone.now()
        profile.save(update_fields=["failed_login_count", "locked_until", "last_login_at"])
    record(AuditAction.LOGIN, actor=user, detail="Thành công", request=request)


def note_logout(user, request=None):
    record(AuditAction.LOGOUT, actor=user, request=request)
