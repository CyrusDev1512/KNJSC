"""Lệnh nạp báo cáo Marketing mẫu để thử Báo cáo tổng hợp với nhiều dòng — AC-42.16 (chủ dự án 03.10.2026)."""
from datetime import date

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from forms_builder.models import DataRecord
from orders.models import Product
from reports.models import DailyReport
from reports.services import activity_service
from reports.tests.test_aggregations import bang_mkt  # noqa: F401
from reports.tests.test_mkt_derived_revenue import mkt_source  # noqa: F401

pytestmark = pytest.mark.django_db


def test_nap_bao_cao_mau_thang_truoc_toi_hom_nay(bang_mkt, mkt_source, nguoi_dung, settings, monkeypatch):  # noqa: F811
    """AC-42.16 — `nap_bao_cao_mau`: DEBUG tắt thì từ chối; DEBUG bật nộp qua service cho mỗi tài khoản mẫu (khoá đăng
    nhập) mỗi ngày từ ngày 1 tháng trước tới hôm nay đúng số lần; chạy lại không nộp trùng; dòng mang VND và hiện
    trên Báo cáo tổng hợp của Manager MKT; `--xoa-cu` xoá đúng báo cáo mẫu, không đụng báo cáo thật"""
    Product.objects.create(code="sp-mau", name="SP mẫu")
    monkeypatch.setattr("django.utils.timezone.localdate", lambda *a, **k: date(2026, 10, 3))
    settings.DEBUG = False
    with pytest.raises(CommandError):
        call_command("nap_bao_cao_mau", "--nguoi", "2", "--lan", "2")
    settings.DEBUG = True
    call_command("nap_bao_cao_mau", "--nguoi", "2", "--lan", "2")
    so_ngay = (date(2026, 10, 3) - date(2026, 9, 1)).days + 1                  # 33 ngày
    mau = DailyReport.objects.filter(created_by__username__startswith="mau_bc_mkt_")
    assert mau.count() == so_ngay * 2 * 2
    assert not mau.filter(created_by__is_active=True).exists()
    call_command("nap_bao_cao_mau", "--nguoi", "2", "--lan", "2")
    assert mau.count() == so_ngay * 2 * 2                                       # không trùng
    assert {r.data.get("loai_tien") for r in DataRecord.objects.filter(table=bang_mkt)} == {"VND"}
    result = activity_service.build(nguoi_dung["manager_mkt"], mkt_source, start=date(2026, 9, 1), end=date(2026, 10, 3))
    assert result.ok and result.totals["so_dong"] == so_ngay * 4
    that = DataRecord.objects.create(table=bang_mkt, department=bang_mkt.department,
                                     created_by=nguoi_dung["staff_mkt"], data={"ngay": "2026-10-01"})
    call_command("nap_bao_cao_mau", "--xoa-cu")
    assert not mau.exists() and list(DataRecord.objects.filter(table=bang_mkt)) == [that]
