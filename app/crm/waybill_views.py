"""Trang lên đơn riêng, chi tiết và thống kê vận đơn — ADR-018, ADR-019."""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from core.exceptions import BusinessError, OutOfScopeError
from core.navigation import SALES_ONLY
from core.permissions import assert_departments, in_departments
from forms_builder.models import TableDef
from forms_builder.services import grant_service
from orders.constants import ACTIVE_WAYBILL_TABLE_CODE
from orders.services import order_service, waybill_service, product_service
from .waybill_forms import WaybillOrderForm


def read_items(data):
    keys = ("product", "quantity", "unit_price", "paid_amount")
    arrays = [data.getlist(k) for k in keys]
    if not arrays[3]:
        arrays[3] = ["0"] * len(arrays[0])
    if len({len(a) for a in arrays}) != 1:
        raise BusinessError("Chi tiết sản phẩm thiếu ô. Hãy kiểm tra lại từng dòng.")
    return [dict(zip(keys, values)) for values in zip(*arrays)]


def item_context(items=None):
    return {"items": items or [{"quantity": 1, "paid_amount": "0.00"}],
            "products": product_service.entry_products()}


@login_required
@require_http_methods(["GET", "POST"])
def create_order(request):
    assert_departments(request.user, SALES_ONLY, request)
    form = WaybillOrderForm(request.POST if request.method == "POST" else None, actor=request.user)
    error, success, items = "", "", None
    if request.method == "POST":
        try:
            items = read_items(request.POST)
            waybill_service.validate_items(items)
            if form.is_valid():
                order = order_service.create_order(**form.cleaned_data, lines=items, actor=request.user, request=request)
                success = f"Đã lưu đơn {order.code} vào Vận đơn."
                form, items = WaybillOrderForm(actor=request.user), None
        except (BusinessError, ValidationError, ValueError) as exc:
            error = str(exc) if isinstance(exc, BusinessError) else "Kiểm tra lại thông tin đơn và chi tiết sản phẩm."
    context = {"form": form, "error": error, "success": success, **item_context(items),
               "ve_url": reverse("thu_muc"), "ve_nhan": "Về Bảng tính — thư mục"}
    template = "crm/_waybill_entry.html" if request.headers.get("HX-Request") else "crm/waybill_entry.html"
    response = render(request, template, context, status=400 if error or form.errors else 200)
    return response


@login_required
@require_http_methods(["GET", "POST"])
def detail(request, pk):
    row, stored = waybill_service.items_for(request.user, pk)
    editable = grant_service.can_edit_record(request.user, row)
    error = ""
    items = [{"product": i.product.code, "quantity": i.quantity,
              "unit_price": str(i.unit_price), "paid_amount": str(i.paid_amount)} for i in stored]
    if request.method == "POST":
        if not editable:
            raise OutOfScopeError()
        try:
            items = read_items(request.POST)
            waybill_service.update_items(request.user, pk, items, request.POST.get("version"), request=request)
            response = HttpResponse("Đã lưu chi tiết sản phẩm.")
            response["HX-Trigger"] = '{"waybillChanged":{"kind":"detail"}}'
            return response
        except BusinessError as exc:
            error = str(exc)
    return render(request, "crm/_waybill_detail.html", {
        "row": row, "editable": editable, "error": error, **item_context(items),
        "version": request.POST.get("version") if error else row.updated_at.isoformat(),
    }, status=400 if error else 200)


@login_required
def statistics(request):
    # Giữ liên kết cũ; kiểm quyền trước khi chuyển sang trang riêng.
    from .services.master_grid_service import table_for
    from django.shortcuts import redirect
    table_for(request.user, ACTIVE_WAYBILL_TABLE_CODE)
    suffix = ('?' + request.GET.urlencode()) if request.GET else ''
    return redirect(reverse('crm_statistics') + suffix)
