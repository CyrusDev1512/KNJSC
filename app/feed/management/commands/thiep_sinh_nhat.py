"""Đăng thiệp sinh nhật — chạy tay khi cần, và chạy mỗi lần máy bật (FR-10.4).

    python manage.py thiep_sinh_nhat                  # hôm nay, bù cả những ngày máy tắt
    python manage.py thiep_sinh_nhat --ngay 2026-09-07

Cùng hàm với tác vụ nền `feed.thiep_sinh_nhat`; chạy lại không nhân đôi.
"""
from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from feed.services import post_service


class Command(BaseCommand):
    help = "Đăng thiệp sinh nhật cho người có sinh nhật trong ngày, bù những ngày máy tắt. Chạy lại nhiều lần được."

    def add_arguments(self, parser):
        parser.add_argument("--ngay", default=None, help="Chỉ một ngày, dạng YYYY-MM-DD; không có thì hôm nay kèm bù ngày trước")

    def handle(self, *args, **o):
        if not o["ngay"]:
            moi = post_service.catch_up_birthday_posts()
            self.stdout.write(self.style.SUCCESS(f"Ngay hom nay (co bu ngay truoc): {moi} thiep moi"))
            return
        try:
            ngay = date.fromisoformat(o["ngay"])
        except ValueError:
            raise CommandError("Ngày phải có dạng YYYY-MM-DD, ví dụ 2026-09-07.")
        if ngay > timezone.localdate():
            raise CommandError("Không đăng thiệp cho ngày trong tương lai.")
        moi = post_service.create_birthday_posts(ngay)
        self.stdout.write(self.style.SUCCESS(f"Ngay {ngay}: {moi} thiep moi"))
