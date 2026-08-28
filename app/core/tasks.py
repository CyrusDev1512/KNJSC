"""Tác vụ nền của core.

Tác vụ nền gọi cùng tầng dịch vụ với giao diện web. Không viết logic hai lần.
"""
from celery import shared_task

from .audit import record
from .constants import AuditAction


@shared_task(name="core.kiem_tra_hang_doi")
def kiem_tra_hang_doi():
    """Tác vụ mẫu để xác nhận Celery và Redis đã chạy được."""
    return "hang doi hoat dong"


@shared_task(name="core.don_tep_xuat_qua_han")
def don_tep_xuat_qua_han():
    """Dọn tệp xuất quá 24 giờ.

    Giai đoạn 7 sẽ viết phần xoá tệp thật. Hiện chỉ ghi nhật ký để có chỗ
    móc vào lịch chạy định kỳ.
    """
    record(AuditAction.DELETE, target=("cleanup", "exports"), detail="Dọn tệp xuất quá hạn")
    return 0
