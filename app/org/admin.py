"""Trang quản trị của org.

Điều cấm 12: chỉ dùng cho quản trị viên. Nghiệp vụ hằng ngày phải đi qua
tầng dịch vụ, không qua đây.
"""
from django.contrib import admin

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
    list_display = ("full_name", "user", "department", "team", "rank",
                    "must_change_password", "last_login_at")
    list_filter = ("rank", "department", "must_change_password")
    search_fields = ("full_name", "user__username", "user__email")
    list_select_related = ("user", "department", "team")
    readonly_fields = ("failed_login_count", "locked_until", "last_login_at", "session_epoch")
