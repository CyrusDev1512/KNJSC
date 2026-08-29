"""Màn hình lên đơn và xem lại đơn.

**Không có view sửa đơn** — BR-3, FR-6.6. Thiếu đường dẫn là cách chặn chắc
nhất; gọi thẳng cũng không có gì để gọi.
"""
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.constants import Currency
from core.exceptions import BusinessError
from core.navigation import SALES_ONLY
from core.permissions import assert_departments
from core.pagination import PAGE_SIZES, page_size, paginate

from .constants import Market, PaymentMethod
from .models import Product
from .services import order_service


def _phan_trang(request, queryset, ten_don_vi="đơn"):
    trang = paginate(request, queryset)
    return {
        "page_obj": trang, "trang": trang,
        "moi_trang": page_size(request), "cac_co_trang": PAGE_SIZES,
        "ten_don_vi": ten_don_vi, "tham_so": "trang", "tham_so_co": "moi_trang",
    }


def _doc_cac_dong(request):
    """Đọc các dòng sản phẩm trên biểu mẫu.

    Ô nhập đặt tên `sp_0`, `sl_0`, `gia_0`... Dòng nào chưa chọn sản phẩm thì
    bỏ qua, để người dùng thêm sẵn ô trống mà vẫn gửi được.
    """
    cac_dong = []
    for i in range(20):
        ma_sp = request.POST.get(f"sp_{i}", "").strip()
        if not ma_sp:
            continue
        cac_dong.append({
            "product": ma_sp,
            "quantity": request.POST.get(f"sl_{i}", "1").strip() or "1",
            "unit_price": request.POST.get(f"gia_{i}", "0").strip() or "0",
        })
    return cac_dong


@login_required
def len_don(request):
    """Lên một đơn hàng mới — FR-6.1, FR-6.2, FR-6.3."""
    request.nav_current = "len_don"
    # Lên đơn là chức năng của Sale — ma trận kiểm chéo `docs/04` mục 3 ghi rõ
    # Vận đơn bị từ chối. Kiểm ở máy chủ, không chỉ ẩn mục trên thanh bên (P1)
    assert_departments(request.user, SALES_ONLY, request)

    du_lieu = request.POST if request.method == "POST" else {}
    loi = []
    nhac_khach = order_service.customer_notice(du_lieu.get("phone", ""))

    if request.method == "POST":
        try:
            don = order_service.create_order(
                phone=du_lieu.get("phone", ""),
                customer_name=du_lieu.get("customer_name", ""),
                facebook=du_lieu.get("facebook", ""),
                email=du_lieu.get("email", ""),
                market=du_lieu.get("market") or Market.US,
                state=du_lieu.get("state", ""),
                city=du_lieu.get("city", ""),
                zipcode=du_lieu.get("zipcode", ""),
                address_line=du_lieu.get("address_line", ""),
                payment_method=du_lieu.get("payment_method") or PaymentMethod.CARD,
                currency=du_lieu.get("currency") or Currency.USD,
                sub_unit=du_lieu.get("sub_unit", ""),
                note=du_lieu.get("note", ""),
                lines=_doc_cac_dong(request),
                actor=request.user, request=request,
            )
            messages.success(
                request,
                f"Đã lưu đơn {don.code} và ghi sang bảng vận đơn. Đơn đã khoá.",
            )
            return redirect("don_hang")
        except BusinessError as e:
            # AC-6.1: từ chối nhưng không mất dữ liệu đã nhập
            loi.append(str(e))

    return render(request, "orders/len_don.html", {
        "d": du_lieu, "loi": loi, "nhac_khach": nhac_khach,
        "cac_san_pham": Product.objects.filter(is_active=True).select_related("group"),
        "cac_thi_truong": Market.choices,
        "cac_pttt": PaymentMethod.choices,
        "cac_loai_tien": Currency.choices,
        "cac_dong": _doc_cac_dong(request) or [{}],
    })


@login_required
def kiem_khach(request):
    """Tra khách theo số điện thoại, trả về mảnh HTML cảnh báo — FR-6.7.

    Dùng bằng HTMX ngay khi gõ xong số điện thoại, để người lên đơn biết
    trước chứ không phải gửi rồi mới biết.
    """
    nhac = order_service.customer_notice(request.GET.get("phone", ""))
    return render(request, "orders/_nhac_khach.html", {"nhac_khach": nhac})


@login_required
def don_hang(request):
    """Danh sách đơn trong phạm vi quyền — FR-6.5."""
    request.nav_current = "don_hang"
    assert_departments(request.user, SALES_ONLY, request)

    ds = order_service.orders_of(request.user)
    tim = request.GET.get("tim", "").strip()
    if tim:
        ds = ds.filter(customer__phone__icontains=tim)
    thi_truong = request.GET.get("thi_truong", "")
    if thi_truong:
        ds = ds.filter(market=thi_truong)

    boi_canh = {"tim": tim, "thi_truong": thi_truong, "cac_thi_truong": Market.choices}
    boi_canh.update(_phan_trang(request, ds))
    return render(request, "orders/don_hang.html", boi_canh)


@login_required
def don_xem(request, code):
    """Xem lại một đơn đã lưu. Chỉ đọc — BR-3."""
    request.nav_current = "don_hang"
    don = get_object_or_404(
        order_service.orders_of(request.user).prefetch_related("lines__product"),
        code=code,
    )
    return render(request, "orders/don_xem.html", {
        "don": don,
        "cac_dong": list(don.lines.select_related("product")),
        "duoc_bo": don.created_by_id == request.user.pk,
    })


@login_required
@require_POST
def don_bo(request, code):
    """Bỏ một đơn đã lưu. Xoá mềm cả dòng trên bảng vận đơn (BR-4)."""
    don = get_object_or_404(order_service.orders_of(request.user), code=code)
    if don.created_by_id != request.user.pk:
        messages.error(request, "Chỉ người lên đơn mới bỏ được đơn của mình.")
        return redirect("don_hang")

    order_service.cancel_order(don, actor=request.user, request=request)
    messages.success(request, f"Đã bỏ đơn {code}. Dòng trên bảng vận đơn cũng đã gỡ.")
    return redirect("don_hang")
