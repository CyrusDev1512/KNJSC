"""Trang lên đơn riêng, chi tiết và thống kê vận đơn — ADR-018, ADR-019."""
from core.permissions import assert_business_write
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from core.exceptions import BusinessError, OutOfScopeError
from core.navigation import SALES_ONLY
from core.permissions import assert_departments, has_rank
from forms_builder.services import grant_service
from orders.constants import ACTIVE_WAYBILL_TABLE_CODE
from orders.units import COMMON_UNITS
from orders.services import order_service, waybill_service, product_service
from core.submission import new_key as new_submission_key

from .services import catalog
from .waybill_forms import WaybillOrderForm


def read_items(data):
    keys = ("product", "quantity", "unit_price", "paid_amount")
    if "unit" in data:
        keys += ("unit",)
    arrays = [data.getlist(k) for k in keys]
    if not arrays[3]:
        arrays[3] = ["0"] * len(arrays[0])
    if len({len(a) for a in arrays}) != 1:
        raise BusinessError("Chi tiết sản phẩm thiếu ô. Hãy kiểm tra lại từng dòng.")
    return [dict(zip(keys, values)) for values in zip(*arrays)]


def require_products(items):
    """Hộp Chi tiết: dòng chưa chọn sản phẩm thì báo, không lặng lẽ bỏ qua — lỡ tay bấm Lưu với dòng trống
    không được làm mất chi tiết hay chữ ở ô Sản phẩm. Muốn đơn không còn sản phẩm thì Bỏ dòng hết rồi Lưu."""
    for number, item in enumerate(items, 1):
        if not item.get("product"):
            raise BusinessError(f"Dòng {number} chưa chọn sản phẩm. Chọn sản phẩm hoặc bấm Bỏ dòng.")
    return items


def item_context(items=None):
    products = product_service.entry_products()
    items = items or [{"quantity": 1, "paid_amount": "0.00"}]
    units = list(dict.fromkeys([*COMMON_UNITS, *(p["unit"] for p in products),
                               *(i.get("unit", "") for i in items)]))
    return {"items": items, "products": products, "units": [u for u in units if u]}


@login_required
@require_http_methods(["GET", "POST"])
def create_order(request):
    assert_business_write(request.user)
    assert_departments(request.user, SALES_ONLY, request)
    form = WaybillOrderForm(request.POST if request.method == "POST" else None, actor=request.user)
    error, success, items = "", "", None
    saved_order = None
    if request.method == "POST":
        try:
            items = read_items(request.POST)
            if not any(i.get("product") for i in items):
                raise BusinessError("Chọn ít nhất 1 sản phẩm cho đơn.")
            waybill_service.validate_items(items, strict_units=True)
            if form.is_valid():
                order, moi = order_service.create_order_once(
                    request.POST.get("ma_lan_nop"), **form.cleaned_data, lines=items, actor=request.user, request=request)
                saved_at = timezone.localtime(order.created_at)
                success = (f"Đã lưu đơn {order.code} vào {order.record.table.name} lúc {saved_at:%H:%M} ngày {saved_at:%d/%m/%Y}."
                           if moi else f"Đơn {order.code} đã lưu từ lần bấm trước lúc {saved_at:%H:%M}, không tạo đơn mới.")
                saved_order = order
                form, items = WaybillOrderForm(actor=request.user), None
        except (BusinessError, ValidationError, ValueError) as exc:
            error = str(exc) if isinstance(exc, BusinessError) else "Kiểm tra lại thông tin đơn và chi tiết sản phẩm."
    context = {"order_date": timezone.localtime(), "saved_order": saved_order,
               # Mã lần nộp dùng một lần (AC-6.11): lưu lỗi thì giữ mã để sửa rồi lưu lại vẫn là một đơn
               "ma_lan_nop": (request.POST.get("ma_lan_nop") if request.method == "POST" and not saved_order else "")
                             or new_submission_key(),
               "duoc_them_sp": has_rank(request.user, product_service.CREATE_RANK),
               "nhac_khach": order_service.customer_notice(
                   form.data.get("phone", ""), form.data.get("customer_name", "")),
               "form": form, "error": error, "success": success, **item_context(items),
               # Không có bảng vận đơn (Sale) thì thư mục 404 — ← về trang chủ KN CRM (AC-40.6)
               **({"ve_url": reverse("thu_muc"), "ve_nhan": "Về Bảng tính — thư mục"}
                  if catalog.co_bang_van_don(request.user)
                  else {"ve_url": reverse("tong_quan"), "ve_nhan": "Về trang chủ KN CRM"})}
    from orders.services.currency_service import MARKET_CURRENCIES
    context['market_currencies'] = MARKET_CURRENCIES
    template = "crm/_waybill_entry.html" if request.headers.get("HX-Request") else "crm/waybill_entry.html"
    response = render(request, template, context, status=400 if error or form.errors else 200)
    return response


@login_required
@require_http_methods(["GET", "POST"])
def detail(request, pk):
    row, stored = waybill_service.items_for(request.user, pk)
    editable = grant_service.can_edit_record(request.user, row)
    error = ""
    items = [{"product": i.product.code, "quantity": i.quantity, "unit": i.unit,
              "unit_price": str(i.unit_price), "paid_amount": str(i.paid_amount)} for i in stored]
    if request.method == "POST":
        if not editable:
            raise OutOfScopeError()
        try:
            items = read_items(request.POST)
            waybill_service.update_items(request.user, pk, require_products(items), request.POST.get("version"),
                                         request=request)
            response = HttpResponse("Đã lưu chi tiết sản phẩm.")
            response["HX-Trigger"] = '{"waybillChanged":{"kind":"detail"}}'
            return response
        except BusinessError as exc:
            error = str(exc)
    return render(request, "crm/_waybill_detail.html", {
        "original_order": order_service.orders_of(request.user).filter(record_id=row.pk).first(),
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
    separator = '&' if suffix else '?'
    return redirect(reverse('crm_statistics') + suffix + separator + 'nguon=van_don')


@login_required
@require_http_methods(["POST"])
def preview_order(request):
    """Tóm tắt nhập liệu, chỉ đọc; dùng chung kiểm tra và Decimal của vận đơn."""
    from django.http import JsonResponse
    from orders.services.currency_service import for_market
    assert_departments(request.user, SALES_ONLY, request)
    try:
        currency = for_market(request.POST.get('market'))
        items = waybill_service.validate_items(read_items(request.POST), strict_units=True)
        result = waybill_service.totals(items)
        return JsonResponse({'lines': len(items), 'quantity': result['so_luong'],
                             'total': result['gia_tien'], 'currency': currency})
    except BusinessError as exc:
        return JsonResponse({'error': str(exc)}, status=400)
