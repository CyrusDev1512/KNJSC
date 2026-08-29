"""Nối trường biểu mẫu với cột bảng, và kiểm khớp kiểu — FR-8.3, FR-8.6.

Tách riêng khỏi `form_service` vì đây là chỗ dễ sai nhất và cần đọc được một
mình: nối lệch kiểu thì dữ liệu người dùng gõ vào sẽ rơi vào cột không nhận
được nó, và lỗi chỉ lộ ra lúc nhập liệu — muộn hơn nhiều so với lúc nối.

Bảng tương thích khai ở `meaning.TYPE_COMPATIBLE`, một chỗ duy nhất (quy tắc 7).
"""
from django.core.exceptions import ValidationError
from django.db import transaction

from core.exceptions import BusinessError

from ..meaning import FieldType, type_fits
from ..models import FormTableLink


@transaction.atomic
def link_column(form_field, column):
    """Nối một trường vào một cột. `column=None` thì gỡ liên kết.

    Ném `ValidationError` với thông báo chỉ đúng trường bị lệch — AC-8.6 đòi
    "thông báo rõ ràng", không phải một câu chung chung.
    """
    cu = FormTableLink.objects.filter(form_field=form_field).first()

    if column is None:
        if cu is not None:
            cu.delete()
        return None

    lien_ket = cu or FormTableLink(form_field=form_field)
    lien_ket.column = column
    lien_ket.full_clean()
    lien_ket.save()
    return lien_ket


def check(field_def, column):
    """Trường này nối được vào cột kia không. Trả về câu giải thích, hoặc None.

    Dùng để hiện trạng thái "khớp / không khớp" trên giao diện mà không phải
    thử lưu rồi bắt lỗi.
    """
    if column.is_computed:
        return f"Cột {column.name} là cột tính sẵn, không nhận dữ liệu nhập tay."
    if not type_fits(field_def.field_type, column.field_type):
        return (
            f"Trường {field_def.name} kiểu {FieldType(field_def.field_type).label} "
            f"không ghi được vào cột {column.name} "
            f"kiểu {FieldType(column.field_type).label}."
        )
    return None


def summary(form, fields=None):
    """Tóm tắt tình trạng nối của cả biểu mẫu, cho khối thông báo trên giao diện.

    Trả về `(số trường đã nối, tổng số trường, danh sách câu lỗi)`.
    """
    fields = fields if fields is not None else list(form.ordered_fields())
    da_noi, loi = 0, []
    for truong in fields:
        lien_ket = getattr(truong, "link", None)
        if lien_ket is None:
            continue
        da_noi += 1
        cau = check(truong.field, lien_ket.column)
        if cau:
            loi.append(cau)
    return da_noi, len(fields), loi


@transaction.atomic
def recheck_links_of_field(field_def):
    """Kiểm lại mọi liên kết đang dùng một định nghĩa trường.

    Gọi sau khi đổi kiểu dữ liệu của trường đó. Còn liên kết nào lệch thì huỷ
    cả giao dịch — thà không cho đổi kiểu, còn hơn để biểu mẫu nhận dữ liệu rồi
    ghi vào cột sai kiểu.
    """
    hong = []
    ds = FormTableLink.objects.filter(
        form_field__field=field_def).select_related("column", "form_field__form")
    for lien_ket in ds:
        cau = check(field_def, lien_ket.column)
        if cau:
            hong.append(f"{lien_ket.form_field.form.name}: {cau}")

    if hong:
        raise BusinessError(
            "Đổi kiểu dữ liệu sẽ làm hỏng các liên kết đang có — "
            + " · ".join(hong)
        )
    return len(ds)


def validation_message(loi):
    """Rút câu tiếng Việt ra khỏi một `ValidationError` của liên kết.

    View dùng để hiện thông báo mà không phải biết cấu trúc lỗi của Django.
    """
    if isinstance(loi, ValidationError):
        if hasattr(loi, "error_dict"):
            return " · ".join(
                str(m) for ds in loi.message_dict.values() for m in ds
            )
        return " · ".join(str(m) for m in loi.messages)
    return str(loi)
