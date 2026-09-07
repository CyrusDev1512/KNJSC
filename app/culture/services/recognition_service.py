"""Ghi nhận và sao — FR-12.1, FR-12.2, FR-12.5, ADR-015.

Tầng dịch vụ, không biết gì về HTTP (điều cấm 2). Sổ sao chỉ ghi thêm.
Ghi nhận đi **từ trên xuống** (Q70, 07.09.2026): trưởng nhóm ghi nhận người
trong team mình, quản lý ghi nhận cả bộ phận, quản trị viên ghi nhận mọi
người; nhân viên không ghi nhận ai. Nhờ vậy sao không bị hai người khen qua
lại mà thổi lên.
"""
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from core.audit import record
from core.constants import AuditAction, Rank, rank_level
from core.exceptions import BusinessError, OutOfScopeError
from core.permissions import get_rank, has_rank
from core.scope import get_user_scope
from org.models import UserProfile

from ..constants import (
    MESSAGE_MAX, PERIOD_FORMAT, STAR_TOP, STARS_PER_RECOGNITION, CoreValue, StarSource,
)
from ..models import Recognition, StarAward


def period_of(day):
    return day.strftime(PERIOD_FORMAT)


def current_period():
    return period_of(timezone.localdate())


def period_label(ky):
    """"2026-09" → "09/2026" để hiện trên màn hình."""
    return f"{ky[5:]}/{ky[:4]}"


def rank_class(hang):
    """Lớp CSS tô vàng, bạc, đồng cho ba hạng đầu; hạng sau không tô."""
    return f"hang-so-{hang}" if hang <= 3 else ""


def competition_rank(items, key):
    """Xếp hạng kiểu thi đấu (Q72): bằng khoá thì đồng hạng, người kế tiếp nhảy
    hạng — 1, 1, 3. `items` đã sắp giảm dần theo `key`. Trả `[(hạng, item)]`."""
    ket_qua, hang, truoc = [], 0, object()
    for i, item in enumerate(items, start=1):
        k = key(item)
        if k != truoc:
            hang, truoc = i, k
        ket_qua.append((hang, item))
    return ket_qua


# ══ NGƯỜI ═════════════════════════════════════════════════════════

def active_users():
    """Mọi tài khoản đang hoạt động có hồ sơ, một truy vấn — dùng làm bản đồ id → người."""
    return {
        u.pk: u for u in get_user_model().objects
        .filter(is_active=True, profile__isnull=False)
        .select_related("profile", "profile__department")   # ô chọn hiện bộ phận; team không ai đọc
        .order_by("profile__full_name", "username")
    }


def active_user(pk):
    """Một tài khoản đang hoạt động có hồ sơ theo mã, không có thì None — một truy vấn."""
    return (
        get_user_model().objects.filter(pk=pk, is_active=True, profile__isnull=False)
        .select_related("profile", "profile__department", "profile__team").first()
    )


def can_recognize(user):
    """Từ Leader trở lên mới ghi nhận được — Q70."""
    return has_rank(user, Rank.LEADER)


def _cap_duoi_trong_pham_vi(actor):
    """Hồ sơ cấp dưới trong phạm vi của người ghi nhận: Leader → team mình phụ
    trách, Manager → bộ phận, Admin → mọi người — luôn thấp hơn cấp bậc của
    người ghi nhận, và không phải chính mình (Q70)."""
    muc = rank_level(get_rank(actor))
    thap_hon = [r for r in Rank.values if rank_level(r) < muc]
    return (
        UserProfile.objects.in_scope(actor)
        .filter(rank__in=thap_hon, user__is_active=True)
        .exclude(user=actor)
    )


def recipients(actor, users=None):
    """Ai được người này ghi nhận — FR-12.1, Q70. Nhân viên: không ai.

    Lọc trên bản đồ người đang hoạt động (đã nạp cho cả trang) theo `Scope`
    của người ghi nhận — cùng luật với `UserProfile.objects.in_scope`, nhưng
    không tốn thêm truy vấn (ngân sách AC-10.2). Lúc ghi thật thì
    `can_recognize_user` vẫn hỏi cơ sở dữ liệu.
    """
    if not can_recognize(actor):
        return []
    scope = get_user_scope(actor)
    muc = rank_level(scope.rank)
    users = users if users is not None else active_users()

    def trong_pham_vi(ho_so):
        if scope.all_departments:
            return True
        if scope.rank == Rank.MANAGER:
            return ho_so.department_id in scope.department_ids
        return ho_so.team_id is not None and ho_so.team_id in scope.team_ids

    return [
        u for u in users.values()
        if u.pk != actor.pk and rank_level(u.profile.rank) < muc and trong_pham_vi(u.profile)
    ]


def can_recognize_user(actor, receiver):
    """Người này có được ghi nhận người kia không — cùng luật với `recipients`."""
    return can_recognize(actor) and _cap_duoi_trong_pham_vi(actor).filter(user=receiver).exists()


# ══ GHI ═══════════════════════════════════════════════════════════

@transaction.atomic
def give_recognition(*, receiver, value, message, actor, request=None):
    """Ghi nhận cấp dưới và cộng sao cùng một giao dịch — FR-12.1, FR-12.2, Q70."""
    if not can_recognize(actor):
        raise OutOfScopeError("Chỉ trưởng nhóm trở lên mới ghi nhận được cấp dưới.")
    if receiver is None:
        raise BusinessError("Không tìm thấy đồng nghiệp này, hoặc tài khoản đã khoá.")
    if receiver.pk == actor.pk:
        raise BusinessError("Không tự ghi nhận chính mình.")
    if not receiver.is_active or getattr(receiver, "profile", None) is None:
        raise BusinessError("Người này không còn hoạt động.")
    if not can_recognize_user(actor, receiver):
        raise BusinessError(
            "Chỉ ghi nhận được cấp dưới trong phạm vi của bạn: trưởng nhóm ghi nhận "
            "người trong team mình, quản lý ghi nhận cả bộ phận."
        )
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
    # Ghi mã người nhận, không ghi tên: tên có thể chứa từ khoá khiến nhật ký bị lược bỏ
    record(
        AuditAction.CREATE, actor=actor, target=ghi_nhan,
        detail=f"Ghi nhận #{ghi_nhan.pk} — {CoreValue(value).label} — tặng #{receiver.pk}",
        request=request,
    )
    return ghi_nhan


# ══ ĐỌC ═══════════════════════════════════════════════════════════

def recognitions_qs():
    return Recognition.objects.select_related(
        "giver", "giver__profile", "receiver", "receiver__profile", "star_award",   # thẻ hiện số sao
    )


def received_by(user):
    return recognitions_qs().filter(receiver=user)


def star_summary(*, period=None, users=None):
    """`{mã người: {"sao": mọi kỳ, "sao_ky": riêng `period`}}` cho mọi người
    đang hoạt động — một truy vấn gộp, dùng cho cả bảng nhiều sao nhất lẫn
    "sao của tôi"."""
    period = period or current_period()
    users = users if users is not None else active_users()
    rows = (
        StarAward.objects.filter(receiver__in=list(users)).values("receiver")
        .annotate(sao=Sum("stars"), sao_ky=Sum("stars", filter=Q(period=period)))
    )
    return {r["receiver"]: {"sao": r["sao"], "sao_ky": r["sao_ky"] or 0} for r in rows}


def star_totals(*, period=None, limit=STAR_TOP, users=None, summary=None):
    """Nhiều sao nhất: người đã khoá bị loại trước khi xếp hạng, bằng sao thì
    đồng hạng (Q72)."""
    users = users if users is not None else active_users()
    summary = summary if summary is not None else star_summary(period=period, users=users)
    thu_tu = sorted(summary.items(), key=lambda kv: (-kv[1]["sao"], kv[0]))
    ket_qua = []
    for hang, (uid, s) in competition_rank(thu_tu, key=lambda kv: kv[1]["sao"]):
        ket_qua.append({
            "hang": hang, "lop_hang": rank_class(hang), "user": users[uid],
            "sao": s["sao"], "sao_ky": s["sao_ky"],
        })
    return ket_qua[:limit] if limit else ket_qua


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
