"""Đăng thiệp sinh nhật cho một ngày — chạy tay khi cần (FR-10.4).

    python manage.py thiep_sinh_nhat                  # hôm nay
    python manage.py thiep_sinh_nhat --ngay 2026-09-07

Cùng hàm với tác vụ nền `feed.thiep_sinh_nhat`; chạy lại không nhân đôi.
"""
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from feed.services import post_service


class Command(BaseCommand):
    help = "Đăng thiệp sinh nhật cho người có sinh nhật trong ngày. Chạy lại nhiều lần được."

    def add_arguments(self, parser):
        parser.add_argument("--ngay", default=None, help="Ngày dạng YYYY-MM-DD, mặc định hôm nay")

    def handle(self, *args, **o):
        ngay = None
        if o["ngay"]:
            try:
                ngay = date.fromisoformat(o["ngay"])
            except ValueError:
                raise CommandError("Ngày phải có dạng YYYY-MM-DD, ví dụ 2026-09-07.")
        moi = post_service.create_birthday_posts(ngay)
        self.stdout.write(self.style.SUCCESS(f"Ngay {ngay or 'hom nay'}: {moi} thiep moi"))
