"""Thẻ và bộ lọc mẫu dùng chung — `{% load knjsc %}`.

Một luật hiển thị tên cho cả hệ thống (`core.identity`, Q59, ADR-037): template viết
`{{ u|ten }}` cho lời chào, `{{ u|ma }}` / `{{ u|ma_ten }}` cho chỗ cần định danh (mã
trước, tên sau) thay vì tự ghép `profile.full_name|default:username`, và `{% avatar u %}`
thay vì chép lại ô chữ cái đầu tên ở từng chỗ.
"""
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django import template
from django.utils.html import format_html

from core.identity import display_name, employee_code, identity_label
from core.money import format_decimal

register = template.Library()


@register.filter
def ten(user):
    """Tên hiển thị: họ tên trong hồ sơ, không có thì tên đăng nhập; không có người thì rỗng."""
    return display_name(user)


@register.filter
def ma(user):
    """Mã nhân sự (ADR-037): `{{ u|ma }}` ở mọi chỗ cần định danh — chưa gán mã thì tên đăng nhập."""
    return employee_code(user)


@register.filter
def ma_ten(user):
    """`MÃ · Họ tên` — mã trước, tên sau; không có họ tên thì chỉ mã."""
    return identity_label(user)


@register.filter
def so(value):
    """Số trên màn hình theo cách viết Việt Nam như ERP: dấu chấm ngăn nghìn, phẩy thập phân, tối đa hai số lẻ, số
    nguyên không kèm ",00" — `48311822000` → `48.311.822.000`, `762792.694` → `762.792,69` (AC-22.27). Không phải số
    (như "—") thì trả nguyên. `floatformat` không nhóm được vì locale `vi` của Django không khai `NUMBER_GROUPING`."""
    try:
        d = Decimal(str(value)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError):
        return value
    d = d.quantize(Decimal(1)) if d == d.to_integral_value() else d.normalize()
    return format_decimal(d) or value


@register.simple_tag
def avatar(user, lon=False):
    """Ô chữ cái đầu tên — chỉ trang trí nên đọc màn hình bỏ qua; không có
    người (tài khoản đã xoá) thì dấu hỏi. `lon=True` là cỡ lớn ở đầu bài."""
    chu = display_name(user)[:1].upper() or "?"
    return format_html(
        '<div class="avatar{}" aria-hidden="true">{}</div>', " avatar-lon" if lon else "", chu,
    )


@register.simple_tag(takes_context=True)
def trang_url(context, dat, gia_tri, bo="", qs_loc=""):
    """Liên kết của thanh phân trang (AC-10.18): giữ **mọi** tham số của URL đang mở, đặt `dat=gia_tri`, bỏ `bo`.

    Chuỗi lọc `qs_loc` màn hình truyền (bắt đầu bằng "&") được chồng lên trước, để màn hình nào đã truyền vẫn y như cũ.
    Màn hình quên truyền không còn mất bộ lọc khi chuyển trang, và trang có hai bảng phân trang không làm bảng kia về
    trang 1. Mã hoá bằng `QueryDict.urlencode`, nên chữ có "&", "#" không làm vỡ liên kết."""
    from django.http import QueryDict

    request = context.get("request")
    tham_so = request.GET.copy() if request is not None else QueryDict(mutable=True)
    if qs_loc:
        for khoa, cac in QueryDict(str(qs_loc).lstrip("&")).lists():
            tham_so.setlist(khoa, cac)
    if bo:
        tham_so.pop(bo, None)
    tham_so[dat] = str(gia_tri)
    return "?" + tham_so.urlencode()
