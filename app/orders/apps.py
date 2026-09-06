from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "orders"
    verbose_name = "Đơn hàng"

    def ready(self):
        # Cột Chọn một mang nhãn Sản phẩm lấy danh sách từ danh mục sản phẩm,
        # và "Thêm mới…" tại ô chọn là thêm sản phẩm (Q57). Đăng ký vào sổ của
        # forms_builder lúc khởi động — forms_builder không được import orders
        from .services import product_service

        product_service.register_sources()
