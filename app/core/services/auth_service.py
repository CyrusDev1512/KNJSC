"""Quy tắc đăng nhập.

FR-1.1 đăng nhập bằng email và mật khẩu.
FR-1.2 khoá tạm tài khoản 15 phút sau 5 lần đăng nhập sai liên tiếp.

Mỗi lần thử **giữ chỗ** trong bộ đếm (khoá dòng hồ sơ) trước khi kiểm mật khẩu — `reserve_attempt`. Đếm sau khi kiểm
thì nhiều yêu cầu gửi cùng lúc đều đọc "chưa bị khoá" và đều được thử mật khẩu: đo 40/40 lần (AC-1.9).

Đếm số lần sai theo tài khoản chứ không theo địa chỉ IP: người dùng nội bộ
hay dùng chung một đường mạng, đếm theo IP sẽ khoá nhầm cả phòng.
"""
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
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


def reserve_attempt(user):
    """Giữ chỗ một lần thử đăng nhập trước khi kiểm mật khẩu. Trả False nếu tài khoản đang bị khoá tạm.

    Khoá dòng hồ sơ nên các lần thử cùng lúc xếp hàng: lần thứ `LOGIN_MAX_FAILED` đặt khoá, các lần sau thấy khoá và
    không được kiểm mật khẩu. Lần giữ chỗ thành công rồi đăng nhập đúng thì `note_successful_login` xoá cả bộ đếm lẫn
    khoá — sai 4 lần rồi lần thứ 5 đúng vẫn vào được như trước (AC-1.2, AC-1.9).
    """
    profile = _profile_of(user)
    if profile is None:
        return True
    gioi_han = getattr(settings, "LOGIN_MAX_FAILED", 5)
    phut_khoa = getattr(settings, "LOGIN_LOCK_MINUTES", 15)
    with transaction.atomic():
        hs = type(profile).all_objects.select_for_update().get(pk=profile.pk)
        # Chép mốc khoá mới nhất về hồ sơ người gọi đang giữ, để lời "thử lại sau N phút" tính đúng
        profile.locked_until = hs.locked_until
        if hs.locked_until and hs.locked_until > timezone.now():
            return False
        hs.failed_login_count += 1
        cot = ["failed_login_count"]
        if hs.failed_login_count >= gioi_han:
            hs.locked_until = timezone.now() + timedelta(minutes=phut_khoa)
            hs.failed_login_count = 0
            cot.append("locked_until")
        hs.save(update_fields=cot)
    profile.locked_until, profile.failed_login_count = hs.locked_until, hs.failed_login_count
    return True


def note_failed_login(username, request=None):
    """Ghi nhật ký một lần đăng nhập sai; lần sai này làm tài khoản bị khoá thì ghi thêm "Khoá tạm".

    Bộ đếm đã tăng ở `reserve_attempt` trước khi kiểm mật khẩu. Không được để lộ ra giao diện tài khoản có tồn tại hay
    không.
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
        return
    profile.refresh_from_db(fields=["failed_login_count", "locked_until"])
    if profile.failed_login_count == 0 and is_locked(user):
        gioi_han = getattr(settings, "LOGIN_MAX_FAILED", 5)
        phut_khoa = getattr(settings, "LOGIN_LOCK_MINUTES", 15)
        record(
            AuditAction.PERMISSION, actor=user, target=profile,
            detail=f"Khoá tạm {phut_khoa} phút do sai mật khẩu {gioi_han} lần",
            request=request,
        )


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
