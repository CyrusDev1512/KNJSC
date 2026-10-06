"""Cảnh báo cho người vận hành — một chỗ duy nhất.

Sao lưu hỏng, tác vụ kẹt, worker chết: hệ thống phải **nói ra** (kien-truc.md),
nhưng việc gửi thư không bao giờ được làm hỏng tác vụ đang chạy. Địa chỉ nhận
lấy từ `settings.ADMINS` (biến `OPERATOR_EMAILS`).
"""
import errno
import logging

from django.core.cache import cache
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


#: Lời cho người dùng khi máy chủ hết chỗ ghi tệp (AC-10.14)
HET_DIA = ("Máy chủ đã hết chỗ lưu tệp nên tệp chưa được lưu. Quản trị viên đã được báo; "
           "thử lại sau khi được báo đã dọn chỗ.")


def la_het_dia(loi):
    """Lỗi do đĩa đầy (ENOSPC) hay vượt hạn mức đĩa (EDQUOT)."""
    return isinstance(loi, OSError) and loi.errno in (errno.ENOSPC, errno.EDQUOT)


def bao_het_dia(noi):
    """Báo người vận hành đĩa đầy — mỗi tiến trình tối đa một thư mỗi 10 phút, không thì mỗi lần tải lên là một thư."""
    logger.critical("Hết chỗ lưu tệp (%s)", noi)
    if cache.add("canh-bao-het-dia", 1, 600):
        bao_nguoi_van_hanh("[KN JSC] Máy chủ hết chỗ lưu tệp",
                           f"Ghi tệp thất bại vì đĩa đầy ({noi}). Dọn thư mục storage hoặc mở rộng ổ đĩa.")
