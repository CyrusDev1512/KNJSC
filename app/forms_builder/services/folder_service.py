"""Thư mục chứa bảng — ADR-010.

Thư mục chỉ để sắp xếp thanh bên Bảng tính: phẳng, thuộc một bộ phận, không
ảnh hưởng phạm vi quyền. Manager của bộ phận (hoặc Admin) tạo, đổi tên, xoá
mềm, và xếp bảng vào thư mục cùng bộ phận. Mọi thay đổi ghi nhật ký (BR-5).
"""
from django.core.exceptions import ValidationError
from django.db import transaction

from core.audit import record
from core.constants import AuditAction
from core.exceptions import BusinessError

from ..models import Folder, TableDef


def _kiem_ten(name, department, exclude_pk=None):
    ten = (name or "").strip()
    if not ten:
        raise BusinessError("Tên thư mục không được để trống.")
    if len(ten) > 120:
        raise BusinessError("Tên thư mục dài quá 120 ký tự.")
    trung = Folder.objects.filter(department=department, name=ten).exclude(pk=exclude_pk).exists()
    if trung:
        raise BusinessError(f'Bộ phận đã có thư mục "{ten}".')
    return ten


@transaction.atomic
def create_folder(*, name, department, actor=None, request=None):
    ten = _kiem_ten(name, department)
    thu_muc = Folder(name=ten, department=department, created_by=actor)
    try:
        thu_muc.full_clean()
    except ValidationError as loi:
        raise BusinessError("; ".join(m for ms in loi.message_dict.values() for m in ms))
    thu_muc.save()
    record(AuditAction.CREATE, actor=actor, target=thu_muc,
           detail=f"Tạo thư mục {ten} ({department.code})", request=request)
    return thu_muc


@transaction.atomic
def rename_folder(folder, name, *, actor=None, request=None):
    ten = _kiem_ten(name, folder.department, exclude_pk=folder.pk)
    if ten == folder.name:
        return folder
    cu = folder.name
    folder.name = ten
    folder.save(update_fields=["name", "updated_at"])
    record(AuditAction.UPDATE, actor=actor, target=folder,
           detail=f"Đổi tên thư mục {cu} → {ten}", request=request)
    return folder


@transaction.atomic
def delete_folder(folder, *, actor=None, request=None):
    """Xoá mềm thư mục; bảng bên trong về "không thư mục" (không xoá bảng)."""
    so_bang = TableDef.all_objects.filter(folder=folder).update(folder=None)
    folder.delete(by=actor)
    record(AuditAction.DELETE, actor=actor, target=folder,
           detail=f"Xoá thư mục {folder.name}, {so_bang} bảng về không thư mục", request=request)
    return so_bang


@transaction.atomic
def move_table(table, folder, *, actor=None, request=None):
    """Xếp bảng vào thư mục (`None` = bỏ ra ngoài). Thư mục phải cùng bộ phận với bảng."""
    if folder is not None and folder.department_id != table.department_id:
        raise BusinessError("Thư mục phải thuộc cùng bộ phận với bảng.")
    if table.folder_id == getattr(folder, "pk", None):
        return table
    cu = table.folder.name if table.folder_id else "không thư mục"
    table.folder = folder
    table.save(update_fields=["folder", "updated_at"])
    record(AuditAction.UPDATE, actor=actor, target=table,
           detail=f"Chuyển bảng {table.code}: {cu} → {folder.name if folder else 'không thư mục'}",
           request=request)
    return table


def tree(user):
    """Cây cho thanh bên: `[(thư mục hoặc None, [bảng...])]`, hai truy vấn.

    Bảng nào người này thấy (kể cả được cấp quyền từ bộ phận khác) mà thư mục
    của nó không nằm trong phạm vi thì xếp vào mục "không thư mục".
    """
    thu_muc = list(Folder.objects.in_scope(user).select_related("department"))
    bang = list(TableDef.objects.in_scope(user).select_related("department").order_by("name"))
    theo_pk = {t.pk: [] for t in thu_muc}
    khong = []
    for b in bang:
        if b.folder_id in theo_pk:
            theo_pk[b.folder_id].append(b)
        else:
            khong.append(b)
    ket_qua = [(t, theo_pk[t.pk]) for t in thu_muc]
    if khong or not ket_qua:
        ket_qua.append((None, khong))
    return ket_qua
