"""Manager phạm vi của báo cáo hằng ngày.

Giữ nguyên thang Staff / Leader / Manager / Admin của `ScopedQuerySet`; chỉ thêm
một ngoại lệ đã chốt (ADR-038, sheet Phân quyền 5.0): **Kế toán – Kiểm soát nội bộ
thấy mọi báo cáo** của mọi bộ phận để đối chiếu và sửa số liệu (quyền sửa kiểm ở
`daily_service.can_amend`). Mở ở đây, không ở view (quy tắc 11).
"""
from django.db import models

from core.managers import AllObjectsManager, ScopedManager, ScopedQuerySet


class DailyReportQuerySet(ScopedQuerySet):
    def in_scope(self, user):
        from org.services.org_service import is_accountant

        if is_accountant(user):
            return self
        return super().in_scope(user)


class DailyReportManager(ScopedManager.from_queryset(DailyReportQuerySet)):
    """Đã loại bản ghi đánh dấu xoá; `all_objects` lấy cả."""


class AllDailyReportManager(AllObjectsManager.from_queryset(DailyReportQuerySet)):
    pass
