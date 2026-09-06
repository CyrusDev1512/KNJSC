from django.apps import AppConfig


class FormsBuilderConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "forms_builder"
    verbose_name = "Biểu mẫu và bảng động"

    def ready(self):
        # Nguồn danh sách chọn mà chính module này biết: cột Chọn một mang
        # nhãn Người bán gợi ý nhân sự bộ phận — một lần, lúc khởi động
        from .services import choice_service

        choice_service.register_sources()
