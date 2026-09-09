"""Cập nhật tài khoản mẫu một lần trên mỗi database local, không nạp dữ liệu."""
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from core.audit import record
from core.constants import AuditAction
from core.management.commands.du_lieu_mau import MAT_KHAU_MAU, TAI_KHOAN
from core.models import AuditLog
from org.models import UserProfile
from org.services import account_service


# Dấu vết theo tài khoản nằm trong DB, không phụ thuộc checkout hay storage/.
UPDATE_KEY = "sample_credentials_20260909_v1"


class Command(BaseCommand):
    help = "Cập nhật một lần mật khẩu tài khoản mẫu trên máy phát triển."

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            self.stdout.write("Bo qua cap nhat tai khoan mau: DEBUG dang tat.")
            return

        changed = 0
        for username, *_ in TAI_KHOAN:
            # Khoá cùng thứ tự để hai launcher không đặt lại cùng tài khoản.
            profile = (UserProfile.objects.select_for_update()
                       .select_related("user").filter(user__username=username).first())
            if profile is None:
                continue
            if AuditLog.objects.filter(
                target_type=UPDATE_KEY, target_id=str(profile.user_id),
            ).exists():
                continue
            must_change = profile.must_change_password
            account_service.reset_password(profile, MAT_KHAU_MAU)
            profile.must_change_password = must_change
            profile.save(update_fields=["must_change_password"])
            record(
                AuditAction.PERMISSION, target=(UPDATE_KEY, profile.user_id),
                detail="Hoàn tất cập nhật tài khoản mẫu local v1",
            )
            changed += 1
        self.stdout.write(f"Da cap nhat {changed} tai khoan mau; lan sau khong dat lai.")
