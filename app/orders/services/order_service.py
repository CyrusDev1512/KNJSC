"""Quy tắc lên đơn.

Tầng dịch vụ, không biết gì về HTTP (điều cấm 2).

**Lưu xong là khoá** — BR-3 và FR-6.6, giống hệt báo cáo hằng ngày. Nên tệp
này **không có hàm sửa đơn**; thiếu hàm là cách chặn chắc nhất. Lên nhầm thì
đánh dấu bỏ rồi lên lại, cả hai việc đều để lại dấu vết.

**Đơn và dòng vận đơn cùng một giao dịch** — AC-6.5. Ghi sang bảng vận đơn
hỏng thì đơn cũng không được lưu; không bao giờ có đơn mồ côi.
"""
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from core.audit import record
from core.constants import AuditAction, Currency
from core.exceptions import BusinessError
from core.money import parse_money

from ..constants import Market, PaymentMethod
from ..models import Customer, Order, OrderLine, Product
from . import dispatch_service


def find_customer(phone):
    """Tìm khách theo số điện thoại — FR-6.7. Không có thì trả None."""
    phone = (phone or "").strip()
    if not phone:
        return None
    return Customer.objects.filter(phone=phone).first()


def customer_notice(phone):
    """Lời nhắc về khách hàng, để hiện ngay lúc gõ số điện thoại.

    Trả về dict rỗng nếu là khách mới. Hai lời nhắc có thể cùng xuất hiện:
    khách mua lại (FR-6.7) và khách trong danh sách đen (backlog Q25).

    **Danh sách đen chỉ cảnh báo, không chặn.** Chưa có yêu cầu nào cho phép
    chặn, mà chặn nhầm thì mất đơn thật.
    """
    khach = find_customer(phone)
    if khach is None:
        return {}
    return {
        "customer": khach,
        "so_don_cu": khach.order_count(),
        "mua_lai": khach.order_count() > 0,
        "danh_sach_den": khach.is_blacklisted,
        "ly_do": khach.blacklist_reason,
    }


def _tien(gia_tri, ten_o):
    """Đổi chuỗi người dùng gõ sang Decimal — BR-8, không qua số thực."""
    try:
        return parse_money(gia_tri)
    except (InvalidOperation, TypeError, ValueError):
        raise BusinessError(f"Giá trị {gia_tri} ở ô {ten_o} không phải số tiền.")


def _sinh_ma_don():
    """Mã đơn dạng DH-2608-0047, đủ ngắn để đọc và gõ lại.

    Bốn số cuối đếm theo ngày, nên trong một ngày không trùng. Lấy số lớn
    nhất đang có thay vì đếm số bản ghi — đơn đã xoá vẫn giữ chỗ.
    """
    hom_nay = timezone.localdate()
    dau = f"DH-{hom_nay:%d%m}-"
    cuoi = (Order.all_objects.filter(code__startswith=dau)
            .order_by("-code").values_list("code", flat=True).first())
    so = int(cuoi.rsplit("-", 1)[1]) + 1 if cuoi else 1
    return f"{dau}{so:04d}"


@transaction.atomic
def create_order(*, phone, customer_name, lines, actor, request=None,
                 facebook="", email="", market=Market.US, state="", city="",
                 zipcode="", address_line="", payment_method=PaymentMethod.CARD,
                 currency=Currency.USD, seller=None, sub_unit="", note=""):
    """Lên một đơn hàng và ghi luôn sang bảng vận đơn.

    `lines` là danh sách dict `{"product": Product|mã, "quantity": int,
    "unit_price": str}`. Đơn phải có ít nhất một dòng — FR-6.1.
    """
    if not lines:
        raise BusinessError("Đơn hàng phải có ít nhất một dòng sản phẩm.")
    if not (phone or "").strip():
        raise BusinessError("Số điện thoại khách là bắt buộc.")
    if not (customer_name or "").strip():
        raise BusinessError("Tên khách là bắt buộc.")

    khach, moi = Customer.objects.get_or_create(
        phone=phone.strip(),
        defaults={"name": customer_name.strip(), "facebook": facebook, "email": email},
    )

    ho_so = getattr(actor, "profile", None)
    don = Order(
        code=_sinh_ma_don(), customer=khach, market=market, state=state, city=city,
        zipcode=zipcode, address_line=address_line, payment_method=payment_method,
        currency=currency, seller=seller or actor, sub_unit=sub_unit, note=note,
        created_by=actor,
        department=getattr(ho_so, "department", None),
        team=getattr(ho_so, "team", None),
    )
    if don.department_id is None:
        raise BusinessError("Tài khoản chưa gán bộ phận nên chưa lên đơn được.")
    don.full_clean(exclude=["created_by", "record", "total"])
    don.save()

    cac_dong = []
    for i, d in enumerate(lines, start=1):
        sp = d["product"]
        if not isinstance(sp, Product):
            sp = Product.objects.filter(code=sp, is_active=True).first()
            if sp is None:
                raise BusinessError(f"Dòng {i}: không tìm thấy sản phẩm {d['product']}.")
        dong = OrderLine(
            order=don, product=sp,
            quantity=int(d.get("quantity") or 1),
            unit_price=_tien(d.get("unit_price") or 0, f"đơn giá dòng {i}"),
        )
        dong.full_clean()
        dong.save()
        cac_dong.append(dong)

    don.recalculate_total()

    # Ghi sang bảng vận đơn trong cùng giao dịch. Bước này hỏng thì đơn ở trên
    # cũng bị huỷ theo — AC-6.5
    ban_ghi = dispatch_service.push(don, actor=actor, request=request, lines=cac_dong)
    don.record = ban_ghi
    don.save(update_fields=["record", "total", "updated_at"])

    record(
        AuditAction.CREATE, actor=actor, target=don,
        detail=(
            f"Lên đơn {don.code} — {khach.name} {khach.phone}, "
            f"{len(cac_dong)} dòng, tổng {don.total} {don.currency}"
        ),
        request=request,
    )
    return don


@transaction.atomic
def cancel_order(don, *, actor=None, request=None):
    """Bỏ một đơn đã lưu. Đánh dấu xoá, không xoá cứng (BR-4).

    Xoá mềm cả dòng trên bảng vận đơn đi kèm — quên là để lại dòng mồ côi mà
    bộ phận Vận đơn vẫn thấy và vẫn đi giao.
    """
    ma = don.code
    don.delete(by=actor)
    if don.record_id:
        don.record.delete(by=actor)
    record(
        AuditAction.DELETE, actor=actor, target=don,
        detail=f"Bỏ đơn {ma}", request=request,
    )
    return don


def orders_of(user):
    """Đơn trong phạm vi quyền — FR-6.5.

    Phạm vi do `ScopedManager` lo, không viết điều kiện lọc ở đây (quy tắc 11).
    """
    # Lấy sẵn cả hồ sơ nhân sự: màn hình hiện họ tên người bán, thiếu là mỗi
    # dòng thêm một lệnh truy vấn (quy tắc Q2)
    return (Order.objects.in_scope(user)
            .select_related(
                "customer", "department", "team",
                "created_by", "created_by__profile",
                "seller", "seller__profile",
            ))
