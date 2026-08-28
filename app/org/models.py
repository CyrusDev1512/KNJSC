"""Cơ cấu tổ chức và tài khoản.

ADR-003: bộ phận và cấp bậc là hai cột riêng, không gộp thành một chuỗi
vai trò. Cấp bậc quyết định phạm vi rộng bao nhiêu, bộ phận quyết định
phạm vi ở đâu.

`UserProfile` là bên thực hiện giao ước mà `core.scope` yêu cầu: phải có
`rank`, `department_id` và `scope_team_ids()`.
"""
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.db import models

from core.constants import Rank
from core.models import SoftDeleteModel, TimestampedModel

from .managers import (
    AllDepartmentManager, AllTeamManager, DepartmentManager, ProfileManager,
    TeamManager,
)


class Department(TimestampedModel, SoftDeleteModel):
    """Bộ phận. Thêm bộ phận mới chỉ là thêm một dòng dữ liệu (ADR-003)."""

    name = models.CharField("Tên bộ phận", max_length=100, unique=True)
    code = models.SlugField("Mã", max_length=30, unique=True)
    is_active = models.BooleanField("Đang hoạt động", default=True, db_index=True)

    objects = DepartmentManager()
    all_objects = AllDepartmentManager()

    class Meta:
        verbose_name = "Bộ phận"
        verbose_name_plural = "Bộ phận"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Team(TimestampedModel, SoftDeleteModel):
    """Team nằm trong một bộ phận.

    Một team có đúng một Leader. Một Leader phụ trách được nhiều team —
    đây là câu hỏi A5 chưa chốt, nên chọn cách rộng hơn để sau này thu hẹp
    lại được mà không phải đổi cấu trúc dữ liệu.
    """

    name = models.CharField("Tên team", max_length=100)
    department = models.ForeignKey(
        Department, verbose_name="Bộ phận",
        on_delete=models.PROTECT, related_name="teams", db_index=True,
    )
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Trưởng nhóm",
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="led_teams", db_index=True,
    )
    is_active = models.BooleanField("Đang hoạt động", default=True, db_index=True)

    objects = TeamManager()
    all_objects = AllTeamManager()

    class Meta:
        verbose_name = "Team"
        verbose_name_plural = "Team"
        ordering = ["department__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["department", "name"], name="team_unique_trong_bo_phan",
            )
        ]

    def __str__(self):
        return f"{self.name}"


class UserProfile(TimestampedModel):
    """Hồ sơ nhân sự gắn với một tài khoản đăng nhập.

    Tách khỏi bảng tài khoản để mật khẩu và thông tin nhân sự không nằm
    chung một chỗ.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, verbose_name="Tài khoản",
        on_delete=models.CASCADE, related_name="profile",
    )
    full_name = models.CharField("Họ tên", max_length=150, blank=True)
    department = models.ForeignKey(
        Department, verbose_name="Bộ phận",
        null=True, blank=True, on_delete=models.PROTECT,
        related_name="members", db_index=True,
    )
    team = models.ForeignKey(
        Team, verbose_name="Team",
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="members", db_index=True,
    )
    rank = models.CharField(
        "Cấp bậc", max_length=10, choices=Rank.choices,
        default=Rank.STAFF, db_index=True,
    )

    # Trạng thái đăng nhập
    must_change_password = models.BooleanField("Buộc đổi mật khẩu", default=True)
    failed_login_count = models.PositiveSmallIntegerField("Số lần sai liên tiếp", default=0)
    locked_until = models.DateTimeField("Khoá tới", null=True, blank=True)
    last_login_at = models.DateTimeField("Đăng nhập lần cuối", null=True, blank=True)

    # Tăng lên mỗi khi đổi quyền hoặc khoá tài khoản, làm mọi phiên đang
    # mở mất hiệu lực ngay lập tức (nguyên tắc P4)
    session_epoch = models.PositiveIntegerField("Mốc phiên", default=0)

    objects = ProfileManager()

    class Meta:
        verbose_name = "Hồ sơ nhân sự"
        verbose_name_plural = "Hồ sơ nhân sự"
        ordering = ["full_name"]
        indexes = [
            models.Index(fields=["department", "rank"], name="profile_dept_rank_idx"),
            # Tìm theo họ tên dùng __icontains — cần GIN với pg_trgm
            GinIndex(
                name="profile_full_name_trgm",
                fields=["full_name"],
                opclasses=["gin_trgm_ops"],
            ),
        ]

    def __str__(self):
        return self.full_name or self.user.get_username()

    # ── Giao ước với core.scope ────────────────────────────────────
    def scope_team_ids(self):
        """Các team người này phụ trách. Chỉ Leader mới có."""
        if self.rank != Rank.LEADER:
            return ()
        return tuple(
            Team.objects.filter(leader_id=self.user_id).values_list("id", flat=True)
        )

    # ── Vô hiệu phiên đang mở ──────────────────────────────────────
    #: Đổi một trong các cột này thì mọi phiên đang mở phải mất hiệu lực
    SESSION_SENSITIVE_FIELDS = ("rank", "department_id", "team_id")

    def invalidate_sessions(self):
        self.session_epoch += 1

    def save(self, *args, **kwargs):
        if self.pk:
            cu = type(self).objects.filter(pk=self.pk).values(
                *self.SESSION_SENSITIVE_FIELDS
            ).first()
            if cu and any(cu[c] != getattr(self, c) for c in self.SESSION_SENSITIVE_FIELDS):
                self.invalidate_sessions()
                fields = kwargs.get("update_fields")
                if fields is not None:
                    kwargs["update_fields"] = list(fields) + ["session_epoch"]
        return super().save(*args, **kwargs)
