"""Hằng của Bảng tin — khai một chỗ (quy tắc 7), ADR-015."""
from django.db import models


class PostKind(models.TextChoices):
    BAI_VIET = "bai_viet", "Bài viết"
    SINH_NHAT = "sinh_nhat", "Sinh nhật"


BODY_MAX = 2000
COMMENT_MAX = 500
#: Thanh bên (FR-10.5): bao nhiêu người nhiều sao nhất, bao nhiêu ghi nhận mới,
#: thành viên mới là hồ sơ tạo trong bao nhiêu ngày, hiện tối đa bao nhiêu
SIDEBAR_STARS = 5
SIDEBAR_RECOGNITIONS = 3
SIDEBAR_NEW_MEMBERS = 5
NEW_MEMBER_DAYS = 30
#: Lời chúc trên thiệp sinh nhật tự động — {ten} là họ tên trong hồ sơ (FR-10.4)
BIRTHDAY_MESSAGE = (
    "Chúc mừng sinh nhật {ten}! Cả nhà KN JSC chúc bạn tuổi mới nhiều sức khoẻ, "
    "nhiều niềm vui và thật nhiều đơn."
)
#: Mỗi lần mở bài chỉ tải chừng này bình luận mới nhất, cũ hơn thì bấm "Xem thêm" (quy tắc 1)
COMMENT_PAGE = 20
#: Máy tắt vài ngày thì khi bật lại đăng bù thiệp lùi tối đa chừng này ngày
BIRTHDAY_CATCH_UP_DAYS = 14
