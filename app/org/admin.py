"""Trang quản trị của org.

Điều cấm 12: chỉ dùng cho quản trị viên. Nghiệp vụ hằng ngày phải đi qua
tầng dịch vụ, không qua đây.
"""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from core.constants import Rank
from core.permissions import assert_rank
from .services.account_management import locked_target

from .models import Department, Team, UserProfile


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "leader", "is_active")
    list_filter = ("department", "is_active")
    search_fields = ("name",)
    autocomplete_fields = ("leader",)
    list_select_related = ("department", "leader")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        # ModelForm đã thay instance; khóa và kiểm bản hiện hành trước khi ghi.
        if change:
            with locked_target(request.user, obj.pk) as (actor, current):
                assert_rank(actor, Rank.ADMIN)
                super().save_model(request, obj, form, change)
                self._sync_admin_flags(obj)
        else:
            super().save_model(request, obj, form, change)
            self._sync_admin_flags(obj)

    @staticmethod
    def _sync_admin_flags(profile):
        admin_rank = profile.rank == Rank.ADMIN
        get_user_model().objects.filter(pk=profile.user_id).update(
            is_staff=admin_rank, is_superuser=admin_rank)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return (obj is None or obj.deleted_at is None) and super().has_change_permission(request, obj)

    list_display = ("staff_code", "full_name", "user", "department", "team", "rank",
                    "must_change_password", "last_login_at")
    list_filter = ("rank", "department", "must_change_password")
    search_fields = ("staff_code", "full_name", "user__username", "user__email")
    list_select_related = ("user", "department", "team")
    readonly_fields = ("failed_login_count", "locked_until", "last_login_at", "session_epoch", "deleted_at", "deleted_by")


class PreservedUserAdmin(UserAdmin):
    """Không cho xóa cứng hoặc phục hồi tài khoản đã xóa qua Django admin."""

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        profile = getattr(obj, "profile", None)
        return (profile is None or profile.deleted_at is None) and super().has_change_permission(request, obj)

    def save_model(self, request, obj, form, change):
        profile = getattr(obj, "profile", None)
        if change and profile is not None:
            with locked_target(request.user, profile.pk) as (actor, current):
                assert_rank(actor, Rank.ADMIN)
                obj.is_staff = obj.is_superuser = current.rank == Rank.ADMIN
                super().save_model(request, obj, form, change)
        else:
            super().save_model(request, obj, form, change)


admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), PreservedUserAdmin)
