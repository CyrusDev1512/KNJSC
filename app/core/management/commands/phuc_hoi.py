"""Phục hồi cơ sở dữ liệu từ một bản sao lưu — ĐÈ LÊN dữ liệu hiện tại.

    python manage.py phuc_hoi                       # liệt kê các bản, không làm gì
    python manage.py phuc_hoi --toi-chac-chan       # phục hồi bản mới nhất
    python manage.py phuc_hoi knjsc-20260903-020000.dump --toi-chac-chan

Không có cờ `--toi-chac-chan` thì lệnh chỉ in ra bản sẽ được dùng rồi dừng —
đây là thao tác không đảo ngược được, phải gõ tay để xác nhận (NFR-10).
"""
from django.core.management.base import BaseCommand, CommandError

from core.exceptions import BusinessError
from core.services import backup_service


class Command(BaseCommand):
    help = "Phục hồi cơ sở dữ liệu từ bản sao lưu (đè lên dữ liệu hiện tại)"

    def add_arguments(self, parser):
        parser.add_argument("tep", nargs="?", help="Tên tệp trong thư mục sao lưu, mặc định bản mới nhất")
        parser.add_argument(
            "--toi-chac-chan", action="store_true", dest="chac_chan",
            help="Bắt buộc: xác nhận đè lên cơ sở dữ liệu hiện tại",
        )

    def handle(self, *args, **options):
        cac_ban = backup_service.list_backups()
        try:
            chon = backup_service.resolve_backup(options.get("tep"))
        except BusinessError as loi:
            raise CommandError(str(loi)) from loi

        self.stdout.write(f"Thư mục sao lưu: {backup_service.backup_dir()}")
        for tep in cac_ban[:10]:
            dau = "→" if tep == chon else " "
            self.stdout.write(f"  {dau} {tep.name}  ({backup_service.format_size(tep.stat().st_size)})")

        if not options["chac_chan"]:
            self.stdout.write(self.style.WARNING(
                f"\nChưa làm gì. Phục hồi sẽ XOÁ dữ liệu hiện tại và thay bằng {chon.name}.\n"
                "Nếu đúng ý, chạy lại kèm --toi-chac-chan"
            ))
            return

        try:
            backup_service.run_restore(chon)
        except BusinessError as loi:
            raise CommandError(f"Phục hồi THẤT BẠI: {loi}") from loi
        self.stdout.write(self.style.SUCCESS(
            f"Đã phục hồi từ {chon.name}. Kiểm lại bằng cách đăng nhập và mở vài màn hình."
        ))
