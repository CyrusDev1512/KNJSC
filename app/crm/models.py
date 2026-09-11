"""Biên nhận ghi lưới; dữ liệu nghiệp vụ vẫn thuộc forms_builder/orders."""
from django.conf import settings
from django.db import models


class GridRevision(models.Model):
    table = models.OneToOneField('forms_builder.TableDef', on_delete=models.CASCADE, primary_key=True)
    revision = models.BigIntegerField(default=0)
    fields = models.JSONField(default=dict)


class GridChange(models.Model):
    table = models.ForeignKey('forms_builder.TableDef', on_delete=models.CASCADE)
    revision = models.BigIntegerField()
    record_ids = models.JSONField(default=list)
    columns = models.JSONField(default=list)
    reset = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['table','revision'], name='crm_change_table_revision')]


class GridPendingChange(models.Model):
    """Chỉ tồn tại trong giao dịch; trigger deferred gom và xóa trước commit."""
    transaction_id = models.BigIntegerField(db_index=True)
    table_id = models.BigIntegerField()
    record_ids = models.JSONField(default=list)
    columns = models.JSONField(default=list)
    reset = models.BooleanField(default=False)


class GridMutationReceipt(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    table = models.ForeignKey('forms_builder.TableDef', on_delete=models.PROTECT)
    operation = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    result = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['actor', 'operation'], name='crm_mutation_actor_operation')]


class HistoryQuerySet(models.QuerySet):
    def bulk_create(self, objs, *args, **kwargs):
        if kwargs.get('update_conflicts'):
            raise RuntimeError('Lịch sử chỉ được ghi thêm.')
        return super().bulk_create(objs, *args, **kwargs)

    def update(self, **kwargs):
        raise RuntimeError('Lịch sử chỉ được ghi thêm.')

    def delete(self):
        raise RuntimeError('Lịch sử chỉ được ghi thêm.')


class GridCellHistory(models.Model):
    """Lịch sử nghiệp vụ có kiểm quyền dòng, không phải log kỹ thuật."""
    record = models.ForeignKey('forms_builder.DataRecord', on_delete=models.PROTECT)
    receipt = models.ForeignKey(GridMutationReceipt, on_delete=models.PROTECT)
    column = models.CharField(max_length=100)
    property = models.CharField(max_length=12, default='value')
    before = models.JSONField(null=True)
    after = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = HistoryQuerySet.as_manager()

    class Meta:
        indexes = [models.Index(fields=['record', '-id'], name='crm_history_record_id')]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise RuntimeError('Lịch sử chỉ được ghi thêm.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError('Lịch sử chỉ được ghi thêm.')
