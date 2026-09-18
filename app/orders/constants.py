"""Các giá trị cố định của module đơn hàng.

Khai ở một chỗ duy nhất (quy tắc 7). Rải ra từng chỗ là ngày nào đó hai nơi
lệch nhau mà không ai biết.
"""
from django.db import models


class Market(models.TextChoices):
    """Thị trường bán hàng — chốt ngày 29.08.2026 (Q23), mở rộng 18.09.2026 (ADR-031 bổ sung).

    Ba nước đầu gộp từ hai nguồn: `README.md` ghi Canada và Philippines,
    `CRM_Tân.xlsx` ghi hàng đi US. Bốn thị trường sau theo sheet Quy ước-Định nghĩa
    và ví dụ báo cáo MKT của `Quản trị nội bộ.xlsx`. Thêm nước mới phải kèm tệp
    chuyển đổi và một cặp trong `currency_service.MARKET_CURRENCIES`.
    """

    US = "us", "Hoa Kỳ"
    CA = "ca", "Canada"
    PH = "ph", "Philippines"
    EU = "eu", "Châu Âu"
    KR = "kr", "Hàn Quốc"
    JP = "jp", "Nhật Bản"
    AU = "au", "Úc"


class PaymentMethod(models.TextChoices):
    """Phương thức thanh toán, theo cột PTTT trong tệp thật."""

    CARD = "card", "Thẻ"
    TRANSFER = "transfer", "Chuyển khoản"
    COD = "cod", "Thu hộ khi giao"
    WALLET = "wallet", "Ví điện tử"
    ZELLE = "zelle", "Zelle"
    PAYPAL = "paypal", "PayPal"


# Giữ mã cũ để đọc lịch sử; chỉ hai phương thức này dùng cho thao tác mới.
ACTIVE_PAYMENT_METHODS = (PaymentMethod.ZELLE, PaymentMethod.PAYPAL)
ACTIVE_PAYMENT_CHOICES = [(method.value, method.label) for method in ACTIVE_PAYMENT_METHODS]
ACTIVE_PAYMENT_LABELS = [method.label for method in ACTIVE_PAYMENT_METHODS]


class ShippingStatus(models.TextChoices):
    """Trạng thái vận đơn — **đúng tám giá trị của tệp thật** (Q40, ADR-009).

    Bộ phận Vận đơn cập nhật trên Bảng tính. Bảng vận đơn lưu *nhãn* (chuỗi
    tiếng Việt) chứ không lưu mã, để tệp Excel xuất ra và nhập lại đều đọc
    được bằng mắt. Đổi nhãn là đổi dữ liệu — phải có tệp chuyển đổi.
    """

    DA_LEN_DON = "da_len_don", "Đã lên đơn"
    HUY_TRUOC_GIAO = "huy_truoc_giao", "Hủy trước giao"
    HUY_SAU_GIAO = "huy_sau_giao", "Hủy sau giao"
    DANG_GIAO = "dang_giao", "Đang giao"
    DA_NHAN_HANG = "da_nhan_hang", "Đã nhận hàng"
    HEN_LAI = "hen_lai", "Hẹn lại"
    KHACH_VANG = "khach_vang", "Khách vắng"
    HOAN_DON = "hoan_don", "Hoàn đơn"


class PaymentStatus(models.TextChoices):
    """Trạng thái thanh toán — ba giá trị của tệp thật (Q40)."""

    UNPAID = "unpaid", "Chưa thanh toán"
    PAID = "paid", "Đã thanh toán"
    PARTIAL = "partial", "Thanh toán 1 phần"


class Reconciliation(models.TextChoices):
    """Đối soát kế toán — tệp thật chỉ đánh dấu một giá trị khi tiền đã về."""

    DA_VE_TK = "da_ve_tk", "Đã về TK"


#: Nhãn cũ (trước 03.09.2026) → nhãn mới, cho tệp chuyển đổi dữ liệu và cho
#: tệp Excel cũ nhập lại. Nhãn không có trong bảng này giữ nguyên.
LEGACY_SHIPPING_LABELS = {
    "Chờ xử lý": ShippingStatus.DA_LEN_DON.label,
    "Đã giao": ShippingStatus.DA_NHAN_HANG.label,
    "Hoàn hàng": ShippingStatus.HOAN_DON.label,
}
LEGACY_PAYMENT_LABELS = {
    "Chờ thanh toán": PaymentStatus.UNPAID.label,
    "Thất bại": PaymentStatus.UNPAID.label,
}


#: Tên kỹ thuật của bảng vận đơn. Đơn hàng ghi một chiều sang bảng này.
WAYBILL_TABLE_CODE = "van_don"

#: Một bảng vận đơn duy nhất từ 18.09.2026 (ADR-036): "Vận đơn mới", mã `van_don`.
#: Tên `ACTIVE_WAYBILL_TABLE_CODE` giữ lại làm bí danh cho mã đang dùng khắp nơi.
ACTIVE_WAYBILL_TABLE_CODE = WAYBILL_TABLE_CODE

#: Tên kỹ thuật và tên hiển thị của bộ phận sở hữu bảng vận đơn. Lệnh
#: `tao_bang_van_don` tự tạo bộ phận này trên máy sạch nếu chưa có.
WAYBILL_DEPARTMENT_CODE = "van-don"
WAYBILL_DEPARTMENT_NAME = "Vận đơn"


def is_waybill_table(table):
    """Profile vận hành giữ nguyên cả khi bảng ngừng nhận đơn mới."""
    return table.code == ACTIVE_WAYBILL_TABLE_CODE or getattr(table, "workflow", "") == "waybill"


def waybill_condition(prefix="table__"):
    from django.db.models import Q
    return Q(**{prefix + "code": ACTIVE_WAYBILL_TABLE_CODE}) | Q(**{prefix + "workflow": "waybill"})
