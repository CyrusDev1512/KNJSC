"""Nạp nhiều báo cáo Marketing mẫu để thử Báo cáo tổng hợp với lượng dòng lớn (chủ dự án 03.10.2026).

    python manage.py nap_bao_cao_mau                   # tháng trước + tháng này, 8 người, 2 lần nộp/ngày
    python manage.py nap_bao_cao_mau --nguoi 20 --lan 3
    python manage.py nap_bao_cao_mau --xoa-cu          # chỉ xoá báo cáo của tài khoản mẫu

Nộp qua `daily_service.submit` như người thật (loại tiền, team, cột tính sẵn do hệ thống đặt). Người nộp là tài khoản
mẫu `mau_bc_mkt_<n>` bị khoá đăng nhập, thuộc bộ phận của biểu mẫu MKT, chia vào các team "Mẫu MKT — Team k". Chạy lại
chỉ nộp bù phần còn thiếu. Chỉ chạy khi DEBUG bật (máy local) — cùng khoá với các lệnh dữ liệu giả khác.
"""
import random
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.constants import Rank
from forms_builder.models import DataRecord
from orders.constants import Market
from orders.models import Product
from org.models import Team, UserProfile
from reports.models import DailyReport, ReportSource
from reports.services import daily_service

PREFIX = "mau_bc_mkt_"
TEAM_PREFIX = "Mẫu MKT — Team "


class Command(BaseCommand):
    help = "Nạp báo cáo Marketing mẫu từ ngày 1 tháng trước tới hôm nay (chỉ khi DEBUG bật)."

    def add_arguments(self, parser):
        parser.add_argument("--nguoi", type=int, default=8, help="Số marketer mẫu (mặc định 8)")
        parser.add_argument("--lan", type=int, default=2, help="Số lần nộp mỗi người mỗi ngày (mặc định 2)")
        parser.add_argument("--xoa-cu", action="store_true", dest="xoa_cu", help="Xoá báo cáo của tài khoản mẫu")

    def handle(self, *args, nguoi, lan, xoa_cu, **options):
        if not settings.DEBUG:
            raise CommandError("DEBUG đang tắt — dữ liệu giả không dành cho máy chủ thật.")
        nguon = ReportSource.objects.filter(kind="mkt").select_related("table").first()
        form = nguon and nguon.table.forms.filter(is_active=True).select_related("department").first()
        if form is None:
            raise CommandError("Chưa có biểu mẫu Báo cáo Marketing — chạy `du_lieu_mau` và `configure_erp_reports` trước.")
        mau = get_user_model().objects.filter(username__startswith=PREFIX)
        if xoa_cu:
            self._xoa(nguon, mau)
            return
        if not 1 <= nguoi <= 200 or not 1 <= lan <= 10:
            raise CommandError("--nguoi từ 1 đến 200, --lan từ 1 đến 10.")
        san_pham = list(Product.objects.filter(is_active=True).order_by("name").values_list("name", flat=True)[:12])
        if not san_pham:
            raise CommandError("Chưa có sản phẩm — chạy `du_lieu_mau` trước.")
        hom_nay = timezone.localdate()
        dau = (hom_nay.replace(day=1) - timedelta(days=1)).replace(day=1)   # ngày 1 tháng trước
        fields = list(form.ordered_fields())
        ngau_nhien = random.Random(20261003)
        da_nop = 0
        for i in range(1, nguoi + 1):
            user = self._tai_khoan(form, i)
            for so_ngay in range((hom_nay - dau).days + 1):
                ngay = dau + timedelta(days=so_ngay)
                con = lan - daily_service.submissions_today(form, user, ngay)
                for _ in range(max(con, 0)):
                    mess = ngau_nhien.randint(40, 400)
                    don = ngau_nhien.randint(1, max(1, mess // 8))
                    gia_tri = {
                        "ngay": ngay.isoformat(), "san_pham": ngau_nhien.choice(san_pham), "thi_truong": ngau_nhien.choice(Market.labels),
                        "so_mess": str(mess), "so_don": str(don),
                        "cpqc": str(ngau_nhien.randrange(500_000, 20_000_000, 1000)),
                        "doanh_so": str(don * ngau_nhien.randrange(800_000, 3_000_000, 1000)),
                    }
                    values = {f.field.code: gia_tri.get(f.link.column.code, "") for f in fields if hasattr(f, "link")}
                    with transaction.atomic():
                        daily_service.submit(form, values, report_date=ngay, actor=user, fields=fields)
                    da_nop += 1
        tong = DailyReport.objects.filter(form=form, created_by__username__startswith=PREFIX).count()
        self.stdout.write(f"Đã nộp thêm {da_nop} báo cáo mẫu từ {dau:%d/%m/%Y} tới {hom_nay:%d/%m/%Y}; "
                          f"tổng {tong} báo cáo của {nguoi} tài khoản mẫu (khoá đăng nhập).")

    def _tai_khoan(self, form, i):
        team, _ = Team.objects.get_or_create(department=form.department, name=f"{TEAM_PREFIX}{(i - 1) // 4 + 1}")
        user, created = get_user_model().objects.get_or_create(username=f"{PREFIX}{i}", defaults={"is_active": False})
        if created:
            user.set_unusable_password()
            user.save(update_fields=["password"])
            UserProfile.objects.create(user=user, department=form.department, team=team, rank=Rank.STAFF,
                                       full_name=f"Marketer mẫu {i}", staff_code=f"MAUMKT{i:03d}")
        profile = getattr(user, "profile", None)
        if user.is_active or user.has_usable_password() or profile is None or profile.department_id != form.department_id:
            raise CommandError(f"Tài khoản {user.username} không phải tài khoản mẫu; không ghi đè.")
        return user

    @transaction.atomic
    def _xoa(self, nguon, mau):
        # Dữ liệu giả của tài khoản mẫu: xoá hẳn (ngoại lệ của BR-4 như PERF-*, MAU-*, KH-*)
        bao_cao = DailyReport.objects.filter(created_by__in=mau)
        ids = list(bao_cao.values_list("record_id", flat=True))
        so = bao_cao.count()
        bao_cao.delete()
        DataRecord.all_objects.filter(pk__in=ids, table=nguon.table).delete()
        self.stdout.write(f"Đã xoá {so} báo cáo mẫu; tài khoản mẫu giữ lại (khoá đăng nhập).")
