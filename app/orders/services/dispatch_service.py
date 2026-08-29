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

from core.exceptions import BusinessError
from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, TableDef
from forms_builder.services import record_service

from ..constants import (
    WAYBILL_DEPARTMENT_CODE, WAYBILL_TABLE_CODE, Market, PaymentMethod,
    PaymentStatus, ShippingStatus,
)

#: Cấu trúc chuẩn của bảng vận đơn.
#:
#: Tám cột đầu lấy đúng theo tệp thật của khách hàng. Sáu cột đánh dấu (+) là
#: phần thêm, chốt ở backlog Q24 — bộ phận Vận đơn cần liên lạc được với khách
#: khi giao hỏng, và cần biết đơn của người bán nào để hỏi lại.
#:
#: Khai ở một chỗ duy nhất (quy tắc 7).
WAYBILL_COLUMNS = [
    # (nhãn, tên kỹ thuật, kiểu, nhãn ý nghĩa)
    ("Mã đơn", "ma_don", FieldType.TEXT, ""),
    ("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
    ("Tên khách", "ten_khach", FieldType.TEXT, Meaning.CUSTOMER),
    ("Số điện thoại", "so_dien_thoai", FieldType.TEXT, Meaning.PHONE),
    ("Sản phẩm", "san_pham", FieldType.TEXT, Meaning.PRODUCT),
    ("Quốc gia", "quoc_gia", FieldType.CHOICE, ""),                    # +
    ("Bang", "bang", FieldType.TEXT, ""),
    ("Thành phố", "thanh_pho", FieldType.TEXT, ""),
    ("Mã bưu chính", "zipcode", FieldType.TEXT, ""),
    ("Số lượng", "so_luong", FieldType.INTEGER, ""),
    ("Giá tiền", "gia_tien", FieldType.MONEY, Meaning.REVENUE),
    ("Loại tiền tệ", "loai_tien", FieldType.TEXT, ""),                 # +
    ("Phương thức thanh toán", "pttt", FieldType.TEXT, ""),
    ("Người bán", "nguoi_ban", FieldType.TEXT, Meaning.SELLER),        # +
    ("Đơn vị phụ", "don_vi_phu", FieldType.TEXT, ""),                  # +
    ("Facebook", "facebook", FieldType.TEXT, ""),                      # +
    ("Email", "email", FieldType.TEXT, ""),                            # +
    ("Trạng thái vận chuyển", "trang_thai_vc", FieldType.CHOICE, Meaning.STATUS),
    ("Ngày thanh toán", "ngay_tt", FieldType.DATE, ""),
    ("Trạng thái thanh toán", "trang_thai_tt", FieldType.CHOICE, ""),
    ("Số tiền thanh toán", "so_tien_tt", FieldType.MONEY, ""),
    ("Bill", "bill", FieldType.TEXT, ""),
    ("Danh sách đen", "black_list", FieldType.TEXT, ""),
    ("Ghi chú", "ghi_chu", FieldType.LONG_TEXT, ""),
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
    """Tạo bảng vận đơn theo đúng cấu trúc chuẩn, nếu chưa có.

    Gọi được nhiều lần: đã có thì bổ sung cột còn thiếu, không đụng cột đã có.
    """
    from org.models import Department

    bo_phan = Department.objects.filter(code=WAYBILL_DEPARTMENT_CODE).first()
    if bo_phan is None:
        raise BusinessError(
            f"Chưa có bộ phận với tên kỹ thuật {WAYBILL_DEPARTMENT_CODE}."
        )

    bang = TableDef.all_objects.filter(code=WAYBILL_TABLE_CODE).first()
    if bang is None:
        bang = TableDef.objects.create(
            name="Bảng vận đơn", code=WAYBILL_TABLE_CODE,
            description="Nhận bản sao từ đơn hàng. Không ghi ngược về đơn.",
            department=bo_phan, created_by=actor,
            # Hàng đợi việc chung: cả bộ phận Vận đơn thấy và sửa được mọi
            # dòng. Để phạm vi theo cấp bậc thì nhân viên Vận đơn thấy rỗng,
            # vì dòng do bên Sale tạo ra
            is_shared=True,
        )
    elif not bang.is_shared:
        bang.is_shared = True
        bang.save(update_fields=["is_shared", "updated_at"])

    da_co = set(bang.columns.values_list("code", flat=True))
    for i, (ten, ma, kieu, nhan) in enumerate(WAYBILL_COLUMNS):
        if ma in da_co:
            continue
        ColumnDef.objects.create(
            table=bang, name=ten, code=ma, field_type=kieu, meaning=nhan, order=i,
        )
    return bang


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
    ten_sp, so_luong, tong = _tom_tat_san_pham(order, lines)
    khach = order.customer
    nguoi_ban = order.seller or order.created_by
    return {
        "ma_don": order.code,
        "ngay": order.created_at.date().isoformat(),
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
        "nguoi_ban": getattr(getattr(nguoi_ban, "profile", None), "full_name", "")
                     or getattr(nguoi_ban, "username", ""),
        "don_vi_phu": order.sub_unit,
        "facebook": khach.facebook,
        "email": khach.email,
        "trang_thai_vc": ShippingStatus.PENDING.label,
        "trang_thai_tt": PaymentStatus.UNPAID.label,
        "black_list": khach.blacklist_reason if khach.is_blacklisted else "",
        "ghi_chu": order.note,
    }


def push(order, *, actor=None, request=None, lines=None):
    """Ghi một đơn sang bảng vận đơn. Trả về dòng vừa sinh.

    Gọi **bên trong** giao dịch của `order_service.create_order`. Hàm này ném
    lỗi thì cả đơn hàng cũng không được lưu — AC-6.5.
    """
    bang = waybill_table()
    return record_service.create_record(
        bang, build_values(order, lines), actor=actor, request=request,
    )
