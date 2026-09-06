"""Số liệu cho **Trang chủ KN CRM** (tổng quan) — ADR-013, AC-11.31.

Theo mẫu `dashboard_service` của KN ERP: mỗi khối chạy trong lớp bọc riêng,
một khối hỏng thì báo "tạm chưa khả dụng", khối khác vẫn hiện. Mọi số liệu
đi qua manager `in_scope` (quy tắc 11): Staff chỉ đếm dòng của mình, Leader
cả team, Manager cả bộ phận.
"""
import logging

from django.db.models import Count, Max, Q
from django.urls import reverse
from django.utils import timezone

from core.models import AuditLog
from forms_builder.models import DataRecord, TableDef

logger = logging.getLogger(__name__)


def _khoi(ten, ham):
    try:
        return {"ok": True, "data": ham()}
    except Exception:
        logger.exception("Khối Trang chủ KN CRM '%s' lỗi", ten)
        return {"ok": False, "data": None}


def _so_lieu(user):
    """Bốn ô số: dòng nhập tháng này, dòng hôm nay, số bảng, tổng dòng — theo
    lúc tạo (`created_at`, giờ Việt Nam) để bảng không có cột Ngày vẫn đếm được."""
    hom_nay = timezone.localdate()
    dau_thang = hom_nay.replace(day=1)
    # Một truy vấn cho cả ba số dòng (đếm có điều kiện), một cho số bảng
    dem = DataRecord.objects.in_scope(user).filter(table__deleted_at__isnull=True).aggregate(
        so_dong=Count("id"),
        dong_thang=Count("id", filter=Q(created_at__date__gte=dau_thang)),
        dong_hom_nay=Count("id", filter=Q(created_at__date=hom_nay)),
    )
    return {
        **dem,
        "so_bang": TableDef.objects.in_scope(user).count(),
        "thang": hom_nay.month, "nam": hom_nay.year,
    }


def _bang_gan_day(user):
    """Bảng trong phạm vi, mới cập nhật trước; kèm số dòng và địa chỉ lưới."""
    cac_bang = list(
        TableDef.objects.in_scope(user)
        .select_related("department")
        .annotate(so_dong=Count("records", distinct=True), cap_nhat=Max("records__updated_at"))
        .order_by("-cap_nhat", "name")[:6]
    )
    for b in cac_bang:
        b.url = reverse("bang_tinh_xem", args=[b.code])
    return cac_bang


def _hoat_dong(user):
    return list(AuditLog.objects.in_scope(user).select_related("actor").order_by("-created_at")[:8])


def tong_quan(user):
    return {
        "so_lieu": _khoi("so_lieu", lambda: _so_lieu(user)),
        "bang": _khoi("bang", lambda: _bang_gan_day(user)),
        "hoat_dong": _khoi("hoat_dong", lambda: _hoat_dong(user)),
    }
