from django.apps import AppConfig


class CoreTestsConfig(AppConfig):
    """App chỉ bật khi chạy kiểm thử, giữ model dùng để thử phạm vi quyền."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core.tests"
    label = "core_tests"
    verbose_name = "Kiểm thử core"
