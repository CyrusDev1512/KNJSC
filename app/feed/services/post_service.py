"""Quy tắc của Bảng tin — FR-10.1 tới FR-10.6, ADR-015.

Tầng dịch vụ, không biết gì về HTTP (điều cấm 2). Mọi tương tác đều ghi nhật
ký (FR-10.6, BR-5) và nằm trong một giao dịch. Thanh bên mượn `culture` cho
sao và ghi nhận — chiều phụ thuộc `feed → culture, org`, không ai import feed.
"""
import calendar
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from core.audit import record
from core.constants import AuditAction, Rank
from core.exceptions import BusinessError, OutOfScopeError
from core.identity import display_name
from core.permissions import has_rank
from culture.services import recognition_service

from ..constants import (
    BIRTHDAY_MESSAGE, BODY_MAX, COMMENT_MAX, NEW_MEMBER_DAYS, SIDEBAR_NEW_MEMBERS,
    SIDEBAR_RECOGNITIONS, SIDEBAR_STARS, PostKind,
)
from ..models import Comment, Like, Post


# ══ QUYỀN ═════════════════════════════════════════════════════════

def can_moderate(user):
    """Manager và Admin ghim, gỡ ghim và gỡ được bài bất kỳ — FR-10.3."""
    return has_rank(user, Rank.MANAGER)


def can_delete_post(user, post):
    return post.author_id == getattr(user, "pk", None) or can_moderate(user)


def can_delete_comment(user, comment):
    return comment.author_id == getattr(user, "pk", None) or can_moderate(user)


# ══ ĐỌC ═══════════════════════════════════════════════════════════

def feed_qs(user):
    """Mọi bài còn sống, ghim đứng đầu, kèm số thích, số bình luận và
    người này đã thích chưa — một truy vấn (FR-10.1)."""
    return (
        Post.objects.select_related(
            "author", "author__profile", "author__profile__department", "subject", "subject__profile",
        )
        .with_counts()
        .annotate(da_thich=Exists(Like.objects.filter(post=OuterRef("pk"), user=user)))
        # Truy vấn có GROUP BY thì Django bỏ Meta.ordering — phải nói rõ lại
        .order_by("-is_pinned", "-created_at")
    )


def comments_of(post):
    return Comment.objects.filter(post=post).select_related("author", "author__profile")


def comment_by_pk(pk):
    """Bình luận còn sống của một bài còn sống, không có thì None."""
    return Comment.objects.select_related("post").filter(pk=pk, post__deleted_at__isnull=True).first()


def like_count(post):
    return Like.objects.filter(post=post).count()


# ══ GHI ═══════════════════════════════════════════════════════════

@transaction.atomic
def create_post(*, body, actor, request=None):
    """Đăng bài dạng chữ — FR-10.1."""
    body = (body or "").strip()
    if not body:
        raise BusinessError("Viết nội dung trước khi đăng.")
    if len(body) > BODY_MAX:
        raise BusinessError(f"Bài dài quá {BODY_MAX} ký tự.")
    bai = Post.objects.create(author=actor, body=body, kind=PostKind.BAI_VIET)
    record(AuditAction.CREATE, actor=actor, target=bai, detail=f"Đăng bài #{bai.pk}", request=request)
    return bai


@transaction.atomic
def delete_post(post, *, actor, request=None):
    """Gỡ bài: tác giả, hoặc Manager trở lên. Xoá mềm (BR-4) — FR-10.3."""
    if not can_delete_post(actor, post):
        raise OutOfScopeError("Bạn chỉ gỡ được bài của mình.")
    post.delete(by=actor)
    record(AuditAction.DELETE, actor=actor, target=post, detail=f"Gỡ bài #{post.pk}", request=request)
    return post


@transaction.atomic
def pin_post(post, *, actor, request=None):
    """Ghim bài lên đầu — Manager trở lên (FR-10.3)."""
    if not can_moderate(actor):
        raise OutOfScopeError("Chỉ quản lý trở lên ghim được bài.")
    post.is_pinned, post.pinned_by, post.pinned_at = True, actor, timezone.now()
    post.save(update_fields=["is_pinned", "pinned_by", "pinned_at", "updated_at"])
    record(AuditAction.UPDATE, actor=actor, target=post, detail=f"Ghim bài #{post.pk}", request=request)
    return post


@transaction.atomic
def unpin_post(post, *, actor, request=None):
    if not can_moderate(actor):
        raise OutOfScopeError("Chỉ quản lý trở lên gỡ ghim được.")
    post.is_pinned, post.pinned_by, post.pinned_at = False, None, None
    post.save(update_fields=["is_pinned", "pinned_by", "pinned_at", "updated_at"])
    record(AuditAction.UPDATE, actor=actor, target=post, detail=f"Gỡ ghim bài #{post.pk}", request=request)
    return post


@transaction.atomic
def add_comment(post, *, body, actor, request=None):
    """Bình luận vào một bài — FR-10.2."""
    body = (body or "").strip()
    if not body:
        raise BusinessError("Viết nội dung bình luận.")
    if len(body) > COMMENT_MAX:
        raise BusinessError(f"Bình luận dài quá {COMMENT_MAX} ký tự.")
    bl = Comment.objects.create(post=post, author=actor, body=body)
    record(
        AuditAction.CREATE, actor=actor, target=bl,
        detail=f"Bình luận #{bl.pk} vào bài #{post.pk}", request=request,
    )
    return bl


@transaction.atomic
def delete_comment(comment, *, actor, request=None):
    """Gỡ bình luận: người viết, hoặc Manager trở lên. Xoá mềm."""
    if not can_delete_comment(actor, comment):
        raise OutOfScopeError("Bạn chỉ gỡ được bình luận của mình.")
    comment.delete(by=actor)
    record(
        AuditAction.DELETE, actor=actor, target=comment,
        detail=f"Gỡ bình luận #{comment.pk} của bài #{comment.post_id}", request=request,
    )
    return comment


@transaction.atomic
def toggle_like(post, *, actor, request=None):
    """Thích, bấm lại là bỏ thích. Trả về True nếu sau khi bấm là đã thích — FR-10.2.

    Bỏ thích là xoá mềm; thích lại chỉ bỏ dấu xoá, nên mỗi người mỗi bài
    không bao giờ quá một dòng (ràng buộc duy nhất).
    """
    like = Like.all_objects.filter(post=post, user=actor).first()
    if like is None:
        like, da_thich = Like.objects.create(post=post, user=actor), True
    elif like.deleted_at is None:
        like.delete(by=actor)
        da_thich = False
    else:
        like.deleted_at, like.deleted_by, da_thich = None, None, True
        like.save(update_fields=["deleted_at", "deleted_by", "updated_at"])
    record(
        AuditAction.CREATE if da_thich else AuditAction.DELETE, actor=actor, target=like,
        detail=f"{'Thích' if da_thich else 'Bỏ thích'} bài #{post.pk}", request=request,
    )
    return da_thich


# ══ THIỆP SINH NHẬT — FR-10.4 ═════════════════════════════════════

def _sinh_nhat_ngay(on):
    """Điều kiện hồ sơ có sinh nhật đúng ngày `on`. Sinh 29.02 thì năm không
    nhuận được chúc ngày 28.02, không bị bỏ quên."""
    dk = Q(profile__birthday__month=on.month, profile__birthday__day=on.day)
    if on.month == 2 and on.day == 28 and not calendar.isleap(on.year):
        dk |= Q(profile__birthday__month=2, profile__birthday__day=29)
    return dk


@transaction.atomic
def create_birthday_posts(on=None, *, actor=None, request=None):
    """Đăng thiệp cho mọi người có sinh nhật ngày `on` (mặc định hôm nay theo
    giờ Việt Nam). Chạy lại không nhân đôi; thiệp đã gỡ cũng không đăng lại.
    Chỉ ghi nhật ký khi có thiệp mới — tác vụ chạy mỗi sáng, không rải dòng
    "0 thiệp" lên nhật ký. Trả về số thiệp mới."""
    on = on or timezone.localdate()
    nguoi = (
        get_user_model().objects.filter(_sinh_nhat_ngay(on), is_active=True)
        .select_related("profile").order_by("pk")
    )
    moi = 0
    for u in nguoi:
        _, tao = Post.all_objects.get_or_create(
            kind=PostKind.SINH_NHAT, subject=u, birthday_on=on,
            defaults={"author": None, "body": BIRTHDAY_MESSAGE.format(ten=display_name(u))},
        )
        moi += int(tao)
    if moi:
        record(
            AuditAction.CREATE, actor=actor, target=("post", on.isoformat()),
            detail=f"Thiệp sinh nhật {on:%d.%m.%Y}: {moi} thiệp mới", request=request,
        )
    return moi


# ══ THANH BÊN — FR-10.5 ═══════════════════════════════════════════

def sidebar(user):
    """Bốn khối thanh bên bằng ba truy vấn: bản đồ người của `culture` dùng
    chung cho sinh nhật tháng này, nhiều sao nhất và thành viên mới."""
    hom_nay = timezone.localdate()
    nguoi = recognition_service.active_users()

    sinh_nhat = []
    for u in nguoi.values():
        ns = u.profile.birthday
        if ns and ns.month == hom_nay.month:
            u.sinh_nhat_hom_nay = ns.day == hom_nay.day
            sinh_nhat.append(u)
    sinh_nhat.sort(key=lambda u: (u.profile.birthday.day, display_name(u)))

    moc = timezone.now() - timedelta(days=NEW_MEMBER_DAYS)
    thanh_vien_moi = sorted(
        (u for u in nguoi.values() if u.profile.created_at >= moc),
        key=lambda u: u.profile.created_at, reverse=True,
    )[:SIDEBAR_NEW_MEMBERS]

    return {
        "hom_nay": hom_nay,
        "sinh_nhat_thang": sinh_nhat,
        "top_sao": recognition_service.star_totals(limit=SIDEBAR_STARS, users=nguoi),
        "ghi_nhan_moi": list(recognition_service.recognitions_qs()[:SIDEBAR_RECOGNITIONS]),
        "thanh_vien_moi": thanh_vien_moi,
    }
