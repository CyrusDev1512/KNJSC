"""Danh sách chọn của cột: ai thêm được, thêm thế nào, và lấy danh sách để vẽ
ô chọn — FR-8.7, Q58.

Tầng dịch vụ (điều cấm 2): đường dẫn "Thêm mới…" trên biểu mẫu, trên ô bảng
và bất kỳ chỗ nào sau này đều gọi vào đây. Việc *phân giải* danh sách nằm ở
`forms_builder.choice_registry`; tệp này chỉ thêm phần quyền, phần ghi và
phần dọn dữ liệu cho giao diện.
"""
from django.db import transaction

from core.exceptions import BusinessError

from .. import choice_registry
from ..meaning import FieldType, Meaning
from ..models import CHOICE_OPTION_MAX_LENGTH
from . import grant_service, table_service


def can_manage_options(user, table):
    """Ai thêm được giá trị vào danh sách chọn của bảng: Admin, hoặc quản lý
    (Leader, Manager — ADR-014) của bộ phận sở hữu bảng — cùng luật với thư mục (ADR-010). Người được cấp
    quyền Sửa vẫn chỉ chọn, vì danh sách là chuyện của Manager (Q58)."""
    return grant_service.can_manage_folders(user, table.department_id)


def options_for(column):
    """Danh sách chọn áp cho cột, hoặc None nếu cột nhận mọi giá trị."""
    return choice_registry.for_column(column)


def items(choice_list):
    """`[(giá trị, nhãn)]` để vẽ từng `<option>`. Giá trị lưu chính là nhãn."""
    if choice_list is None:
        return []
    return [(nhan, nhan) for nhan in choice_list.options()]


def seller_options(column):
    """Người đang làm ở bộ phận sở hữu bảng, theo đúng luật danh tính
    (họ tên, không có thì tên đăng nhập) — để ô Người bán gợi ý đúng chuỗi mà
    báo cáo tổng hợp nhóm theo."""
    from org.models import UserProfile

    ds = (UserProfile.objects
          .filter(department_id=column.table.department_id, user__is_active=True)
          .order_by("full_name", "user__username")
          .values_list("full_name", "user__username"))
    ten = [(ho_ten or "").strip() or ten_dn for ho_ten, ten_dn in ds]
    return sorted(set(ten), key=str.casefold)


def register_sources():
    """Đăng ký nguồn danh sách mà chính `forms_builder` biết — gọi lúc khởi động app."""
    choice_registry.register_meaning(Meaning.SELLER, seller_options, strict=False)


@transaction.atomic
def add_option(column, label, *, actor=None, request=None):
    """Thêm một giá trị vào danh sách chọn của cột, trả về nhãn chuẩn.

    Đã có thì trả nhãn có sẵn và không ghi gì. Nguồn theo nhãn ý nghĩa có hàm
    `add` (sản phẩm) thì gọi hàm đó; danh sách trên cột thì ghi vào
    `ColumnDef.options` qua `table_service` để có nhật ký và kiểm hợp lệ.
    """
    nhan = " ".join(str(label or "").split())
    if not nhan:
        raise BusinessError("Giá trị mới không được để trống.")
    if len(nhan) > CHOICE_OPTION_MAX_LENGTH:
        raise BusinessError(f"Giá trị mới tối đa {CHOICE_OPTION_MAX_LENGTH} ký tự.")
    if column.field_type != FieldType.CHOICE:
        raise BusinessError(f'Cột "{column.name}" không phải kiểu Chọn một.')

    ds = choice_registry.for_column(column)
    co_san = choice_registry.find(ds, nhan)
    if co_san is not None:
        return co_san
    if ds.add is not None:
        return ds.add(nhan, actor=actor, request=request)
    if ds.source == choice_registry.SOURCE_COLUMN:
        table_service.update_column(
            column, {"options": [*(column.options or []), nhan]},
            actor=actor, request=request,
        )
        return nhan
    raise BusinessError(
        f'Danh sách của cột "{column.name}" do hệ thống quản lý, không thêm tại đây.'
    )


def attach_lists(columns, *, user, table):
    """Gắn danh sách chọn lên từng cột để template chỉ in ra: `la_chon` (là cột
    Chọn một), `cac_muc` (các mục), `chat` (chặt hay gợi ý), `co_them` (được thêm mới).

    Mỗi nguồn hệ thống tốn một truy vấn; danh sách trên cột không tốn gì.
    Cột không phải Chọn một thì `cac_muc` là None.
    """
    duoc_them = can_manage_options(user, table)
    for cot in columns:
        cot.la_chon = cot.field_type == FieldType.CHOICE
        if not cot.la_chon:
            cot.cac_muc, cot.chat, cot.co_them = None, True, False
            continue
        ds = choice_registry.for_column(cot)
        cot.cac_muc = items(ds)
        cot.chat = ds.strict
        cot.co_them = duoc_them and ds.can_add
    return columns
