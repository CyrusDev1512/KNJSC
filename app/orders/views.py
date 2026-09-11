"""Màn hình lên đơn và xem lại đơn.

**Không có view sửa đơn** — BR-3, FR-6.6. Thiếu đường dẫn là cách chặn chắc
nhất; gọi thẳng cũng không có gì để gọi.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_GET

from core.constants import Rank
from core.exceptions import BusinessError
from core.navigation import SALES_ONLY
from core.permissions import assert_departments, assert_rank

from .models import Product
from .services import order_service, product_service


def _muc_san_pham():
    """`[(mã, tên)]` của sản phẩm đang bán, cho ô chọn trên màn hình Lên đơn."""
    return [
        (sp.code, sp.name)
        for sp in Product.objects.filter(is_active=True).order_by("name")
    ]


@login_required
@require_POST
def san_pham_moi(request):
    """Thêm sản phẩm ngay tại ô chọn trên màn hình Lên đơn — FR-6.8, Q61.

    Chỉ Manager trở lên của bộ phận Sale (màn hình này là của Sale). Trả về
    các `<option>` mới với sản phẩm vừa thêm được chọn sẵn.
    """
    assert_departments(request.user, SALES_ONLY, request)
    assert_rank(request.user, Rank.MANAGER, request)
    try:
        san_pham = product_service.create_product(
            name=request.POST.get("nhan_moi", ""), actor=request.user, request=request,
        )
    except BusinessError as loi:
        return HttpResponse(str(loi), status=400)
    if request.headers.get("Accept") == "application/json":
        return JsonResponse({"code": san_pham.code, "name": san_pham.name})
    return render(request, "components/o_chon_muc.html", {
        "cac_muc": _muc_san_pham(), "gia_tri": san_pham.code, "co_them": True,
        "nhan_trong": "— chọn sản phẩm —",
    })


@login_required
def kiem_khach(request):
    """Tra khách theo số điện thoại, trả về mảnh HTML cảnh báo — FR-6.7.

    Dùng bằng HTMX ngay khi gõ xong số điện thoại, để người lên đơn biết
    trước chứ không phải gửi rồi mới biết.
    """
    assert_departments(request.user, SALES_ONLY, request)
    nhac = order_service.customer_notice(request.GET.get("phone", ""))
    return render(request, "orders/_nhac_khach.html", {"nhac_khach": nhac})


@login_required
@require_GET
def don_xem(request, code):
    """Xem lại một đơn đã lưu. Chỉ đọc — BR-3."""
    request.nav_current = "waybill_create"
    don = get_object_or_404(
        order_service.orders_of(request.user).select_related("record"),
        code=code,
    )
    from forms_builder.models import DataRecord
    from django.urls import reverse
    row = DataRecord.objects.in_scope(request.user).filter(pk=don.record_id).select_related("table").first()
    return render(request, "orders/don_xem.html", {
        "van_don_url": reverse("bang_tinh_xem", args=[row.table.code]) if row else None,
        "don": don,
        "ve_url": "/thu-muc/", "ve_nhan": "Về Bảng tính — thư mục",
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
        return redirect("thu_muc")

    order_service.cancel_order(don, actor=request.user, request=request)
    messages.success(request, f"Đã bỏ đơn {code}. Dòng trên bảng vận đơn cũng đã gỡ.")
    return redirect("thu_muc")
