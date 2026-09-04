"""Các giá trị cố định của module đơn hàng.

Khai ở một chỗ duy nhất (quy tắc 7). Rải ra từng chỗ là ngày nào đó hai nơi
lệch nhau mà không ai biết.
"""
from django.db import models


class Market(models.TextChoices):
    """Thị trường bán hàng — chốt ngày 29.08.2026, backlog Q23.

    Ba nước gộp từ hai nguồn: `README.md` ghi Canada và Philippines,
    `CRM_Tân.xlsx` ghi hàng đi US. Thêm nước mới phải kèm tệp chuyển đổi.
    """

    US = "us", "Hoa Kỳ"
    CA = "ca", "Canada"
    PH = "ph", "Philippines"


class PaymentMethod(models.TextChoices):
    """Phương thức thanh toán, theo cột PTTT trong tệp thật."""

    CARD = "card", "Thẻ"
    TRANSFER = "transfer", "Chuyển khoản"
    COD = "cod", "Thu hộ khi giao"
    WALLET = "wallet", "Ví điện tử"


class ShippingStatus(models.TextChoices):
    """Trạng thái vận chuyển. Bộ phận Vận đơn sửa thẳng trên bảng — Q26."""

    PENDING = "pending", "Chờ xử lý"
    SHIPPING = "shipping", "Đang giao"
    DELIVERED = "delivered", "Đã giao"
    RETURNED = "returned", "Hoàn hàng"


class PaymentStatus(models.TextChoices):
    """Trạng thái thanh toán."""

    UNPAID = "unpaid", "Chờ thanh toán"
    PAID = "paid", "Đã thanh toán"
    FAILED = "failed", "Thất bại"


#: Tên kỹ thuật của bảng vận đơn. Đơn hàng ghi một chiều sang bảng này.
WAYBILL_TABLE_CODE = "van_don"

#: Tên kỹ thuật và tên hiển thị của bộ phận sở hữu bảng vận đơn. Lệnh
#: `tao_bang_van_don` tự tạo bộ phận này trên máy sạch nếu chưa có.
WAYBILL_DEPARTMENT_CODE = "van-don"
WAYBILL_DEPARTMENT_NAME = "Vận đơn"
