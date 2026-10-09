from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "orders"
    verbose_name = "Đơn hàng"

    def ready(self):
        # Cột Chọn một mang nhãn Sản phẩm lấy danh sách từ danh mục sản phẩm,
        # và "Thêm mới…" tại ô chọn là thêm sản phẩm (Q61). Đăng ký vào sổ của
        # forms_builder lúc khởi động — forms_builder không được import orders
        from django.apps import apps
        from django.db.models.signals import pre_migrate

        from .services import integrity_service, product_service, waybill_service

        product_service.register_sources()
        waybill_service.register()
        # Còn mã đơn trùng thì `migrate` dừng trước khi áp `forms_builder/0017`, kèm cách gỡ (TL-76)
        pre_migrate.connect(integrity_service.chan_migrate_khi_trung_ma, sender=apps.get_app_config("forms_builder"),
                            dispatch_uid="orders.chan_migrate_khi_trung_ma")
