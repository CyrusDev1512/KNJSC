"""Quy tắc quản lý tài khoản.

Tầng dịch vụ, không biết gì về HTTP. Cả giao diện web lẫn tác vụ nền đều
gọi vào đây.
"""
from django.contrib.auth import get_user_model
from django.db import transaction

from core.audit import record
from core.constants import AuditAction, Rank

from ..models import UserProfile


@transaction.atomic
def create_account(*, username, email, full_name, rank=Rank.STAFF,
                   department=None, team=None, password=None, actor=None, request=None):
    """Tạo tài khoản kèm hồ sơ nhân sự.

    Mật khẩu đặt lần đầu luôn phải đổi ở lần đăng nhập kế tiếp (FR-1.3).
    """
    User = get_user_model()
    user = User(username=username, email=email, is_active=True)
    # Admin có tất cả các quyền, gồm cả trang quản trị Django (điều cấm 12:
    # trang đó chỉ dành cho quản trị viên, không dùng cho nghiệp vụ hằng ngày)
    if rank == Rank.ADMIN:
        user.is_staff = True
        user.is_superuser = True
    if password:
        user.set_password(password)
    else:
        user.set_unusable_password()
    user.save()

    profile = UserProfile.objects.create(
        user=user, full_name=full_name, rank=rank,
        department=department, team=team, must_change_password=True,
    )
    record(
        AuditAction.CREATE, actor=actor, target=user,
        detail=f"Tạo tài khoản cấp bậc {rank}", request=request,
    )
    return profile


#: Nhãn tiếng Việt của các trường được phép sửa, dùng khi ghi nhật ký
PROFILE_FIELD_LABELS = {
    "full_name": "Họ tên",
    "rank": "Cấp bậc",
    "department": "Bộ phận",
    "team": "Team",
}


def _nhan_gia_tri(profile, ten, gia_tri):
    """Hiển thị một giá trị theo cách người đọc nhật ký hiểu được.

    Trường có danh sách lựa chọn thì lấy nhãn tiếng Việt, không ghi mã thô —
    người vận hành đọc `Nhân viên → Quản lý` chứ không phải `staff → manager`.
    """
    if gia_tri in (None, ""):
        return "—"
    truong = profile._meta.get_field(ten)
    lua_chon = getattr(truong, "choices", None)
    if lua_chon:
        return dict(lua_chon).get(gia_tri, gia_tri)
    return str(gia_tri)


def snapshot_profile(profile, fields=None):
    """Chụp lại giá trị hiện tại của hồ sơ, để so sánh sau khi sửa.

    Phải gọi **trước** khi `ModelForm.is_valid()` chạy: form gắn với instance
    sẽ ghi đè giá trị mới lên chính đối tượng đó ngay trong lúc kiểm tra, nên
    sau đó không còn giá trị cũ để so.
    """
    fields = fields or PROFILE_FIELD_LABELS.keys()
    return {ten: getattr(profile, ten) for ten in fields}


@transaction.atomic
def update_profile(profile, changes, *, before=None, actor=None, request=None):
    """Cập nhật hồ sơ nhân sự và ghi lại đúng những gì đã đổi.

    BR-5: mọi thao tác thay đổi dữ liệu phải ghi vào nhật ký. Trước đây màn
    hình sửa hồ sơ gọi thẳng `form.save()`, nên đổi cấp bậc không để lại dấu
    vết nào — vừa vi phạm BR-5, vừa bỏ qua tầng dịch vụ.

    `changes` là dict tên trường sang giá trị mới. `before` là ảnh chụp giá
    trị cũ lấy bằng `snapshot_profile`; bỏ trống thì so với chính đối tượng.
    """
    goc = before if before is not None else snapshot_profile(profile, changes.keys())
    da_doi = []
    for ten, moi in changes.items():
        cu = goc.get(ten)
        if cu == moi:
            continue
        nhan = PROFILE_FIELD_LABELS.get(ten, ten)
        da_doi.append(
            f"{nhan}: {_nhan_gia_tri(profile, ten, cu)}"
            f" → {_nhan_gia_tri(profile, ten, moi)}"
        )
        setattr(profile, ten, moi)

    if not da_doi:
        return profile

    # Đổi cấp bậc, bộ phận hoặc team làm phiên đang mở mất hiệu lực ngay (P4);
    # phần đó do UserProfile.save() lo
    profile.save()

    if "rank" in changes:
        la_admin = profile.rank == Rank.ADMIN
        if profile.user.is_staff != la_admin or profile.user.is_superuser != la_admin:
            profile.user.is_staff = la_admin
            profile.user.is_superuser = la_admin
            profile.user.save(update_fields=["is_staff", "is_superuser"])

    record(
        AuditAction.UPDATE, actor=actor, target=profile,
        detail="Sửa hồ sơ — " + " · ".join(da_doi), request=request,
    )
    return profile


@transaction.atomic
def set_rank(profile, rank, *, actor=None, request=None):
    """Đổi cấp bậc. Phiên đang mở mất hiệu lực ngay (P4)."""
    cu = profile.rank
    profile.rank = rank
    profile.save(update_fields=["rank"])
    # Lên hoặc xuống khỏi Admin thì quyền vào trang quản trị đổi theo
    la_admin = rank == Rank.ADMIN
    if profile.user.is_staff != la_admin or profile.user.is_superuser != la_admin:
        profile.user.is_staff = la_admin
        profile.user.is_superuser = la_admin
        profile.user.save(update_fields=["is_staff", "is_superuser"])
    record(
        AuditAction.PERMISSION, actor=actor, target=profile,
        detail=f"Đổi cấp bậc {cu} sang {rank}", request=request,
    )
    return profile


@transaction.atomic
def lock_account(profile, *, actor=None, request=None):
    """Khoá tài khoản. Phiên đang mở mất hiệu lực ngay (P4)."""
    profile.user.is_active = False
    profile.user.save(update_fields=["is_active"])
    profile.invalidate_sessions()
    profile.save(update_fields=["session_epoch"])
    record(
        AuditAction.PERMISSION, actor=actor, target=profile,
        detail="Khoá tài khoản, phiên đang mở bị huỷ", request=request,
    )
    return profile


@transaction.atomic
def unlock_account(profile, *, actor=None, request=None):
    profile.user.is_active = True
    profile.user.save(update_fields=["is_active"])
    profile.failed_login_count = 0
    profile.locked_until = None
    profile.save(update_fields=["failed_login_count", "locked_until"])
    record(
        AuditAction.PERMISSION, actor=actor, target=profile,
        detail="Mở khoá tài khoản", request=request,
    )
    return profile


@transaction.atomic
def reset_password(profile, new_password, *, actor=None, request=None):
    """Đặt lại mật khẩu. Người dùng phải đổi ở lần đăng nhập kế tiếp."""
    profile.user.set_password(new_password)
    profile.user.save(update_fields=["password"])
    profile.must_change_password = True
    profile.failed_login_count = 0
    profile.locked_until = None
    profile.invalidate_sessions()
    profile.save(update_fields=[
        "must_change_password", "failed_login_count", "locked_until", "session_epoch",
    ])
    # Không ghi mật khẩu vào nhật ký, kể cả khi gỡ lỗi
    record(
        AuditAction.PERMISSION, actor=actor, target=profile,
        detail="Đặt lại mật khẩu", request=request,
    )
    return profile
