from django.apps import AppConfig


class ReportsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reports"
    verbose_name = "Báo cáo"

    def ready(self):
        from forms_builder.choice_registry import register
        from orders.constants import Market

        for table_code in ("bao_cao_sale", "bao_cao_mkt"):
            register(table_code, "thi_truong", lambda: list(Market.labels))
