"""Các giá trị cố định của toàn hệ thống.

Khai báo ở một chỗ duy nhất, không viết rải rác (quy tắc 7).
"""
from django.db import models


class Rank(models.TextChoices):
    """Cấp bậc — quyết định phạm vi rộng bao nhiêu (ADR-003)."""

    STAFF = "staff", "Nhân viên"
    LEADER = "leader", "Trưởng nhóm"
    MANAGER = "manager", "Quản lý"
    ADMIN = "admin", "Quản trị viên"


# Thứ bậc để so sánh. Không dùng thứ tự chữ cái vì nó sai.
RANK_LEVEL = {
    Rank.STAFF: 10,
    Rank.LEADER: 20,
    Rank.MANAGER: 30,
    Rank.ADMIN: 40,
}


def rank_level(rank):
    """Trả về mức của một cấp bậc. Cấp bậc lạ coi như thấp nhất."""
    return RANK_LEVEL.get(rank, 0)


class Currency(models.TextChoices):
    """Loại tiền tệ dùng trong phase 1.

    Bán xuyên biên giới nên vừa có doanh số bằng USD vừa có chi phí bằng VND.
    Mỗi số tiền phải đi kèm loại tiền của nó, không quy đổi khi lưu.
    """

    VND = "VND", "Việt Nam đồng"
    USD = "USD", "Đô la Mỹ"


# Số chữ số thập phân theo tập quán từng loại tiền, dùng khi hiển thị
CURRENCY_DECIMALS = {Currency.VND: 0, Currency.USD: 2}
CURRENCY_SYMBOL = {Currency.VND: "₫", Currency.USD: "$"}


class AuditAction(models.TextChoices):
    """Các loại hành động được ghi vào nhật ký (BR-6)."""

    LOGIN = "login", "Đăng nhập"
    LOGIN_FAILED = "login_failed", "Đăng nhập thất bại"
    LOGOUT = "logout", "Đăng xuất"
    CREATE = "create", "Tạo"
    UPDATE = "update", "Sửa"
    DELETE = "delete", "Xoá"
    EXPORT = "export", "Xuất dữ liệu"
    IMPORT = "import", "Nhập dữ liệu"
    PERMISSION = "permission", "Đổi quyền"
    DENIED = "denied", "Từ chối truy cập"
