from django.apps import AppConfig


class CrmConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "crm"
    verbose_name = "CRM"

    def ready(self):
        # Đăng ký sổ danh sách chọn cho bảng vận đơn — một lần, lúc khởi động
        from forms_builder.services import export_service

        from . import choices
        from .services import grid_service

        from forms_builder.record_policies import register_grid
        from orders.constants import WAYBILL_TABLE_CODE
        from .services import waybill_grid
        register_grid(WAYBILL_TABLE_CODE, waybill_grid)
        choices.register_all()
        # Nút Xuất Excel trên Bảng tính xuất đúng lưới đang hiện, kể cả hai bộ
        # lọc riêng của lưới (`trung`, `sp`) — ADR-002
        export_service.register_builder("grid", grid_service.export_queryset)
