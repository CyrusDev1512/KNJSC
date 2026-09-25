"""Quyền quản lý tài khoản, độc lập với quyền sửa hồ sơ và quyền xem dữ liệu."""
from contextlib import contextmanager

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from core.audit import record
from core.constants import AuditAction, Rank
from core.exceptions import BusinessError, OutOfScopeError
from core.scope import get_user_scope
from org.models import UserProfile


class AccountPolicy:
    """Một lần tính phạm vi cho cả trang; không hỏi DB theo từng nút/dòng."""

    def __init__(self, actor):
        self.actor = actor
        self.scope = get_user_scope(actor)

    def can_manage(self, profile):
        actor_profile = getattr(self.actor, "profile", None)
        if (not self.actor.is_active or profile.deleted_at is not None
                or (actor_profile and actor_profile.deleted_at is not None)
                or profile.user_id == self.actor.pk):
            return False
        rank = self.scope.rank
        # Superuser vẫn được bảo vệ như Admin nếu hồ sơ bị gán cấp thấp hơn.
        target_rank = Rank.ADMIN if profile.user.is_superuser else profile.rank
        if rank == Rank.ADMIN:
            return True
        if rank == Rank.CEO:
            return target_rank in (Rank.STAFF, Rank.LEADER, Rank.MANAGER)
        if rank == Rank.MANAGER:
            return (target_rank in (Rank.STAFF, Rank.LEADER)
                    and profile.department_id in self.scope.department_ids)
        return (rank == Rank.LEADER and target_rank == Rank.STAFF
                and profile.team_id in self.scope.team_ids)

    def require(self, profile):
        if not self.can_manage(profile):
            raise OutOfScopeError("Bạn không có quyền quản lý tài khoản này.")


@contextmanager
def locked_target(actor, profile_id):
    """Khóa tài khoản trước hồ sơ; kiểm lại quyền từ DB, không dùng object cũ.

    Giữ cùng thứ tự ID cho actor/target và Admin để hai lượt xóa chéo không
    vượt kiểm Admin cuối. Các thao tác sửa hồ sơ/khóa dùng chung ranh giới này.
    """
    User = get_user_model()
    with transaction.atomic():
        target_user_id = UserProfile.all_objects.filter(pk=profile_id).values_list("user_id", flat=True).first()
        if target_user_id is None:
            raise Http404
        users = list(User.objects.filter(
            Q(pk__in=[actor.pk, target_user_id]) | Q(profile__rank=Rank.ADMIN) | Q(is_superuser=True)
        ).order_by("pk").select_for_update(of=("self",)))
        fresh_actor = next((user for user in users if user.pk == actor.pk), None)
        if fresh_actor is None or not fresh_actor.is_active:
            raise OutOfScopeError()
        profile = (UserProfile.all_objects.select_for_update(of=("self",))
                   .select_related("user", "department", "team").get(pk=profile_id))
        if profile.deleted_at is not None:
            raise Http404
        if getattr(getattr(fresh_actor, "profile", None), "deleted_at", None):
            raise OutOfScopeError()
        yield fresh_actor, profile


@sensitive_variables("password")
def reset_account_password(profile_id, password, *, actor, request=None):
    from .account_service import reset_password
    with locked_target(actor, profile_id) as (current_actor, profile):
        AccountPolicy(current_actor).require(profile)
        validate_password(password, profile.user)
        return reset_password(profile, password, actor=current_actor, request=request)


def delete_account(profile_id, *, actor, request=None):
    with locked_target(actor, profile_id) as (current_actor, profile):
        AccountPolicy(current_actor).require(profile)
        if profile.rank == Rank.ADMIN or profile.user.is_superuser:
            admins = get_user_model().objects.filter(
                profile__deleted_at__isnull=True, is_active=True,
            ).filter(Q(profile__rank=Rank.ADMIN) | Q(is_superuser=True))
            if profile.user.is_active and admins.count() <= 1:
                raise BusinessError("Không được xóa Admin hoạt động cuối cùng.")
        profile.deleted_at = timezone.now()
        profile.deleted_by = current_actor
        profile.invalidate_sessions()
        profile.save(update_fields=["deleted_at", "deleted_by", "session_epoch", "updated_at"])
        profile.user.is_active = False
        profile.user.set_unusable_password()
        profile.user.save(update_fields=["is_active", "password"])
        record(AuditAction.DELETE, actor=current_actor, target=profile,
               detail="Xóa mềm tài khoản; giữ dữ liệu và liên kết lịch sử", request=request)
        return profile


def require_live_profile(profile):
    """Primitive nội bộ cũng không được mở lại hoặc sửa hồ sơ đã xóa."""
    get_user_model().objects.select_for_update().get(pk=profile.user_id)
    if UserProfile.all_objects.filter(pk=profile.pk, deleted_at__isnull=False).exists():
        raise BusinessError("Tài khoản đã xóa không thể sửa hoặc mở khóa.")
