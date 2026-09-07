"""Manager của Bảng tin.

Bảng tin là của toàn công ty (FR-10.1): ai đăng nhập cũng thấy mọi bài, nên
không có `in_scope`. Việc còn lại của manager là loại bản ghi đã xoá mềm và
đếm thích, bình luận bằng một truy vấn (ngân sách AC-10.2).
"""
from django.db import models
from django.db.models import Count, Q

from core.managers import SoftDeleteQuerySet


class AliveManager(models.Manager):
    """Loại sẵn bản ghi đã đánh dấu xoá; muốn lấy cả thì dùng `all_objects`."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class PostQuerySet(SoftDeleteQuerySet):
    def with_counts(self):
        """Số thích và số bình luận còn sống, gắn vào từng bài."""
        return self.annotate(
            so_thich=Count("likes", filter=Q(likes__deleted_at__isnull=True), distinct=True),
            so_binh_luan=Count("comments", filter=Q(comments__deleted_at__isnull=True), distinct=True),
        )


class PostManager(AliveManager.from_queryset(PostQuerySet)):
    pass


class AllPostManager(models.Manager.from_queryset(PostQuerySet)):
    pass


class CommentManager(AliveManager.from_queryset(SoftDeleteQuerySet)):
    pass


class AllCommentManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    pass


class LikeManager(AliveManager.from_queryset(SoftDeleteQuerySet)):
    pass


class AllLikeManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    pass
