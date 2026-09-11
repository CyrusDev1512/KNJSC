"""Đơn vị phổ biến và bản chụp đơn vị khi ghi chi tiết."""
from core.exceptions import BusinessError

COMMON_UNITS = ("hộp", "cái", "chiếc", "túi")


def resolve_unit(product, value=None, *, previous=None, allow_custom=False):
    # Caller cũ thiếu trường vẫn dùng danh mục hoặc bản chụp hiện có.
    if value is None:
        value = previous if previous is not None else product.unit
    if not isinstance(value, str) or len(value) > 40:
        raise BusinessError("Đơn vị tính không hợp lệ.")
    value = value.strip()
    # Rỗng biểu thị bản ghi cũ chưa biết đơn vị; không suy lại lịch sử.
    if not allow_custom and value not in (*COMMON_UNITS, product.unit, previous, ""):
        raise BusinessError("Chọn đơn vị tính trong danh sách của sản phẩm.")
    return value
