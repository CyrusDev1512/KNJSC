"""Ghi nhận văn hoá và sổ sao — FR-12.1 tới FR-12.5, ADR-015.

Chạy xuôi: tạo `culture_recognition` và `culture_staraward` kèm chỉ mục theo
người nhận, theo (kỳ, nguồn) và ràng buộc mỗi người mỗi kỳ một dòng sao xếp
hạng. Chạy ngược: bỏ hai bảng.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Recognition",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, db_index=True, verbose_name="Tạo lúc"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Sửa lúc"),
                ),
                (
                    "value",
                    models.CharField(
                        choices=[
                            ("tan_tam", "Tận tâm"),
                            ("chinh_truc", "Chính trực"),
                            ("hop_tac", "Hợp tác"),
                            ("sang_tao", "Sáng tạo"),
                            ("trach_nhiem", "Trách nhiệm"),
                        ],
                        max_length=16,
                        verbose_name="Giá trị văn hoá",
                    ),
                ),
                ("message", models.CharField(max_length=300, verbose_name="Lời nhắn")),
                (
                    "giver",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="recognitions_given",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Người ghi nhận",
                    ),
                ),
                (
                    "receiver",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="recognitions_received",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Người được ghi nhận",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ghi nhận",
                "verbose_name_plural": "Ghi nhận",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="StarAward",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, db_index=True, verbose_name="Tạo lúc"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Sửa lúc"),
                ),
                (
                    "source",
                    models.CharField(
                        choices=[
                            ("ghi_nhan", "Ghi nhận"),
                            ("xep_hang", "Xếp hạng doanh số"),
                        ],
                        db_index=True,
                        max_length=12,
                        verbose_name="Nguồn",
                    ),
                ),
                ("stars", models.PositiveSmallIntegerField(verbose_name="Số sao")),
                (
                    "period",
                    models.CharField(db_index=True, max_length=7, verbose_name="Kỳ"),
                ),
                (
                    "rank",
                    models.PositiveSmallIntegerField(
                        blank=True, null=True, verbose_name="Hạng"
                    ),
                ),
                (
                    "receiver",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="star_awards",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Người nhận",
                    ),
                ),
                (
                    "recognition",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="star_award",
                        to="culture.recognition",
                        verbose_name="Ghi nhận",
                    ),
                ),
            ],
            options={
                "verbose_name": "Sao",
                "verbose_name_plural": "Sao",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="recognition",
            index=models.Index(
                fields=["receiver", "-created_at"], name="recognition_receiver_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="staraward",
            index=models.Index(
                fields=["period", "source"], name="star_period_source_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="staraward",
            constraint=models.UniqueConstraint(
                condition=models.Q(("source", "xep_hang")),
                fields=("receiver", "period", "source"),
                name="star_rank_unique_per_month",
            ),
        ),
    ]
