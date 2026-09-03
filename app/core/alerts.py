"""Cảnh báo cho người vận hành — một chỗ duy nhất.

Sao lưu hỏng, tác vụ kẹt, worker chết: hệ thống phải **nói ra** (kien-truc.md),
nhưng việc gửi thư không bao giờ được làm hỏng tác vụ đang chạy. Địa chỉ nhận
lấy từ `settings.ADMINS` (biến `OPERATOR_EMAILS`).
"""
import logging

from django.core.mail import mail_admins

logger = logging.getLogger(__name__)


def bao_nguoi_van_hanh(tieu_de, noi_dung):
    """Gửi thư cho người vận hành. Không có địa chỉ hay gửi hỏng thì chỉ ghi
    nhật ký ứng dụng. Nội dung **không được chứa mật khẩu hay dữ liệu khách**
    — người gọi chịu trách nhiệm (điều cấm 6)."""
    try:
        mail_admins(tieu_de, noi_dung, fail_silently=True)
    except Exception:  # pragma: khong do
        logger.exception("Không gửi được thư cảnh báo")
