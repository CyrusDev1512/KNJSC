"""Bảy nhãn ý nghĩa và cách dùng.

Chốt ở ADR-007, lấy theo `docs/03-thiet-ke-ky-thuat.md` mục 2.5.

**Nhãn nói về nghiệp vụ, không nói về kiểu dữ liệu.** Kiểu đã có ở
`FieldDef.field_type`; nhãn cho hệ thống biết giá trị đó *đại diện cho cái gì*,
và nhờ đó báo cáo tổng hợp mới biết cộng hay đếm hay nhóm theo nó.

Cột có nhãn được **tách ra cột riêng có chỉ mục** trên `DataRecord`, không nằm
trong JSON — nếu để trong JSON thì lọc và thống kê sẽ chậm (ADR-001).

Khai ở một chỗ duy nhất (quy tắc 7). Thêm nhãn thứ tám phải kèm tệp chuyển
đổi cấu trúc, không sửa nóng.
"""
from django.db import models


class Meaning(models.TextChoices):
    """Bảy nhãn ý nghĩa. Giá trị lưu trong cơ sở dữ liệu là chuỗi tiếng Anh."""

    DATE = "date", "Ngày"
    CUSTOMER = "customer", "Khách hàng"
    PHONE = "phone", "Số điện thoại"
    REVENUE = "revenue", "Doanh thu"
    SELLER = "seller", "Người bán"
    PRODUCT = "product", "Sản phẩm"
    STATUS = "status", "Trạng thái"


class FieldType(models.TextChoices):
    """Kiểu dữ liệu của một trường."""

    TEXT = "text", "Chữ ngắn"
    LONG_TEXT = "long_text", "Chữ dài"
    INTEGER = "integer", "Số nguyên"
    DECIMAL = "decimal", "Số thập phân"
    MONEY = "money", "Tiền"
    DATE = "date", "Ngày"
    DATETIME = "datetime", "Ngày giờ"
    BOOLEAN = "boolean", "Đúng sai"
    CHOICE = "choice", "Chọn một"


class Aggregation(models.TextChoices):
    """Phép tính mà báo cáo tổng hợp làm được trên một cột."""

    SUM = "sum", "Cộng tổng"
    AVERAGE = "average", "Trung bình"
    COUNT = "count", "Đếm"
    COUNT_DISTINCT = "count_distinct", "Đếm giá trị khác nhau"
    GROUP = "group", "Nhóm theo"


#: Cột vật lý trên `DataRecord` ứng với mỗi nhãn.
#: Đổi tên ở đây là phải viết tệp chuyển đổi cấu trúc.
COLUMN_OF = {
    Meaning.DATE: "val_date",
    Meaning.CUSTOMER: "val_customer",
    Meaning.PHONE: "val_phone",
    Meaning.REVENUE: "val_revenue",
    Meaning.SELLER: "val_seller",
    Meaning.PRODUCT: "val_product",
    Meaning.STATUS: "val_status",
}

#: Kiểu dữ liệu mà mỗi nhãn nhận. Gán nhãn cho trường sai kiểu thì bị chặn.
ALLOWED_TYPES = {
    Meaning.DATE: {FieldType.DATE, FieldType.DATETIME},
    Meaning.CUSTOMER: {FieldType.TEXT},
    Meaning.PHONE: {FieldType.TEXT},
    Meaning.REVENUE: {FieldType.MONEY, FieldType.DECIMAL, FieldType.INTEGER},
    Meaning.SELLER: {FieldType.TEXT, FieldType.CHOICE},
    Meaning.PRODUCT: {FieldType.TEXT, FieldType.CHOICE},
    Meaning.STATUS: {FieldType.TEXT, FieldType.CHOICE},
}

#: Báo cáo tổng hợp làm được gì trên cột mang nhãn này.
AGGREGATIONS = {
    Meaning.DATE: (Aggregation.GROUP, Aggregation.COUNT),
    Meaning.CUSTOMER: (Aggregation.COUNT_DISTINCT, Aggregation.GROUP),
    Meaning.PHONE: (Aggregation.COUNT_DISTINCT,),
    Meaning.REVENUE: (Aggregation.SUM, Aggregation.AVERAGE),
    Meaning.SELLER: (Aggregation.GROUP, Aggregation.COUNT),
    Meaning.PRODUCT: (Aggregation.GROUP, Aggregation.COUNT),
    Meaning.STATUS: (Aggregation.GROUP, Aggregation.COUNT),
}

#: Mô tả ngắn, hiện ngay dưới ô chọn nhãn trong trình tạo biểu mẫu.
HINTS = {
    Meaning.DATE: "Lọc theo khoảng thời gian",
    Meaning.CUSTOMER: "Đếm khách mới, khách cũ",
    Meaning.PHONE: "Phát hiện khách mua lại — FR-6.7",
    Meaning.REVENUE: "Cộng tổng, tính trung bình",
    Meaning.SELLER: "Thống kê theo nhân viên",
    Meaning.PRODUCT: "Thống kê theo sản phẩm",
    Meaning.STATUS: "Lọc và đếm theo trạng thái",
}

#: Nhãn chỉ được gán cho đúng một cột trong mỗi bảng. Hai cột cùng mang nhãn
#: Doanh thu thì hệ thống không biết cộng cột nào.
UNIQUE_PER_TABLE = True


def column_of(meaning):
    """Cột vật lý ứng với một nhãn. Không có nhãn thì trả None."""
    return COLUMN_OF.get(meaning)


def allows(meaning, field_type):
    """Nhãn này có nhận kiểu dữ liệu đó không."""
    return field_type in ALLOWED_TYPES.get(meaning, set())


def aggregations_for(meaning):
    """Các phép tính báo cáo tổng hợp làm được trên nhãn này."""
    return AGGREGATIONS.get(meaning, ())


def can_sum(meaning):
    """Nhãn này cộng tổng được không. Dùng cho dòng tổng cộng — FR-5.4."""
    return Aggregation.SUM in aggregations_for(meaning)


def can_group(meaning):
    """Nhãn này nhóm được không. Dùng cho bốn cách nhóm — FR-5.1."""
    return Aggregation.GROUP in aggregations_for(meaning)


def choices_with_hint():
    """Danh sách lựa chọn cho ô chọn nhãn, kèm mô tả ngắn."""
    return [("", "Không gán")] + [
        (m.value, f"{m.label} — {HINTS[m]}") for m in Meaning
    ]
