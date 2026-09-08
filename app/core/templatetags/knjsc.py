"""Thẻ và bộ lọc mẫu dùng chung — `{% load knjsc %}`.

Một luật hiển thị tên cho cả hệ thống (`core.identity.display_name`, Q59):
template viết `{{ u|ten }}` thay vì tự ghép `profile.full_name|default:username`,
và `{% avatar u %}` thay vì chép lại ô chữ cái đầu tên ở từng chỗ.
"""
from django import template
from django.utils.html import format_html

from core.identity import display_name

register = template.Library()


@register.filter
def ten(user):
    """Tên hiển thị: họ tên trong hồ sơ, không có thì tên đăng nhập; không có người thì rỗng."""
    return display_name(user)


@register.simple_tag
def avatar(user, lon=False):
    """Ô chữ cái đầu tên — chỉ trang trí nên đọc màn hình bỏ qua; không có
    người (tài khoản đã xoá) thì dấu hỏi. `lon=True` là cỡ lớn ở đầu bài."""
    chu = display_name(user)[:1].upper() or "?"
    return format_html(
        '<div class="avatar{}" aria-hidden="true">{}</div>', " avatar-lon" if lon else "", chu,
    )
