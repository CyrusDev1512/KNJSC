"""Phần tạo/hoàn tác dòng trong cùng giao dịch và biên nhận của lưới."""
from django.utils import timezone
from django.core.exceptions import ValidationError
from core.exceptions import BusinessError, OutOfScopeError
from forms_builder.models import DataRecord
from forms_builder.services import grant_service, record_service
from forms_builder import record_policies
from crm.models import GridMutationReceipt, GridCellHistory


def can_create(user, table):
    policy=record_policies.for_table(table)
    return not (policy and getattr(policy,'protect_table',False)) and grant_service.can_create_record(user,table)


def create(user, table, cells, columns):
    drafts={}
    for cell in cells:
        if cell['id']>=0:continue
        if cell.get('property','value')!='value' or cell['old'] not in (None,''):
            raise BusinessError('Dòng nháp chỉ nhận giá trị mới.')
        drafts.setdefault(cell['id'],{})[cell['column']]=cell['value']
    if drafts and not can_create(user,table):raise OutOfScopeError()
    allowed={c.code for c in columns if not c.is_computed}
    for values in drafts.values():
        if set(values)-allowed:raise BusinessError('Dòng nháp có cột không tồn tại hoặc cột tính toán.')
        if not any(v not in (None,'') for v in values.values()):raise BusinessError('Dòng trống chưa được lưu.')
    if not drafts:return {}
    # Lõi nhập kiểm kiểu/cột tính/tách giống nhau; outer transaction của save
    # biến các lô thành một lượt nguyên tử và trả ánh xạ ID chính xác.
    from core.constants import AuditAction
    created=[]
    result=record_service.create_records_bulk(table,list(drafts.values()),actor=user,columns=columns,
        row_numbers=list(drafts),on_created=created.extend,audit_action=AuditAction.CREATE)
    if result.errors:
        temporary,message=result.errors[0]
        values=drafts[temporary]
        column=result.error_columns.get(temporary) or next(iter(values))
        raise record_service.CellError(message,pk=temporary,code=column)
    return {str(temporary):row.pk for temporary,row in zip(drafts,created)}



def change(user, table, actions, receipt, *, replay=False):
    if not actions:return []
    if not can_create(user,table):raise OutOfScopeError()
    ids=[a.get('id') for a in actions if isinstance(a,dict)]
    if len(ids)!=len(actions) or any(type(pk)is not int or pk<=0 for pk in ids) or len(set(ids))!=len(ids):
        raise BusinessError('Định danh hoàn tác dòng không hợp lệ.')
    rows=list(DataRecord.all_objects.filter(table=table,pk__in=ids).select_related('table').select_for_update(of=('self',)).order_by('pk'))
    visible=set(DataRecord.all_objects.in_scope(user,table=table).filter(pk__in=ids).values_list('pk',flat=True))
    if visible!=set(ids):raise OutOfScopeError()
    by_id={r.pk:r for r in rows}
    for action in actions:
        row=by_id[action['id']]
        if not grant_service.can_edit_record(user,row):raise OutOfScopeError()
        try:
            source=GridMutationReceipt.objects.get(actor=user,table=table,operation=action.get('source'))
        except (GridMutationReceipt.DoesNotExist,ValueError,TypeError,ValidationError):raise BusinessError('Thiếu biên nhận tạo dòng.')
        if row.pk not in source.result.get('created_ids',[]):raise OutOfScopeError()
        if action.get('action') not in ('delete','restore'):raise BusinessError('Chỉ hoàn tác hoặc làm lại dòng đã tạo.')
        if replay:continue
        deleted=action['action']=='delete'
        if row.updated_at.isoformat()!=action.get('version') or (row.deleted_at is not None)==deleted:
            raise BusinessError('Dòng đã thay đổi. Không thể hoàn tác toàn lượt.',code='conflict')
        if GridCellHistory.objects.filter(record=row).exclude(receipt__actor=user).exists():
            raise BusinessError('Dòng đã được người khác sửa. Không thể hoàn tác toàn lượt.',code='conflict')
        before=row.deleted_at is not None
        row.deleted_at=timezone.now() if deleted else None
        row.deleted_by=user if deleted else None
        row.save(update_fields=['deleted_at','deleted_by','updated_at'],skip_sync=True)
        GridCellHistory.objects.create(record=row,receipt=receipt,column='__row__',property='value',before=before,after=deleted)
    return [{'id':r.pk,'version':r.updated_at.isoformat(),'deleted':r.deleted_at is not None} for r in rows]
