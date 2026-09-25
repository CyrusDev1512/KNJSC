"""Kho chứng từ: quyền theo dòng, giao dịch nguyên tử và file riêng tư."""
from core.permissions import is_company_reader
from orders.constants import waybill_condition
import hashlib
import json
import uuid
from datetime import date
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.db.models import Count, F, Window
from django.db.models.functions import Coalesce, RowNumber, TruncDate
from django.utils import timezone

from core.audit import record as audit
from core.constants import AuditAction, FileKind
from core.excel import check_size, sniff_kind
from core.exceptions import BusinessError, OutOfScopeError
from core.scope import get_user_scope
from forms_builder.models import DataRecord
from orders.models import PaymentDocument, PaymentImage
from . import assignment_service, waybill_service

SUBDIR = 'chung-tu-thanh-toan'


def can_manage(user):
    if is_company_reader(user):
        return False
    return user.is_active and (get_user_scope(user).is_admin or assignment_service.is_accountant(user))


def can_create(user):
    if is_company_reader(user):
        return False
    return can_manage(user) or (user.is_active and assignment_service.department(user) == 'van-don')


def documents_for(user, *, include_deleted=False):
    if not user.is_active:
        raise OutOfScopeError()
    rows = DataRecord.objects.in_scope(user).filter(waybill_condition())
    documents = PaymentDocument.objects.filter(record_id__in=rows.values('pk'))
    if not include_deleted or not can_manage(user):
        documents = documents.filter(deleted_at__isnull=True)
    return documents


def document_for(user, pk, *, include_deleted=False):
    document = documents_for(user, include_deleted=include_deleted).filter(pk=pk).first()
    if document is None:
        raise OutOfScopeError()
    return document


def ordered(documents):
    return documents.annotate(payment_day=Coalesce('transfer_date', TruncDate('created_at'))).order_by('payment_day', 'id')


def metadata(record_ids):
    """Một truy vấn cho cả khối đã kiểm quyền; chỉ trả tối đa hai Ref/dòng."""
    documents = ordered(PaymentDocument.objects.filter(record_id__in=record_ids, deleted_at__isnull=True))
    result = {}
    first = documents.annotate(total=Window(Count('id'), partition_by=[F('record_id')]),
                              position=Window(RowNumber(), partition_by=[F('record_id')],
                                order_by=[F('payment_day'), F('id')])).filter(position__lte=2).only('id', 'record_id', 'reference')
    for doc in first:
        result.setdefault(doc.record_id, {'count': doc.total, 'links': []})
        result[doc.record_id]['links'].append({'id': doc.pk, 'reference': doc.reference,
                                              'position': doc.position})
    return result


def filter_options(records, search, limit):
    """UNION loại cặp dòng/Ref trùng trước khi đếm, kể cả Bill cũ."""
    scoped_sql, scoped_params = records.order_by().values('pk').query.sql_with_params()
    sql = f'''WITH scope(id) AS ({scoped_sql}), refs AS (
        SELECT p.record_id, p.reference AS label FROM orders_paymentdocument p
        JOIN scope s ON s.id=p.record_id WHERE p.deleted_at IS NULL
        UNION
        SELECT r.id, r.data->>'bill' FROM forms_builder_datarecord r
        JOIN scope s ON s.id=r.id WHERE COALESCE(r.data->>'bill', '') <> ''
    ) SELECT label, COUNT(*) FROM refs WHERE label ILIKE %s
      GROUP BY label ORDER BY COUNT(*) DESC, label LIMIT %s'''
    # LIKE pattern là tham số, không ghép nội dung người dùng vào SQL.
    pattern = '%' + connection.ops.prep_for_like_query(search) + '%'
    with connection.cursor() as cursor:
        cursor.execute(sql, [*scoped_params, pattern, limit])
        return cursor.fetchall()


def validated_files(uploads, *, required):
    if len(uploads) > 5 or (required and not uploads):
        raise BusinessError('Chọn từ 1 đến 5 ảnh JPG/PNG; mỗi lượt tối đa 10 MB.')
    check_size(sum(f.size for f in uploads))
    return [(f, sniff_kind(f, allowed={FileKind.JPG, FileKind.PNG})) for f in uploads]


def fields(reference, transfer_date, note):
    reference = str(reference).strip()
    if not reference or len(reference) > 200 or len(note) > 1000:
        raise BusinessError('Ref bắt buộc, tối đa 200 ký tự; ghi chú tối đa 1.000 ký tự.')
    try:
        transfer_date = date.fromisoformat(transfer_date) if transfer_date else None
    except (TypeError, ValueError):
        raise BusinessError('Ngày chuyển khoản không hợp lệ.')
    return {'reference': reference, 'transfer_date': transfer_date, 'note': note}


def unique_ref(row, reference, *, exclude=None):
    if PaymentDocument.objects.filter(record=row, deleted_at__isnull=True,
                                      reference__iexact=reference).exclude(pk=exclude).exists():
        raise BusinessError('Ref này đã tồn tại trên đơn. Hãy kiểm tra chứng từ hiện có.')


def save_files(document, files, user, created_paths):
    folder = Path(settings.STORAGE_DIR) / SUBDIR
    folder.mkdir(parents=True, exist_ok=True)
    for upload, kind in files:
        path = folder / f'{uuid.uuid4().hex}.{kind}'
        created_paths.append(path)
        with path.open('xb') as stream:
            for chunk in upload.chunks():
                stream.write(chunk)
        PaymentImage.objects.create(document=document, file_path=path.relative_to(settings.STORAGE_DIR).as_posix(),
            file_name=Path(upload.name).name[:200], file_kind=kind, file_size=upload.size, created_by=user)


def changed(row, document, user, action, *, mutation='create', image_ids=()):
    """Đánh thức cả polling cũ và journal tối ưu trong cùng giao dịch."""
    from crm.models import GridPendingChange
    row.save(update_fields=['updated_at'])
    with connection.cursor() as cursor:
        cursor.execute('SELECT txid_current()')
        transaction_id = cursor.fetchone()[0]
    GridPendingChange.objects.create(transaction_id=transaction_id, table_id=row.table_id,
                                    record_ids=[row.pk], columns=['bill'])
    audit(action, actor=user, target=document,
          detail=f'Chứng từ {document.pk}; dòng {row.pk}; {mutation}; ảnh {list(image_ids)}')


def create(user, row_id, reference, transfer_date, note, uploads, operation):
    if not can_create(user):
        raise OutOfScopeError()
    values = fields(reference, transfer_date, note)
    files = validated_files(uploads, required=True)
    try:
        operation = uuid.UUID(str(operation))
    except ValueError:
        raise BusinessError('Mã lượt tạo không hợp lệ.')
    digest = hashlib.sha256(json.dumps([row_id, values], sort_keys=True, default=str).encode())
    for upload, kind in files:
        digest.update(kind.encode())
        digest.update(json.dumps([upload.name, upload.size]).encode())
        for chunk in upload.chunks():
            digest.update(chunk)
        upload.seek(0)
    fingerprint = digest.hexdigest()
    paths = []
    try:
        with transaction.atomic():
            # Khóa người tạo để hai request lặp trỏ khác dòng vẫn tuần tự.
            get_user_model().objects.select_for_update().get(pk=user.pk)
            row = waybill_service.row_for(user, row_id, lock=True)
            replay = PaymentDocument.objects.filter(created_by=user, operation=operation).first()
            if replay:
                if replay.fingerprint != fingerprint:
                    raise BusinessError('Mã lượt tạo đã được dùng cho nội dung khác.', code='conflict')
                return document_for(user, replay.pk, include_deleted=True)
            unique_ref(row, values['reference'])
            document = PaymentDocument.objects.create(record=row, created_by=user, updated_by=user,
                operation=operation, fingerprint=fingerprint, **values)
            save_files(document, files, user, paths)
            changed(row, document, user, AuditAction.CREATE,
                    image_ids=document.images.values_list('pk', flat=True))
            return document
    except Exception:
        for path in paths:
            path.unlink(missing_ok=True)
        raise


def update(user, pk, version, action, *, reference='', transfer_date='', note='', uploads=(), remove=()):
    if not can_manage(user):
        raise OutOfScopeError()
    initial = document_for(user, pk, include_deleted=True)
    files = validated_files(uploads, required=False)
    paths = []
    try:
        with transaction.atomic():
            row = waybill_service.row_for(user, initial.record_id, lock=True)
            document = PaymentDocument.objects.select_for_update().get(pk=pk)
            if str(version) != str(document.version):
                raise BusinessError('Chứng từ đã thay đổi. Mở lại để đối chiếu.', code='conflict')
            if action == 'delete' and document.deleted_at is None:
                document.deleted_at = timezone.now()
                document.deleted_by = user
            elif action == 'restore' and document.deleted_at is not None:
                unique_ref(row, document.reference, exclude=pk)
                document.deleted_at = None
                document.deleted_by = None
            elif action == 'edit' and document.deleted_at is None:
                values = fields(reference, transfer_date, note)
                unique_ref(row, values['reference'], exclude=pk)
                images = document.images.filter(deleted_at__isnull=True)
                remove = {int(value) for value in remove}
                if len(remove) != images.filter(pk__in=remove).count():
                    raise BusinessError('Ảnh cần gỡ không thuộc chứng từ.')
                if images.exclude(pk__in=remove).count() + len(files) < 1:
                    raise BusinessError('Chứng từ cần giữ ít nhất một ảnh.')
                images.filter(pk__in=remove).update(deleted_at=timezone.now(), deleted_by=user)
                for key, value in values.items():
                    setattr(document, key, value)
                save_files(document, files, user, paths)
            else:
                raise BusinessError('Thao tác không hợp lệ với trạng thái chứng từ.')
            document.version += 1
            document.updated_by = user
            document.save()
            changed(row, document, user, AuditAction.UPDATE, mutation=action,
                    image_ids=document.images.values_list('pk', flat=True))
            return document
    except Exception:
        for path in paths:
            path.unlink(missing_ok=True)
        raise


def image_for(user, pk):
    image = PaymentImage.objects.filter(pk=pk, deleted_at__isnull=True).first()
    if image is None:
        raise OutOfScopeError()
    document_for(user, image.document_id)
    root = (Path(settings.STORAGE_DIR) / SUBDIR).resolve()
    path = (Path(settings.STORAGE_DIR) / image.file_path).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise BusinessError('Không tìm thấy tệp ảnh. Liên hệ quản trị viên.')
    return image, path
