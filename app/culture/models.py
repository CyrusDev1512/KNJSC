"""Ghi nhận văn hoá và sao — FR-12.1 tới FR-12.5, ADR-015.

Hai bảng này là sổ cái: chỉ ghi thêm, không sửa, không xoá (như báo cáo đã
nộp, BR-2) để tổng sao không bao giờ lệch với lịch sử.
"""
from django.conf import settings
from django.db import models
from django.db.models import Q

from core.models import TimestampedModel

from .constants import MESSAGE_MAX, CoreValue, StarSource


class Recognition(TimestampedModel):
    """Một lần ghi nhận đồng nghiệp theo một giá trị văn hoá."""

    giver = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Người ghi nhận",
        on_delete=models.PROTECT, related_name="recognitions_given",
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Người được ghi nhận",
        on_delete=models.PROTECT, related_name="recognitions_received", db_index=True,
    )
    value = models.CharField("Giá trị văn hoá", max_length=16, choices=CoreValue.choices)
    message = models.CharField("Lời nhắn", max_length=MESSAGE_MAX)

    class Meta:
        verbose_name = "Ghi nhận"
        verbose_name_plural = "Ghi nhận"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["receiver", "-created_at"], name="recognition_receiver_idx"),
        ]

    def __str__(self):
        return f"Ghi nhận #{self.pk}"


class StarAward(TimestampedModel):
    """Một dòng sao: từ một ghi nhận, hoặc từ xếp hạng doanh số tháng."""

    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Người nhận",
        on_delete=models.PROTECT, related_name="star_awards", db_index=True,
    )
    source = models.CharField("Nguồn", max_length=12, choices=StarSource.choices, db_index=True)
    stars = models.PositiveSmallIntegerField("Số sao")
    period = models.CharField("Kỳ", max_length=7, db_index=True)
    rank = models.PositiveSmallIntegerField("Hạng", null=True, blank=True)
    recognition = models.OneToOneField(
        Recognition, verbose_name="Ghi nhận", null=True, blank=True,
        on_delete=models.PROTECT, related_name="star_award",
    )

    class Meta:
        verbose_name = "Sao"
        verbose_name_plural = "Sao"
        ordering = ["-created_at"]
        constraints = [
            # Thưởng tháng chạy lại không được nhân đôi — FR-12.4
            models.UniqueConstraint(
                fields=["receiver", "period", "source"],
                condition=Q(source="xep_hang"),
                name="star_rank_unique_per_month",
            ),
        ]
        indexes = [
            models.Index(fields=["period", "source"], name="star_period_source_idx"),
        ]

    def __str__(self):
        return f"{self.stars} sao — {self.receiver_id} — {self.period}"
