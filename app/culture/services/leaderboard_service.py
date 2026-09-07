"""Bảng xếp hạng doanh số và thưởng sao tháng — FR-12.3, FR-12.4, ADR-015.

**Ngoại lệ phạm vi có chủ ý** (ADR-015 mục 5, Q66): bảng xếp hạng đọc
`orders.Order` của toàn công ty, không qua `in_scope`, vì đây là chỉ số gộp
cho văn hoá — chỉ trả hạng, tên, số đơn và tổng đã quy đổi, không bao giờ trả
chi tiết đơn. Đổi luật này là đổi ADR, không sửa lặng lẽ.
"""
from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone

from core.audit import record
from core.constants import AuditAction
from core.exceptions import BusinessError
from orders.models import Order

from ..constants import LEADERBOARD_ROWS, MONTHLY_RANK_STARS, PERIOD_FORMAT, StarSource
from ..models import StarAward
from .recognition_service import active_users, current_period, rank_class


def parse_period(period):
    try:
        return datetime.strptime(period, PERIOD_FORMAT).date().replace(day=1)
    except (TypeError, ValueError):
        raise BusinessError("Kỳ phải có dạng YYYY-MM, ví dụ 2026-09.")


def previous_period(today=None):
    today = today or timezone.localdate()
    dau_thang = today.replace(day=1)
    thang_truoc = (dau_thang - timedelta(days=1)).replace(day=1)
    return thang_truoc.strftime(PERIOD_FORMAT)


def month_range(period=None):
    """(đầu tháng, đầu tháng sau) dạng giờ có múi Việt Nam — BR-7."""
    dau = parse_period(period) if period else timezone.localdate().replace(day=1)
    cuoi = date(dau.year + (dau.month == 12), dau.month % 12 + 1, 1)
    mui = timezone.get_current_timezone()
    return (
        timezone.make_aware(datetime.combine(dau, time.min), mui),
        timezone.make_aware(datetime.combine(cuoi, time.min), mui),
    )


def to_vnd(amount, currency):
    """Quy về VND bằng tỉ giá cố định trong settings (Decimal, BR-8)."""
    ti_gia = settings.EXCHANGE_RATES_VND.get(currency)
    if ti_gia is None:
        raise BusinessError(f"Chưa có tỉ giá cho {currency} trong EXCHANGE_RATES_VND.")
    return (Decimal(amount) * Decimal(ti_gia)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def format_vnd(so):
    """15000000 → "15.000.000" — cách nhóm số kiểu Việt Nam."""
    return f"{int(so):,}".replace(",", ".")


def sales_leaderboard(period=None, *, limit=LEADERBOARD_ROWS, users=None):
    """Top người bán tháng: gộp theo (người bán, tiền tệ) rồi quy đổi và xếp hạng.

    Đơn đã bỏ (xoá mềm) không tính. Trả `[{hang, user, so_don, tong_vnd, sao_thuong}]`.
    """
    dau, cuoi = month_range(period)
    rows = (
        Order.all_objects.alive()          # ngoại lệ phạm vi có chủ ý — xem docstring
        .filter(created_at__gte=dau, created_at__lt=cuoi, seller__isnull=False)
        .values("seller", "currency")
        .annotate(so_don=Count("id"), tong=Sum("total"))
    )
    gop = {}
    for r in rows:
        muc = gop.setdefault(r["seller"], {"so_don": 0, "tong_vnd": Decimal("0")})
        muc["so_don"] += r["so_don"]
        muc["tong_vnd"] += to_vnd(r["tong"] or 0, r["currency"])
    thu_tu = sorted(gop.items(), key=lambda kv: (-kv[1]["tong_vnd"], -kv[1]["so_don"], kv[0]))[:limit]
    users = users if users is not None else active_users()
    ket_qua = []
    for hang, (uid, muc) in enumerate(thu_tu, start=1):
        nguoi = users.get(uid)
        if nguoi is None:
            continue
        ket_qua.append({
            "hang": hang, "lop_hang": rank_class(hang), "user": nguoi,
            "so_don": muc["so_don"], "tong_vnd": muc["tong_vnd"],
            "tong_hien": format_vnd(muc["tong_vnd"]),
            "sao_thuong": MONTHLY_RANK_STARS[hang - 1] if hang <= len(MONTHLY_RANK_STARS) else 0,
        })
    return ket_qua


@transaction.atomic
def award_monthly_stars(period, *, actor=None, request=None):
    """Thưởng 5/3/1 sao cho top 3 của `period`; chạy lại không nhân đôi — FR-12.4."""
    parse_period(period)
    top = sales_leaderboard(period, limit=len(MONTHLY_RANK_STARS))
    moi = 0
    for dong in top:
        _, tao = StarAward.objects.get_or_create(
            receiver=dong["user"], period=period, source=StarSource.XEP_HANG,
            defaults={"stars": dong["sao_thuong"], "rank": dong["hang"]},
        )
        moi += int(tao)
    record(
        AuditAction.CREATE, actor=actor, target=("star_award", period),
        detail=f"Thưởng sao xếp hạng {period}: {len(top)} người trong top, {moi} dòng sao mới",
        request=request,
    )
    return moi


__all__ = [
    "award_monthly_stars", "format_vnd", "month_range",
    "parse_period", "previous_period", "sales_leaderboard", "to_vnd",
]
