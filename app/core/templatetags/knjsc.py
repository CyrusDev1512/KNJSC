"""Thẻ và bộ lọc mẫu dùng chung — `{% load knjsc %}`.

Một luật hiển thị tên cho cả hệ thống (`core.identity`, Q59, ADR-037): template viết
`{{ u|ten }}` cho lời chào, `{{ u|ma }}` / `{{ u|ma_ten }}` cho chỗ cần định danh (mã
trước, tên sau) thay vì tự ghép `profile.full_name|default:username`, và `{% avatar u %}`
thay vì chép lại ô chữ cái đầu tên ở từng chỗ.
"""
from django import template
from django.utils.html import format_html

from core.identity import display_name, employee_code, identity_label

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


@register.simple_tag
def avatar(user, lon=False):
    """Ô chữ cái đầu tên — chỉ trang trí nên đọc màn hình bỏ qua; không có
    người (tài khoản đã xoá) thì dấu hỏi. `lon=True` là cỡ lớn ở đầu bài."""
    chu = display_name(user)[:1].upper() or "?"
    return format_html(
        '<div class="avatar{}" aria-hidden="true">{}</div>', " avatar-lon" if lon else "", chu,
    )
