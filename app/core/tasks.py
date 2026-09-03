"""Tác vụ nền của core: canh hàng đợi, dọn dẹp, sao lưu.

Tác vụ nền gọi cùng tầng dịch vụ với giao diện web. Không viết logic hai lần.
Mọi tác vụ đều ghi nhật ký kết quả (AC-9.2) — chạy nền không có nghĩa là
chạy âm thầm.
"""
import logging
from datetime import datetime, timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import mail_admins
from django.utils import timezone

from .audit import record
from .constants import EXPORT_FILE_TTL_HOURS, JOB_STALE_MINUTES, AuditAction, JobStatus
from .models import BackgroundJob

logger = logging.getLogger(__name__)


def bao_nguoi_van_hanh(tieu_de, noi_dung):
    """Gửi thư cho người vận hành. Không có địa chỉ hay gửi hỏng thì chỉ ghi
    nhật ký ứng dụng — không được làm hỏng tác vụ đang chạy."""
    try:
        mail_admins(tieu_de, noi_dung, fail_silently=True)
    except Exception:  # pragma: khong do
        logger.exception("Không gửi được thư cảnh báo")


@shared_task(name="core.kiem_tra_hang_doi")
def kiem_tra_hang_doi():
    """Tác vụ mẫu để xác nhận Celery và Redis đã chạy được."""
    return "hang doi hoat dong"


@shared_task(name="core.danh_dau_tac_vu_ket")
def danh_dau_tac_vu_ket():
    """Tác vụ chờ quá lâu mà không ai nhận nghĩa là worker không chạy.

    Đánh dấu kẹt, ghi nhật ký và báo người vận hành — kien-truc.md: hệ thống
    phải nói ra, người dùng không bị treo màn hình chờ mãi.
    """
    moc = timezone.now() - timedelta(minutes=JOB_STALE_MINUTES)
    ket = list(BackgroundJob.objects.filter(status=JobStatus.PENDING, updated_at__lt=moc))
    for job in ket:
        job.status = JobStatus.STALE
        job.error = (
            f"Chờ quá {JOB_STALE_MINUTES} phút mà chưa được xử lý — worker không chạy. "
            "Quản trị viên đã được cảnh báo."
        )
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "error", "finished_at", "updated_at"])
        record(
            AuditAction.UPDATE, target=("job", job.pk),
            detail=f"Tác vụ kẹt: {job.title[:80]} — worker không chạy",
        )
    if ket:
        logger.error("%d tác vụ nền kẹt, worker không chạy", len(ket))
        bao_nguoi_van_hanh(
            f"[KN JSC] {len(ket)} tác vụ nền kẹt",
            "Các tác vụ sau chờ quá lâu mà không được xử lý — kiểm worker Celery:\n"
            + "\n".join(f"- #{j.pk} {j.title}" for j in ket),
        )
    return len(ket)


@shared_task(name="core.don_tep_xuat_qua_han")
def don_tep_xuat_qua_han():
    """Dọn tệp xuất và tệp nhập chờ quá 24 giờ — NFR-16, docs/03 mục 9.

    Tác vụ nhập còn *Chờ xác nhận* quá 24 giờ thì đóng lại: người dùng đã bỏ
    dở, tệp không còn. Ghi một dòng nhật ký với số tệp đã xoá.
    """
    from pathlib import Path

    moc = timezone.now() - timedelta(hours=EXPORT_FILE_TTL_HOURS)
    da_xoa = 0
    for thu_muc in (Path(settings.EXPORT_DIR), Path(settings.STORAGE_DIR) / "uploads" / "imports"):
        if not thu_muc.exists():
            continue
        for tep in thu_muc.iterdir():
            if not tep.is_file():
                continue
            sua_luc = datetime.fromtimestamp(tep.stat().st_mtime, tz=timezone.get_current_timezone())
            if sua_luc < moc:
                tep.unlink(missing_ok=True)
                da_xoa += 1

    het_han = BackgroundJob.objects.filter(status=JobStatus.DRAFT, created_at__lt=moc)
    so_het_han = het_han.count()
    for job in het_han:
        job.mark_failed("Hết hạn xác nhận sau 24 giờ. Tải tệp lên lại nếu vẫn cần nhập.")

    record(
        AuditAction.DELETE, target=("cleanup", "exports"),
        detail=f"Dọn tệp xuất quá hạn: xoá {da_xoa} tệp, đóng {so_het_han} tác vụ bỏ dở",
    )
    return da_xoa


@shared_task(name="core.sao_luu_hang_dem")
def sao_luu_hang_dem():
    """Sao lưu tự động mỗi đêm — NFR-19. Thân thật ở `backup_service` (7B)."""
    from .services import backup_service

    job = backup_service.run_backup()
    return job.status
