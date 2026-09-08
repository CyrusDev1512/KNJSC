"""Manager của Bảng tin.

Bảng tin là của toàn công ty (FR-10.1): ai đăng nhập cũng thấy mọi bài, nên
không có `in_scope`. Việc còn lại của manager là loại bản ghi đã xoá mềm và
đếm thích, bình luận (ngân sách AC-10.2).
"""
from django.db import models
from django.db.models import Count, IntegerField, OuterRef, Subquery
from django.db.models.functions import Coalesce

from core.managers import AliveManager, SoftDeleteQuerySet


def _dem(model, ten_khoa="post"):
    """Truy vấn con đếm bản ghi còn sống của `model` trỏ về bài — không GROUP BY,
    không nhân chéo hai bảng như khi nối thích và bình luận cùng lúc."""
    con = (
        model.objects.filter(**{ten_khoa: OuterRef("pk")})
        .order_by().values(ten_khoa).annotate(c=Count("pk")).values("c")[:1]
    )
    return Coalesce(Subquery(con, output_field=IntegerField()), 0)


class PostQuerySet(SoftDeleteQuerySet):
    def with_counts(self):
        """Số thích và số bình luận còn sống, gắn vào từng bài."""
        like = self.model._meta.get_field("likes").related_model
        comment = self.model._meta.get_field("comments").related_model
        return self.annotate(so_thich=_dem(like), so_binh_luan=_dem(comment))


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
