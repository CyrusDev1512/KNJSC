"""Trang quản trị của core.

Điều cấm 12: Django Admin chỉ dùng cho quản trị viên, không dùng cho nghiệp
vụ hằng ngày — nó bỏ qua tầng dịch vụ.

Nhật ký hoạt động ở đây chỉ để tra cứu. Không thêm, không sửa, không xoá
được, kể cả quản trị viên (BR-6).
"""
from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor_label", "action", "target_type", "target_id", "ip_address")
    list_filter = ("action", "target_type")
    search_fields = ("actor_label", "target_id", "detail")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
