"""Danh mục sản phẩm: thêm sản phẩm và cung cấp danh sách cho ô chọn — FR-6.8, Q61.

Tầng dịch vụ (điều cấm 2). Danh mục dùng chung cả công ty, không áp phạm vi
quyền; ai được *thêm* thì tầng view kiểm (Manager trở lên). Thêm sản phẩm là
phải có ngay cột số lượng `sl_<mã>` trên bảng vận đơn (AC-11.8), nên hàm ở
đây gọi luôn `dispatch_service.sync_product_columns`.
"""
from django.db import transaction
from django.utils.text import slugify

from core.audit import record
from core.constants import AuditAction
from core.exceptions import BusinessError
from forms_builder import choice_registry
from forms_builder.meaning import Meaning
from forms_builder.models import TableDef

from ..constants import WAYBILL_TABLE_CODE
from ..models import Product
from . import dispatch_service

#: Mã sản phẩm là SlugField 60 ký tự; chừa chỗ cho hậu tố "-2", "-3"…
CODE_BASE_MAX = 50
NAME_MAX = Product._meta.get_field("name").max_length


def unique_code(name):
    """Mã kỹ thuật sinh từ tên: bỏ dấu, chữ thường, gạch nối; trùng thì thêm số.

    `slugify` của Django bỏ hẳn chữ Đ (không tách được thành D + dấu), nên đổi
    tay trước — "Đèn ngủ" phải thành `den-ngu`, không phải `en-ngu`.
    """
    khong_dau = str(name).replace("Đ", "D").replace("đ", "d")
    goc = slugify(khong_dau)[:CODE_BASE_MAX].strip("-") or "sp"
    ma, so = goc, 1
    while Product.objects.filter(code=ma).exists():
        so += 1
        ma = f"{goc}-{so}"
    return ma


@transaction.atomic
def create_product(*, name, code="", group=None, unit="cái", actor=None, request=None):
    """Thêm một sản phẩm vào danh mục và sinh cột số lượng trên bảng vận đơn."""
    ten = " ".join(str(name or "").split())
    if not ten:
        raise BusinessError("Tên sản phẩm không được để trống.")
    if len(ten) > NAME_MAX:
        raise BusinessError(f"Tên sản phẩm tối đa {NAME_MAX} ký tự.")
    trung = Product.objects.filter(name__iexact=ten, is_active=True).first()
    if trung is not None:
        raise BusinessError(f'Sản phẩm "{trung.name}" đã có trong danh mục.')

    ma = (code or "").strip() or unique_code(ten)
    if Product.objects.filter(code=ma).exists():
        raise BusinessError(f'Mã sản phẩm "{ma}" đã có.')

    san_pham = Product.objects.create(name=ten, code=ma, group=group, unit=unit or "cái")
    # Bảng vận đơn là bảng động, máy sạch có thể chưa có (entrypoint tạo sau
    # migrate) — không có thì không đồng bộ, không phải lỗi
    if TableDef.all_objects.filter(code=WAYBILL_TABLE_CODE).exists():
        dispatch_service.sync_product_columns()

    record(
        AuditAction.CREATE, actor=actor, target=san_pham,
        detail=f"Thêm sản phẩm {ma} — {ten}", request=request,
    )
    return san_pham


def option_labels(column=None):
    """Tên các sản phẩm đang bán, theo thứ tự tên — danh sách của ô chọn Sản phẩm."""
    return list(
        Product.objects.filter(is_active=True).order_by("name").values_list("name", flat=True)
    )


def add_from_label(column, label, *, actor=None, request=None):
    """Hàm `add` cho sổ theo nhãn: "Thêm mới…" tại ô chọn Sản phẩm là thêm sản phẩm."""
    return create_product(name=label, actor=actor, request=request).name


def register_sources():
    """Đăng ký nguồn Sản phẩm vào sổ danh sách chọn — gọi lúc khởi động app."""
    choice_registry.register_meaning(
        Meaning.PRODUCT, option_labels, strict=True, add=add_from_label,
    )
