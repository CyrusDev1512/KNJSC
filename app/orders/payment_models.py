"""Chứng từ thanh toán độc lập với nội dung ô và file xuất."""
from django.conf import settings
from django.db import models
from django.db.models.functions import Lower
from core.models import TimestampedModel, SoftDeleteModel


class PaymentDocument(TimestampedModel, SoftDeleteModel):
    record = models.ForeignKey('forms_builder.DataRecord', on_delete=models.PROTECT, related_name='payment_documents')
    reference = models.CharField(max_length=200)
    transfer_date = models.DateField(null=True, blank=True)
    note = models.CharField(max_length=1000, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    version = models.PositiveIntegerField(default=1)
    operation = models.UUIDField()
    fingerprint = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower('reference'), 'record', condition=models.Q(deleted_at__isnull=True), name='payment_ref_per_record'),
            models.UniqueConstraint(fields=['created_by', 'operation'], name='payment_create_operation'),
        ]
        indexes = [models.Index(fields=['record', 'created_at', 'id'], name='payment_record_created')]


class PaymentImage(TimestampedModel, SoftDeleteModel):
    document = models.ForeignKey(PaymentDocument, on_delete=models.PROTECT, related_name='images')
    file_path = models.CharField(max_length=300)
    file_name = models.CharField(max_length=200)
    file_kind = models.CharField(max_length=8)
    file_size = models.PositiveBigIntegerField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')

    class Meta:
        ordering = ['id']
