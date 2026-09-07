"""Hằng của Tài nguyên — khai một chỗ (quy tắc 7), ADR-015."""
from django.db import models


class ResourceStatus(models.TextChoices):
    TRONG = "trong", "Trống"
    DANG_DUNG = "dang_dung", "Đang dùng"
    KHOA = "khoa", "Khoá"
    HONG = "hong", "Hỏng"


#: Chip màu theo trạng thái — trạng thái là chip, không phải nút
STATUS_CHIP = {
    ResourceStatus.TRONG: "chip-tot",
    ResourceStatus.DANG_DUNG: "chip-nhan",
    ResourceStatus.KHOA: "chip-cho",
    ResourceStatus.HONG: "chip-xau",
}

#: Mục mặc định khi dựng dữ liệu mẫu — anh/chị chốt 06.09.2026: "BM, via, page..."
DEFAULT_CATEGORIES = ("BM", "Via", "Page", "Tài khoản QC", "SIM")

CATEGORY_NAME_MAX = 120
NAME_MAX = 200
NOTE_MAX = 500
LINK_MAX = 500

#: Nhãn hiện trong nhật ký khi sửa — cùng một chỗ với form
RESOURCE_FIELD_LABELS = {
    "category": "Mục", "name": "Tên", "note": "Ghi chú", "link": "Liên kết",
    "status": "Trạng thái", "holder": "Người giữ", "department": "Bộ phận",
}

#: Ghi chú không được chứa mật khẩu hay mã bí mật (FR-13.4) — thấy từ này là chặn
SECRET_HINTS = (
    "mật khẩu", "mat khau", "password", "passwd", "pass:", "pwd", "otp", "2fa",
    "secret", "token", "mã bí mật", "ma bi mat", "api key", "api_key",
)
