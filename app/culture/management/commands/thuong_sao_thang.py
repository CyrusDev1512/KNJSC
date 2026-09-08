"""Thưởng sao xếp hạng doanh số cho một tháng — chạy tay khi cần (FR-12.4).

    python manage.py thuong_sao_thang                # tháng trước
    python manage.py thuong_sao_thang --thang 2026-08

Cùng hàm với tác vụ nền `culture.thuong_sao_thang`; chạy lại không nhân đôi.
"""
from django.core.management.base import BaseCommand, CommandError

from core.exceptions import BusinessError
from culture.services import leaderboard_service


class Command(BaseCommand):
    help = "Thưởng 5/3/1 sao cho top 3 doanh số của một tháng. Chạy lại nhiều lần được."

    def add_arguments(self, parser):
        parser.add_argument("--thang", default=None, help="Kỳ dạng YYYY-MM, mặc định tháng trước")

    def handle(self, *args, **o):
        ky = o["thang"] or leaderboard_service.previous_period()
        try:
            moi = leaderboard_service.award_monthly_stars(ky)
        except BusinessError as loi:
            raise CommandError(str(loi))
        self.stdout.write(self.style.SUCCESS(f"Ky {ky}: {moi} dong sao moi"))
