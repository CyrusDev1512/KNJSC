"""Quy tắc tạo và sửa biểu mẫu.

Tầng dịch vụ, không biết gì về HTTP (điều cấm 2). Mọi thao tác ghi đều ghi
nhật ký (BR-5) và nằm trong một giao dịch.

**Sửa biểu mẫu không làm mất dữ liệu đã nhập** — FR-8.5. Điều đó đúng vì dữ
liệu nằm trong `DataRecord.data`, khoá là tên kỹ thuật của **cột bảng**, không
phải của trường biểu mẫu. Thêm, bớt hay đổi thứ tự trường chỉ đổi cách nhập,
không đụng tới dữ liệu đã có. Đừng phá tính chất đó.
"""
from django.db import transaction

from core.audit import record
from core.constants import AuditAction

from ..models import FieldDef, FormDef, FormField
from . import link_service


@transaction.atomic
def create_form(*, name, code, department, table, description="",
                actor=None, request=None):
    """Tạo biểu mẫu mới, ghi vào một bảng có sẵn — FR-8.1, ADR-007."""
    bieu_mau = FormDef(
        name=name, code=code, department=department, table=table,
        description=description, created_by=actor,
    )
    bieu_mau.full_clean(exclude=["created_by"])
    bieu_mau.save()
    record(
        AuditAction.CREATE, actor=actor, target=bieu_mau,
        detail=f"Tạo biểu mẫu {code}, ghi vào bảng {table.code}", request=request,
    )
    return bieu_mau


@transaction.atomic
def update_form(form, changes, *, actor=None, request=None):
    """Sửa tên, mô tả hoặc trạng thái. Không đổi được tên kỹ thuật và bảng đích."""
    da_doi = []
    for ten in ("name", "description", "is_active"):
        if ten not in changes:
            continue
        cu, moi = getattr(form, ten), changes[ten]
        if cu == moi:
            continue
        da_doi.append(f"{form._meta.get_field(ten).verbose_name}: {cu} → {moi}")
        setattr(form, ten, moi)

    if not da_doi:
        return form

    form.full_clean(exclude=["created_by"])
    form.save()
    record(
        AuditAction.UPDATE, actor=actor, target=form,
        detail=f"Sửa biểu mẫu {form.code} — " + " · ".join(da_doi), request=request,
    )
    return form


# ══ THƯ VIỆN ĐỊNH NGHĨA TRƯỜNG ════════════════════════════════════

@transaction.atomic
def create_field_def(*, name, code, field_type, department, meaning="", hint="",
                     default_value="", actor=None, request=None):
    """Thêm một định nghĩa trường vào thư viện dùng chung của bộ phận."""
    truong = FieldDef(
        name=name, code=code, field_type=field_type, meaning=meaning,
        hint=hint, default_value=default_value, department=department,
    )
    truong.full_clean()
    truong.save()
    record(
        AuditAction.CREATE, actor=actor, target=truong,
        detail=f"Thêm định nghĩa trường {code} cho bộ phận {department}",
        request=request,
    )
    return truong


@transaction.atomic
def update_field_def(field_def, changes, *, actor=None, request=None):
    """Sửa một định nghĩa trường.

    Đổi kiểu dữ liệu có thể làm các liên kết đang có thành sai kiểu, nên phải
    kiểm lại toàn bộ chỗ đang dùng nó — không thì biểu mẫu vẫn nhận dữ liệu mà
    ghi vào cột sai kiểu.
    """
    da_doi, doi_kieu = [], False
    for ten in ("name", "field_type", "meaning", "hint", "default_value"):
        if ten not in changes:
            continue
        cu, moi = getattr(field_def, ten), changes[ten]
        if cu == moi:
            continue
        da_doi.append(f"{field_def._meta.get_field(ten).verbose_name}: {cu} → {moi}")
        setattr(field_def, ten, moi)
        if ten == "field_type":
            doi_kieu = True

    if not da_doi:
        return field_def

    field_def.full_clean()
    field_def.save()

    if doi_kieu:
        link_service.recheck_links_of_field(field_def)

    record(
        AuditAction.UPDATE, actor=actor, target=field_def,
        detail=f"Sửa định nghĩa trường {field_def.code} — " + " · ".join(da_doi),
        request=request,
    )
    return field_def


# ══ TRƯỜNG TRONG BIỂU MẪU ═════════════════════════════════════════

@transaction.atomic
def add_field(form, field_def, *, column=None, required=False, order=None,
              actor=None, request=None):
    """Đưa một trường vào biểu mẫu, và nối luôn vào cột đích nếu có chọn.

    Kiểm khớp kiểu chạy trong `link_service` — FR-8.6.
    """
    truong = FormField(
        form=form, field=field_def, required=required,
        order=order if order is not None else _thu_tu_ke_tiep(form),
    )
    truong.full_clean()
    truong.save()

    if column is not None:
        link_service.link_column(truong, column)

    record(
        AuditAction.CREATE, actor=actor, target=truong,
        detail=f"Thêm trường {field_def.code} vào biểu mẫu {form.code}",
        request=request,
    )
    return truong


@transaction.atomic
def update_field(form_field, changes, *, actor=None, request=None):
    """Sửa cờ bắt buộc, thứ tự, hoặc cột đích của một trường trong biểu mẫu."""
    da_doi = []
    for ten in ("required", "order"):
        if ten not in changes:
            continue
        cu, moi = getattr(form_field, ten), changes[ten]
        if cu == moi:
            continue
        da_doi.append(f"{form_field._meta.get_field(ten).verbose_name}: {cu} → {moi}")
        setattr(form_field, ten, moi)

    if da_doi:
        form_field.full_clean()
        form_field.save()

    if "column" in changes:
        cot_moi = changes["column"]
        cot_cu = getattr(getattr(form_field, "link", None), "column", None)
        if cot_cu != cot_moi:
            link_service.link_column(form_field, cot_moi)
            da_doi.append(f"Cột đích: {cot_cu or '—'} → {cot_moi or '—'}")

    if not da_doi:
        return form_field

    record(
        AuditAction.UPDATE, actor=actor, target=form_field,
        detail=f"Sửa trường {form_field} — " + " · ".join(da_doi), request=request,
    )
    return form_field


@transaction.atomic
def remove_field(form_field, *, actor=None, request=None):
    """Bỏ một trường khỏi biểu mẫu.

    Chỉ bỏ khỏi biểu mẫu, **không** đụng vào định nghĩa trường trong thư viện
    và cũng không đụng vào dữ liệu đã nhập — FR-8.5.
    """
    bieu_mau, ma = form_field.form, form_field.field.code
    form_field.delete()
    record(
        AuditAction.DELETE, actor=actor, target=bieu_mau,
        detail=f"Bỏ trường {ma} khỏi biểu mẫu {bieu_mau.code}", request=request,
    )
    return bieu_mau


@transaction.atomic
def reorder(form, ma_truong_theo_thu_tu, *, actor=None, request=None):
    """Sắp xếp lại thứ tự trường. Nhận danh sách khoá chính của `FormField`."""
    hien_co = {c.pk: c for c in form.fields.all()}
    for i, pk in enumerate(ma_truong_theo_thu_tu):
        truong = hien_co.get(int(pk))
        if truong is not None and truong.order != i:
            truong.order = i
            truong.save(update_fields=["order"])
    record(
        AuditAction.UPDATE, actor=actor, target=form,
        detail=f"Đổi thứ tự trường của biểu mẫu {form.code}", request=request,
    )
    return form


def _thu_tu_ke_tiep(form):
    cuoi = form.fields.order_by("-order").values_list("order", flat=True).first()
    return (cuoi or 0) + 1


def values_by_column(form, du_lieu_theo_truong, fields=None):
    """Đổi `{tên trường: giá trị}` sang `{tên cột: giá trị}` để ghi vào bảng.

    Trường chưa nối cột thì bỏ qua — nó chỉ hiện trên biểu mẫu, không chảy đi
    đâu cả.
    """
    fields = fields if fields is not None else list(form.ordered_fields())
    theo_cot = {}
    for truong in fields:
        lien_ket = getattr(truong, "link", None)
        if lien_ket is None:
            continue
        ma = truong.field.code
        if ma in du_lieu_theo_truong:
            theo_cot[lien_ket.column.code] = du_lieu_theo_truong[ma]
    return theo_cot


def missing_required(form, du_lieu_theo_truong, fields=None):
    """Tên các trường bắt buộc còn để trống — AC-8.2."""
    fields = fields if fields is not None else list(form.ordered_fields())
    return [
        t.field.name for t in fields
        if t.required and du_lieu_theo_truong.get(t.field.code) in (None, "")
    ]
