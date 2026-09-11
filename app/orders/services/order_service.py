"""Quy tắc lên đơn.

Tầng dịch vụ, không biết gì về HTTP (điều cấm 2).

**Lưu xong là khoá** — BR-3 và FR-6.6, giống hệt báo cáo hằng ngày. Nên tệp
này **không có hàm sửa đơn**; thiếu hàm là cách chặn chắc nhất. Lên nhầm thì
đánh dấu bỏ rồi lên lại, cả hai việc đều để lại dấu vết.

**Đơn và dòng vận đơn cùng một giao dịch** — AC-6.5. Ghi sang bảng vận đơn
hỏng thì đơn cũng không được lưu; không bao giờ có đơn mồ côi.
"""
from decimal import InvalidOperation

from django.db import OperationalError, connection, transaction
from django.db.models import DecimalField, Max
from django.db.models.functions import Cast, Substr
from django.utils import timezone

from core.audit import record
from core.constants import AuditAction, Currency, Rank
from core.permissions import has_rank
from core.exceptions import BusinessError
from core.money import parse_money

from ..constants import Market, PaymentMethod
from ..models import Customer, Order, OrderLine, Product
from ..units import resolve_unit
from . import dispatch_service


# Namespace riêng, ổn định giữa mọi worker; không dùng hash() của Python.
ORDER_CODE_LOCK_NAMESPACE = 0x4B4E4F52
ORDER_CODE_LOCK_TIMEOUT = "5s"


def _lock_order_code(prefix):
    """Giữ quyền cấp mã đến hết giao dịch đơn–Vận đơn, kể cả khi rollback."""
    if not connection.in_atomic_block:
        raise RuntimeError("Cấp mã đơn phải nằm trong giao dịch tạo đơn.")
    try:
        # Savepoint khôi phục giao dịch/cấu hình trước khi xử lý lỗi timeout.
        # Khóa lấy thành công vẫn sống đến cuối giao dịch ngoài cùng.
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_setting('lock_timeout')")
                previous_timeout = cursor.fetchone()[0]
                cursor.execute("SELECT set_config('lock_timeout', %s, true)",
                               [ORDER_CODE_LOCK_TIMEOUT])
                cursor.execute("SELECT pg_advisory_xact_lock(%s, %s)",
                               [ORDER_CODE_LOCK_NAMESPACE, int(prefix[3:7])])
                cursor.execute("SELECT set_config('lock_timeout', %s, true)",
                               [previous_timeout])
    except OperationalError as exc:
        if getattr(exc.__cause__, "sqlstate", None) != "55P03":
            raise
        raise BusinessError(
            "Hệ thống đang bận cấp mã đơn. Vui lòng thử lại.",
            code="order_code_busy",
        ) from exc


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

    Hậu tố tối thiểu bốn chữ số, tăng theo cùng tiền tố ngày–tháng, kể cả
    năm khác vì mã hiện không có năm. Đơn đã xoá mềm vẫn giữ chỗ.
    """
    hom_nay = timezone.localdate()
    dau = f"DH-{hom_nay:%d%m}-"
    _lock_order_code(dau)
    # Đọc sau câu lấy khóa, để READ COMMITTED thấy đơn vừa commit của người
    # trước. Sắp chuỗi sẽ chọn 9999 thay vì 10000; chỉ lấy hậu tố số hợp lệ.
    cuoi = (Order.all_objects.filter(code__startswith=dau,
                                    code__regex=rf"^{dau}[0-9]+$")
            .aggregate(last=Max(Cast(Substr("code", len(dau) + 1),
                                    DecimalField(max_digits=22, decimal_places=0))))["last"])
    so = int(cuoi) + 1 if cuoi is not None else 1
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

    # Mọi đường tạo đơn cùng thứ tự khóa, trước cả lần ghi khách hàng đầu.
    code = _sinh_ma_don()
    khach, moi = Customer.objects.get_or_create(
        phone=phone.strip(),
        defaults={"name": customer_name.strip(), "facebook": facebook, "email": email},
    )

    if seller is not None:
        from django.contrib.auth import get_user_model
        from django.db.models import Q
        if seller.pk != actor.pk and not has_rank(actor, Rank.ADMIN):
            raise BusinessError('Chỉ Admin được chọn Sale đứng đơn.')
        seller = get_user_model().objects.select_related('profile__department', 'profile__team').filter(
            pk=seller.pk, is_active=True, profile__department__code='sale',
            profile__department__is_active=True, profile__department__deleted_at__isnull=True).filter(
                Q(profile__locked_until__isnull=True) | Q(profile__locked_until__lte=timezone.now())).first()
        if seller is None:
            raise BusinessError('Sale phải đang hoạt động và thuộc bộ phận Sale.')
    ho_so = getattr(seller or actor, "profile", None)
    department = getattr(ho_so, "department", None)
    team = getattr(ho_so, "team", None)
    if seller is None and has_rank(actor, Rank.ADMIN) and (
            department is None or department.code != "sale"):
        # Admin tự đứng đơn thử: dùng Sale làm phạm vi nội bộ, không gán team giả.
        from org.models import Department
        department = Department.objects.filter(code="sale", is_active=True).first()
        team = None
        if department is None:
            raise BusinessError("Chưa có bộ phận Sale đang hoạt động để lưu đơn.")
    don = Order(
        code=code, customer=khach, market=market, state=state, city=city,
        zipcode=zipcode, address_line=address_line, payment_method=payment_method,
        currency=currency, seller=seller or actor, sub_unit=sub_unit, note=note,
        created_by=actor,
        department=department, team=team,
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
            order=don, product=sp, unit=resolve_unit(sp, d.get("unit") or sp.unit),
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
            f"Lên đơn {don.code} — {len(cac_dong)} dòng sản phẩm"
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
