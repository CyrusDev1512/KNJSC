"""Sao lưu cơ sở dữ liệu ngay bây giờ — cùng đường với tác vụ hằng đêm.

    python manage.py sao_luu

Trong Docker: `scripts/backup.sh`. Thoát mã 1 khi thất bại để script và cron
bên ngoài biết.
"""
from django.core.management.base import BaseCommand

from core.constants import JobStatus
from core.services import backup_service


class Command(BaseCommand):
    help = "Sao lưu cơ sở dữ liệu bằng pg_dump, giữ tối đa 30 bản gần nhất"

    def handle(self, *args, **options):
        job = backup_service.run_backup(title="Sao lưu bằng tay")
        if job.status != JobStatus.DONE:
            self.stderr.write(self.style.ERROR(f"Sao lưu THẤT BẠI: {job.error}"))
            raise SystemExit(1)
        tom_tat = job.summary
        self.stdout.write(self.style.SUCCESS(
            f"Đã sao lưu: {tom_tat['file_name']} ({tom_tat['size']}) "
            f"vào {backup_service.backup_dir()} — đang giữ {tom_tat['kept']} bản"
        ))
