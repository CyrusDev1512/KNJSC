"""Hằng của module Văn hoá — khai một chỗ (quy tắc 7), ADR-017."""
from django.db import models


class CoreValue(models.TextChoices):
    """Năm giá trị văn hoá mẫu — backlog N12 chờ anh/chị chốt danh sách thật."""

    TAN_TAM = "tan_tam", "Tận tâm"
    CHINH_TRUC = "chinh_truc", "Chính trực"
    HOP_TAC = "hop_tac", "Hợp tác"
    SANG_TAO = "sang_tao", "Sáng tạo"
    TRACH_NHIEM = "trach_nhiem", "Trách nhiệm"


class StarSource(models.TextChoices):
    GHI_NHAN = "ghi_nhan", "Ghi nhận"
    XEP_HANG = "xep_hang", "Xếp hạng doanh số"


#: Mỗi ghi nhận cho người nhận bấy nhiêu sao — Q72
STARS_PER_RECOGNITION = 1
#: Ba người đứng đầu doanh số tháng trước nhận lần lượt — Q72
MONTHLY_RANK_STARS = (5, 3, 1)
#: Số dòng hiện trên bảng xếp hạng doanh số và bảng nhiều sao nhất
LEADERBOARD_ROWS = 10
STAR_TOP = 10
MESSAGE_MAX = 300
#: Kỳ tính sao và xếp hạng: "YYYY-MM" theo giờ Việt Nam
PERIOD_FORMAT = "%Y-%m"
