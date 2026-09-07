"""Bảng tin — FR-10.1 tới FR-10.6, ADR-015.

Bài, bình luận, lượt thích. Gỡ là xoá mềm (BR-4); bỏ thích cũng là xoá mềm,
thích lại chỉ bỏ dấu xoá nên một người một bài không bao giờ quá một dòng.
Thiệp sinh nhật là bài không có tác giả (hệ thống đăng), mỗi người mỗi ngày
sinh nhật đúng một thiệp — kể cả khi thiệp đã bị gỡ.
"""
from django.conf import settings
from django.db import models
from django.db.models import Q

from core.models import SoftDeleteModel, TimestampedModel

from .constants import COMMENT_MAX, PostKind
from .managers import (
    AllCommentManager, AllLikeManager, AllPostManager, CommentManager, LikeManager, PostManager,
)


class Post(TimestampedModel, SoftDeleteModel):
    """Một bài trên Bảng tin: bài viết của một người, hoặc thiệp sinh nhật của hệ thống."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Tác giả",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="posts",
    )
    kind = models.CharField(
        "Loại", max_length=12, choices=PostKind.choices, default=PostKind.BAI_VIET, db_index=True,
    )
    body = models.TextField("Nội dung")
    subject = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Người được chúc",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="birthday_posts",
    )
    birthday_on = models.DateField("Ngày sinh nhật", null=True, blank=True)
    is_pinned = models.BooleanField("Ghim", default=False)      # chỉ mục ghép post_pinned_created_idx đã đủ
    pinned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Người ghim",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )
    pinned_at = models.DateTimeField("Ghim lúc", null=True, blank=True)

    objects = PostManager()
    all_objects = AllPostManager()

    class Meta:
        verbose_name = "Bài"
        verbose_name_plural = "Bài"
        ordering = ["-is_pinned", "-created_at"]
        constraints = [
            # Mỗi người mỗi ngày sinh nhật một thiệp, kể cả thiệp đã gỡ — FR-10.4
            models.UniqueConstraint(
                fields=["subject", "birthday_on"], condition=Q(kind="sinh_nhat"),
                name="post_birthday_unique_per_day",
            ),
        ]
        indexes = [
            models.Index(fields=["-is_pinned", "-created_at"], name="post_pinned_created_idx"),
            models.Index(fields=["author", "-created_at"], name="post_author_created_idx"),
        ]

    def __str__(self):
        return f"Bài #{self.pk}"

    @property
    def la_sinh_nhat(self):
        return self.kind == PostKind.SINH_NHAT


class Comment(TimestampedModel, SoftDeleteModel):
    post = models.ForeignKey(Post, verbose_name="Bài", on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Người viết",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="comments",
    )
    body = models.CharField("Nội dung", max_length=COMMENT_MAX)

    objects = CommentManager()
    all_objects = AllCommentManager()

    class Meta:
        verbose_name = "Bình luận"
        verbose_name_plural = "Bình luận"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["post", "created_at"], name="comment_post_created_idx"),
        ]

    def __str__(self):
        return f"Bình luận #{self.pk}"


class Like(TimestampedModel, SoftDeleteModel):
    post = models.ForeignKey(Post, verbose_name="Bài", on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Người thích", on_delete=models.CASCADE, related_name="likes",
    )

    objects = LikeManager()
    all_objects = AllLikeManager()

    class Meta:
        verbose_name = "Lượt thích"
        verbose_name_plural = "Lượt thích"
        constraints = [
            models.UniqueConstraint(fields=["post", "user"], name="like_unique_post_user"),
        ]

    def __str__(self):
        return f"Thích bài #{self.post_id}"
