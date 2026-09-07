"""Ghi nhận và sao — FR-12.1, FR-12.2, FR-12.5, ADR-015.

Tầng dịch vụ, không biết gì về HTTP (điều cấm 2). Sổ sao chỉ ghi thêm.
"""
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from core.audit import record
from core.constants import AuditAction
from core.exceptions import BusinessError
from core.identity import display_name

from ..constants import (
    MESSAGE_MAX, PERIOD_FORMAT, STAR_TOP, STARS_PER_RECOGNITION, CoreValue, StarSource,
)
from ..models import Recognition, StarAward


def period_of(day):
    return day.strftime(PERIOD_FORMAT)


def rank_class(hang):
    """Lớp CSS tô vàng, bạc, đồng cho ba hạng đầu; hạng sau không tô."""
    return f"hang-so-{hang}" if hang <= 3 else ""


def current_period():
    return period_of(timezone.localdate())


def active_users():
    """Mọi tài khoản đang hoạt động có hồ sơ, một truy vấn — dùng làm bản đồ id → người."""
    return {
        u.pk: u for u in get_user_model().objects
        .filter(is_active=True, profile__isnull=False)
        .select_related("profile", "profile__department", "profile__team")   # ô chọn hiện bộ phận
        .order_by("profile__full_name", "username")
    }


def recipients(actor, users=None):
    """Ai được ghi nhận: mọi người đang hoạt động trừ chính mình — FR-12.1."""
    users = users if users is not None else active_users()
    return [u for u in users.values() if u.pk != actor.pk]


@transaction.atomic
def give_recognition(*, receiver, value, message, actor, request=None):
    """Ghi nhận đồng nghiệp và cộng sao cùng một giao dịch — FR-12.1, FR-12.2."""
    if receiver is None or receiver.pk == actor.pk:
        raise BusinessError("Không tự ghi nhận chính mình.")
    if not receiver.is_active or getattr(receiver, "profile", None) is None:
        raise BusinessError("Người này không còn hoạt động.")
    if value not in CoreValue.values:
        raise BusinessError("Chọn một giá trị văn hoá trong danh sách.")
    message = (message or "").strip()
    if not message:
        raise BusinessError("Viết một lời nhắn cho người được ghi nhận.")
    if len(message) > MESSAGE_MAX:
        raise BusinessError(f"Lời nhắn dài quá {MESSAGE_MAX} ký tự.")

    ghi_nhan = Recognition.objects.create(
        giver=actor, receiver=receiver, value=value, message=message,
    )
    StarAward.objects.create(
        receiver=receiver, source=StarSource.GHI_NHAN, stars=STARS_PER_RECOGNITION,
        period=current_period(), recognition=ghi_nhan,
    )
    record(
        AuditAction.CREATE, actor=actor, target=ghi_nhan,
        detail=f"Ghi nhận #{ghi_nhan.pk} — {CoreValue(value).label} — tặng {display_name(receiver)}",
        request=request,
    )
    return ghi_nhan


def recognitions_qs():
    return Recognition.objects.select_related(
        "giver", "giver__profile", "receiver", "receiver__profile",
    )


def received_by(user):
    return recognitions_qs().filter(receiver=user)


def star_totals(*, period=None, limit=STAR_TOP, users=None):
    """Nhiều sao nhất: tất cả các kỳ, kèm riêng số sao của `period` — một truy vấn gộp."""
    period = period or current_period()
    rows = (
        StarAward.objects.values("receiver")
        .annotate(sao=Sum("stars"), sao_ky=Sum("stars", filter=Q(period=period)))
        .order_by("-sao", "receiver")[:limit]
    )
    users = users if users is not None else active_users()
    ket_qua = []
    for hang, r in enumerate(rows, start=1):
        nguoi = users.get(r["receiver"])
        if nguoi is None:
            continue
        ket_qua.append({
            "hang": hang, "lop_hang": rank_class(hang), "user": nguoi,
            "sao": r["sao"], "sao_ky": r["sao_ky"] or 0,
        })
    return ket_qua


def stars_of(user, period=None):
    qs = StarAward.objects.filter(receiver=user)
    if period:
        qs = qs.filter(period=period)
    return qs.aggregate(t=Sum("stars"))["t"] or 0


def stars_by_period(user):
    """[(kỳ, sao)] mới nhất trước — cho trang thành viên."""
    rows = (
        StarAward.objects.filter(receiver=user).values("period")
        .annotate(sao=Sum("stars")).order_by("-period")
    )
    return [(r["period"], r["sao"]) for r in rows]
