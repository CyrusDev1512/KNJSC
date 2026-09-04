from django.apps import AppConfig


class CrmConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "crm"
    verbose_name = "CRM"

    def ready(self):
        # Đăng ký sổ danh sách chọn cho bảng vận đơn — một lần, lúc khởi động
        from . import choices

        choices.register_all()
