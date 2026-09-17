"""Dữ liệu xem thử local: nộp qua service, không giả lập riêng bảng lịch sử."""
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.constants import Rank
from forms_builder.models import FormDef
from orders.models import Product
from org.models import Team, UserProfile
from reports.services import daily_service

SAMPLE_PREFIX = 'mau_erp_1609_'
FORM_CODES = ('bc_mkt_ngay', 'bc_sale_ngay', 'bc_van_don_ngay')


class Command(BaseCommand):
    help = 'Tạo 36 báo cáo mẫu 14–16/09/2026 trên local; chạy lại không tạo trùng.'

    @transaction.atomic
    def handle(self, *args, **options):
        if settings.SETTINGS_MODULE not in ('knjsc.settings.dev', 'knjsc.settings.test'):
            raise CommandError('Chỉ cho phép bộ dữ liệu mẫu này trong settings dev/test.')
        forms = {f.code: f for f in FormDef.objects.filter(code__in=FORM_CODES).select_related('department', 'table')}
        if set(forms) != set(FORM_CODES):
            raise CommandError('Cần cấu hình đủ biểu mẫu Marketing, Sale và Vận đơn trước.')
        product = Product.objects.filter(is_active=True).order_by('pk').first()
        if product is None:
            raise CommandError('Cần một sản phẩm trong danh mục để tạo báo cáo mẫu.')
        count = 0
        names = ('An', 'Bình', 'Chi', 'Dũng')
        for code in FORM_CODES:
            form = forms[code]
            fields = list(form.ordered_fields())
            for index, name in enumerate(names):
                username = f'{SAMPLE_PREFIX}{form.department.code}_{index+1}'
                team, _ = Team.objects.get_or_create(department=form.department,
                    name=f'Mẫu ERP 16.09 — Team {index//2+1}')
                user, created = get_user_model().objects.get_or_create(username=username,
                    defaults={'is_active':False})
                if created:
                    user.set_unusable_password()
                    user.save(update_fields=['password'])
                    UserProfile.objects.create(user=user, department=form.department, team=team,
                        rank=Rank.STAFF, full_name=f'Mẫu {form.department.name} — {name}')
                profile = getattr(user, 'profile', None)
                if user.is_active or user.has_usable_password() or profile is None or (
                    profile.department_id != form.department_id or profile.team_id != team.pk
                ):
                    raise CommandError(f'Tài khoản {username} không khớp dữ liệu mẫu; không ghi đè.')
                for offset in range(3):
                    day = date(2026, 9, 16) - timedelta(days=offset)
                    if daily_service.already_submitted(form, user, day):
                        continue
                    raw = {'ngay':day.isoformat(), 'san_pham':product.name,
                        'thi_truong':'Canada', 'so_mess':str(40+index*10+offset*5),
                        'so_don':str(4+index+offset), 'cpqc':str(20+index*5),
                        'doanh_so':str(100+index*25+offset*10), 'loai_tien':'CAD',
                        'cong_viec':f'[MẪU] Kiểm tra địa chỉ, liên hệ hãng vận chuyển và cập nhật tình trạng giao ngày {day:%d/%m}.',
                        'ket_qua':f'[MẪU] Đã hoàn tất kiểm tra {12+index*3+offset} đơn và bàn giao danh sách cần theo dõi.',
                        'vuong_mac':'[MẪU] Chờ xác nhận địa chỉ bổ sung; đề xuất kiểm tra trước khi bàn giao.' if index%2 else '[MẪU] Không có vướng mắc.'}
                    values = {f.field.code:raw.get(f.link.column.code, '') for f in fields}
                    daily_service.submit(form, values, report_date=day, actor=user, fields=fields)
                    count += 1
        self.stdout.write(f'Đã nộp {count} báo cáo mẫu mới; tài khoản mẫu bị khóa đăng nhập.')
