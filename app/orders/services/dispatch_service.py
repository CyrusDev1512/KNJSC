"""Ghi đơn hàng sang bảng vận đơn — FR-6.3, FR-6.4.

**Một chiều, không bao giờ ghi ngược.** Đơn hàng là nguồn; bảng vận đơn nhận
bản sao rồi bộ phận Vận đơn tự cập nhật trạng thái trên đó (backlog Q26). Cho
ghi ngược là mất luôn ranh giới nguồn dữ liệu — đúng thứ `kien-truc.md` cấm.

**Một đơn sinh đúng một dòng** — AC-6.3. Đơn nhiều sản phẩm thì cột Sản phẩm
gộp tên, Số lượng cộng lại, Giá tiền là tổng. Chi tiết từng dòng vẫn nằm trên
đơn hàng, không mất.
"""
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from core.audit import record
from core.constants import AuditAction
from core.exceptions import BusinessError
from core.identity import employee_code
from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, TableDef
from forms_builder.services import record_service

from ..constants import (
    WAYBILL_DEPARTMENT_CODE, WAYBILL_TABLE_CODE, Market, PaymentMethod,
    PaymentStatus, ShippingStatus,
)
from . import waybill_service

#: Cấu trúc của bảng vận đơn duy nhất "Vận đơn mới" (ADR-036, 18.09.2026).
#:
#: 25 cột chuẩn theo `waybill_service.COLUMNS` (profile Vận đơn: chi tiết sản phẩm, phân
#: công, tiền theo quốc gia) đứng trước; chín cột giữ từ tệp thật và backlog Q24 đứng sau —
#: Đối soát kế toán, Danh sách đen, Mua lại lần… vẫn có dữ liệu và vẫn dùng. Cột số lượng
#: theo sản phẩm (`sl_*`) do `sync_product_columns` sinh (AC-11.8).
#:
#: Khai ở một chỗ duy nhất (quy tắc 7).
EXTRA_COLUMNS = [
    ("Danh sách đen", "black_list", FieldType.TEXT, ""),
    ("Đối soát kế toán", "doi_soat", FieldType.CHOICE, ""),
    ("Mua lại lần", "mua_lai", FieldType.INTEGER, ""),
    ("Nhân viên vận đơn", "nv_van_don", FieldType.CHOICE, ""),
    ("MKT", "mkt", FieldType.TEXT, ""),
    ("Tên người chuyển tiền", "nguoi_chuyen_tien", FieldType.TEXT, ""),
    ("Đơn vị phụ", "don_vi_phu", FieldType.TEXT, ""),
    ("Facebook", "facebook", FieldType.TEXT, ""),
    ("Email", "email", FieldType.TEXT, ""),
]
WAYBILL_COLUMNS = list(waybill_service.COLUMNS) + EXTRA_COLUMNS

#: Tiền tố tên kỹ thuật của cột số lượng theo sản phẩm
PRODUCT_COLUMN_PREFIX = "sl_"


def product_column_code(product):
    """Tên kỹ thuật cột số lượng của một sản phẩm: `sl_` + mã sản phẩm."""
    return (PRODUCT_COLUMN_PREFIX + product.code.replace("-", "_"))[:60]


def is_product_column(code):
    return code.startswith(PRODUCT_COLUMN_PREFIX)


def product_columns():
    """`(tên, mã cột, sản phẩm)` cho mọi sản phẩm đang bán — mỗi sản phẩm một
    cột như tệp thật (Q39)."""
    from ..models import Product

    return [
        (sp.name, product_column_code(sp), sp)
        for sp in Product.objects.filter(is_active=True).order_by("name", "id")
    ]


def waybill_table():
    """Bảng vận đơn đang dùng. Chưa có thì báo lỗi rõ ràng, không trả None."""
    bang = TableDef.all_objects.filter(code=WAYBILL_TABLE_CODE).first()
    if bang is None:
        raise BusinessError(
            "Chưa có bảng vận đơn. Chạy lệnh `manage.py tao_bang_van_don` "
            "hoặc tạo bảng có tên kỹ thuật " + WAYBILL_TABLE_CODE
        )
    return bang


@transaction.atomic
def ensure_waybill_table(*, actor=None):
    """Tạo bảng vận đơn duy nhất "Vận đơn mới" (`van_don`) theo cấu trúc chuẩn, nếu chưa có;
    có rồi thì nâng cấp tại chỗ (ADR-036): bổ sung cột thiếu, đổi cột chữ thành danh sách
    chuẩn, gắn profile Vận đơn (`workflow="waybill"`), bảng dùng chung, cột khoá Mã đơn,
    cột số lượng theo sản phẩm. Gọi được nhiều lần, không đụng cột đã có, không sửa dữ liệu.
    """
    from org.models import Department

    bo_phan = Department.objects.select_for_update().filter(code=WAYBILL_DEPARTMENT_CODE).first()
    if bo_phan is None:
        raise BusinessError(
            f"Chưa có bộ phận với tên kỹ thuật {WAYBILL_DEPARTMENT_CODE}."
        )

    bang = TableDef.all_objects.select_for_update().filter(code=WAYBILL_TABLE_CODE).first()
    if bang is None:
        bang = TableDef.objects.create(
            name="Vận đơn mới", code=WAYBILL_TABLE_CODE,
            description="Bảng vận đơn duy nhất: nhận bản sao từ đơn hàng, bộ phận Vận đơn vận hành trên đó.",
            department=bo_phan, created_by=actor,
            # Hàng đợi việc chung: cả bộ phận Vận đơn thấy và sửa được mọi dòng (ADR-033).
            is_shared=True, workflow="waybill",
        )
        record(AuditAction.CREATE, actor=actor, target=bang, detail="Tạo bảng Vận đơn mới (ADR-036)")

    da_co = set(bang.columns.values_list("code", flat=True))
    for i, (ten, ma, kieu, nhan) in enumerate(WAYBILL_COLUMNS):
        if ma in da_co:
            continue
        ColumnDef.objects.create(
            table=bang, name=ten, code=ma, field_type=kieu, meaning=nhan, order=i,
            is_key=ma == "ma_don",
            options=list(waybill_service.OPTIONS.get(ma, [])),
        )
    waybill_service.upgrade_schema(bang, actor=actor)
    sync_product_columns(bang)
    # Mã đơn là cột khoá của bảng vận đơn — bấm ô Mã đơn trên Bảng tính là lọc
    # ra đúng đơn đó (ADR-010). Chỉ đặt khi bảng chưa có cột khoá nào.
    if not bang.columns.filter(is_key=True).exists():
        bang.columns.filter(code="ma_don").update(is_key=True)
    fields = []
    if bang.name in ("Bảng vận đơn", "Vận đơn"):
        bang.name = "Vận đơn mới"; fields.append("name")
    if bang.workflow != "waybill":
        bang.workflow = "waybill"; fields.append("workflow")
        bang.delivery_view_version += 1; fields.append("delivery_view_version")
    if not bang.is_shared:
        bang.is_shared = True; fields.append("is_shared")
    if fields:
        bang.save(update_fields=fields + ["updated_at"])
        record(AuditAction.UPDATE, actor=actor, target=bang,
               detail="Vận đơn mới là bảng vận đơn duy nhất (ADR-036): " + ", ".join(fields))
    bang.refresh_from_db()
    return bang


def sync_product_columns(bang=None):
    """Mỗi sản phẩm đang bán có một cột số lượng trên bảng vận đơn — AC-11.8.

    Gọi lại được: sản phẩm mới → cột mới; cột đã có thì đổi tên theo tên sản
    phẩm. Không xoá cột của sản phẩm ngừng bán — dữ liệu cũ vẫn phải xem được.
    """
    bang = bang or waybill_table()
    theo_ma = {c.code: c for c in bang.columns.all()}
    thu_tu = len(WAYBILL_COLUMNS) + 100
    them = 0
    # Nhóm cột sản phẩm đang bị ẩn với cả công ty (ADR-039) thì sản phẩm mới
    # cũng vào ở trạng thái ẩn — thêm hàng không làm cả nhóm hiện trở lại.
    cu = [c for c in theo_ma.values() if is_product_column(c.code)]
    an_ca_nhom = bool(cu) and all(c.is_hidden for c in cu)
    for i, (ten, ma, _) in enumerate(product_columns()):
        cot = theo_ma.get(ma)
        if cot is None:
            ColumnDef.objects.create(
                table=bang, name=ten, code=ma, field_type=FieldType.INTEGER,
                order=thu_tu + i, is_hidden=an_ca_nhom,
            )
            them += 1
        elif cot.name != ten:
            cot.name = ten
            cot.save(update_fields=["name", "updated_at"])
    return them


def _tom_tat_san_pham(order, lines=None):
    """Gộp các dòng sản phẩm thành một ô — AC-6.3 đòi đúng một dòng."""
    lines = lines if lines is not None else list(order.lines.select_related("product"))
    if not lines:
        return "", 0, Decimal("0.00")
    ten = " + ".join(f"{d.product.name} ×{d.quantity}" for d in lines)
    so_luong = sum(d.quantity for d in lines)
    tong = sum((d.line_total for d in lines), Decimal("0.00"))
    return ten, so_luong, tong


def build_values(order, lines=None):
    """Dựng dict giá trị để ghi sang bảng vận đơn.

    Tách riêng khỏi `push` để kiểm thử đối chiếu được từng ô mà không cần
    chạm vào cơ sở dữ liệu.
    """
    lines = lines if lines is not None else list(order.lines.select_related("product"))
    ten_sp, so_luong, tong = _tom_tat_san_pham(order, lines)
    khach = order.customer
    nguoi_ban = order.seller or order.created_by
    # Mỗi sản phẩm một cột số lượng — AC-11.8
    theo_san_pham = {}
    for d in lines:
        ma = product_column_code(d.product)
        theo_san_pham[ma] = theo_san_pham.get(ma, 0) + d.quantity
    return {
        **theo_san_pham,
        "dia_chi": order.address_line,
        "mua_lai": _lan_mua(order),
        "mkt": "",
        "nguoi_chuyen_tien": "",
        "nv_van_don": None,
        "doi_soat": None,
        "ma_don": order.code,
        "ngay": timezone.localdate(order.created_at).isoformat(),
        "ten_khach": khach.name,
        "so_dien_thoai": khach.phone,
        "san_pham": ten_sp,
        "quoc_gia": Market(order.market).label,
        "bang": order.state,
        "thanh_pho": order.city,
        "zipcode": order.zipcode,
        "so_luong": so_luong,
        "gia_tien": str(tong),
        "loai_tien": order.currency,
        "pttt": PaymentMethod(order.payment_method).label,
        "nguoi_ban": employee_code(nguoi_ban),
        "don_vi_phu": order.sub_unit,
        "facebook": khach.facebook,
        "email": khach.email,
        "trang_thai_vc": ShippingStatus.DA_LEN_DON.label,
        "trang_thai_tt": PaymentStatus.UNPAID.label,
        "black_list": khach.blacklist_reason if khach.is_blacklisted else "",
        "ghi_chu": order.note,
    }


def _lan_mua(order):
    """Khách mua lần thứ mấy — FR-6.7, cột "Mua lại lần ?" của tệp thật.
    Lần đầu là 1. Đếm đơn của cùng khách tới thời điểm này."""
    from ..models import Order

    if not getattr(order, "customer_id", None):
        return 1
    ds = Order.objects.filter(customer_id=order.customer_id)
    if order.pk:
        ds = ds.filter(pk__lte=order.pk)
    return max(ds.count(), 1)


def push(order, *, actor=None, request=None, lines=None):
    """Ghi một đơn sang bảng vận đơn. Trả về dòng vừa sinh.

    Gọi **bên trong** giao dịch của `order_service.create_order`. Hàm này ném
    lỗi thì cả đơn hàng cũng không được lưu — AC-6.5.
    """
    DETAIL_CODE = waybill_service.DETAIL_CODE
    bang = waybill_table()
    lines = list(lines if lines is not None else order.lines.select_related("product"))
    values = build_values(order, lines)
    values["ngay"] = timezone.localdate(order.created_at).isoformat()
    values[DETAIL_CODE] = [{"product": line.product.code, "quantity": line.quantity, "unit": line.unit,
                           "unit_price": str(line.unit_price), "paid_amount": "0.00"} for line in lines]
    return record_service.create_record(
        bang, values, actor=actor, request=request,
    )
