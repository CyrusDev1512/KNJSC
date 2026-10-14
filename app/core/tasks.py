"""Tác vụ nền của core: canh hàng đợi, dọn dẹp, sao lưu.

Tác vụ nền gọi cùng tầng dịch vụ với giao diện web. Không viết logic hai lần.
Mọi tác vụ đều ghi nhật ký kết quả (AC-9.2) — chạy nền không có nghĩa là
chạy âm thầm.
"""
import logging
from datetime import datetime, timedelta

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .alerts import bao_nguoi_van_hanh  # noqa: F401 — tác vụ khác dùng lại
from .audit import record
from .constants import (
    EXPORT_FILE_TTL_HOURS, JOB_RUNNING_STALE_MINUTES, JOB_RUNNING_STALE_MINUTES_BACKUP, JOB_STALE_MINUTES,
    AuditAction, JobKind, JobStatus,
)
from .models import BackgroundJob

logger = logging.getLogger(__name__)


@shared_task(name="core.kiem_tra_hang_doi")
def kiem_tra_hang_doi():
    """Tác vụ mẫu để xác nhận Celery và Redis đã chạy được."""
    return "hang doi hoat dong"


@shared_task(name="core.danh_dau_tac_vu_ket")
def danh_dau_tac_vu_ket():
    """Đánh dấu kẹt hai loại tác vụ nền, ghi nhật ký và báo người vận hành — kien-truc.md: hệ thống phải nói
    ra, người dùng không bị treo màn hình chờ mãi.

    - *Chờ xử lý* quá JOB_STALE_MINUTES mà không ai nhận: worker không chạy.
    - *Đang chạy* mà không có tiến độ quá JOB_RUNNING_STALE_MINUTES (sao lưu: JOB_RUNNING_STALE_MINUTES_BACKUP):
      worker chết giữa chừng — không có đường tự phục hồi vì gửi lại cũng bị bỏ qua khi tác vụ không còn
      *Chờ xử lý* (TL-23). Đóng lại thì bảng hết bị chặn xoá và `moi-nhat/` thôi báo đang tính lại.
    """
    bay_gio = timezone.now()
    ket = _dong_tac_vu_ket(
        BackgroundJob.objects.filter(status=JobStatus.PENDING,
                                     updated_at__lt=bay_gio - timedelta(minutes=JOB_STALE_MINUTES)),
        f"Chờ quá {JOB_STALE_MINUTES} phút mà chưa được xử lý — worker không chạy. "
        "Quản trị viên đã được cảnh báo.",
        "worker không chạy",
    )
    dang_chay = BackgroundJob.objects.filter(status=JobStatus.RUNNING)
    for ds, phut in (
        (dang_chay.exclude(kind=JobKind.BACKUP), JOB_RUNNING_STALE_MINUTES),
        (dang_chay.filter(kind=JobKind.BACKUP), JOB_RUNNING_STALE_MINUTES_BACKUP),
    ):
        ket += _dong_tac_vu_ket(
            ds.filter(updated_at__lt=bay_gio - timedelta(minutes=phut)),
            f"Đang chạy mà quá {phut} phút không có tiến độ — worker đã dừng giữa chừng (khởi động lại, hết "
            "bộ nhớ). Quản trị viên đã được cảnh báo; hãy làm lại thao tác.",
            "worker dừng giữa chừng",
        )
    if ket:
        logger.error("%d tác vụ nền kẹt", len(ket))
        noi_dung = ("Các tác vụ sau kẹt (chờ quá lâu không được nhận, hoặc đang chạy mà mất tiến độ) — kiểm "
                    "worker Celery:\n" + "\n".join(f"- #{j.pk} {j.title} ({j.trang_thai_cu})" for j in ket))
        if any(j.kind == JobKind.RECOMPUTE for j in ket):
            noi_dung += ("\n\nCó tác vụ tính lại cột dừng dở: cột tính sẵn của bảng có thể lệch. Sửa lại cột hoặc "
                         "chạy `python manage.py kiem_tra_du_lieu --sua`.")
        bao_nguoi_van_hanh(f"[KN JSC] {len(ket)} tác vụ nền kẹt", noi_dung)
    return len(ket)


def _dong_tac_vu_ket(ds, loi, ly_do):
    """Đóng các tác vụ của `ds` thành *Kẹt*, giữ tiến độ đã làm. `skip_locked`: tác vụ đang bị worker còn sống
    khoá (nhập giữ khoá dòng tác vụ suốt giao dịch, nhịp tiến độ chưa commit) thì bỏ qua, không treo lượt canh."""
    with transaction.atomic():
        ket = list(ds.select_for_update(skip_locked=True))
        for job in ket:
            job.trang_thai_cu = job.get_status_display()
            job.status = JobStatus.STALE
            job.error = loi
            job.finished_at = timezone.now()
            job.save(update_fields=["status", "error", "finished_at", "updated_at"])
            record(AuditAction.UPDATE, target=("job", job.pk), detail=f"Tác vụ kẹt: {job.title[:80]} — {ly_do}")
    return ket


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
    """Sao lưu tự động mỗi đêm — NFR-19, AC-10.6. Thân thật ở `backup_service`."""
    from .services import backup_service

    job = backup_service.run_backup()
    return job.status
