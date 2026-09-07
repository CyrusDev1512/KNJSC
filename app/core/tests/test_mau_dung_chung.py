"""Bộ lọc `|ten`, thẻ `{% avatar %}` và `is_htmx` — rà soát 07.09.2026.

Một luật hiển thị tên cho template (Q59) và một chỗ nhận biết yêu cầu htmx,
thay cho `profile.full_name|default:username` và `request.headers.get(...)`
chép ở từng nơi.
"""
import pytest
from django.template import Context, Template

from core.htmx import is_htmx

pytestmark = pytest.mark.django_db

MAU = Template("{% load knjsc %}[{{ u|ten }}]{% avatar u %}{% avatar u lon=True %}")


def test_loc_ten_va_the_avatar(nguoi_dung):
    """Q59 — `|ten` là họ tên trong hồ sơ, không có thì tên đăng nhập, không có người thì rỗng; `{% avatar %}` là chữ cái đầu tên có `aria-hidden`, bản lớn thêm lớp `avatar-lon`, không có người thì dấu hỏi; tên chứa ký tự HTML được thoát"""
    u = nguoi_dung["staff_sale_1"]
    ra = MAU.render(Context({"u": u}))
    assert "[Staff Sale 1]" in ra
    assert '<div class="avatar" aria-hidden="true">S</div>' in ra
    assert '<div class="avatar avatar-lon" aria-hidden="true">S</div>' in ra

    ra = MAU.render(Context({"u": None}))
    assert ra.startswith("[]") and ra.count('>?</div>') == 2

    u.profile.full_name = ""
    u.profile.save(update_fields=["full_name"])
    assert "[staff_sale_1]" in MAU.render(Context({"u": u}))

    u.profile.full_name = "<b>Ẩn</b>"
    u.profile.save(update_fields=["full_name"])
    ra = MAU.render(Context({"u": u}))
    assert "[&lt;b&gt;Ẩn&lt;/b&gt;]" in ra and 'aria-hidden="true">&lt;</div>' in ra and "<b>" not in ra


def test_is_htmx_chi_nhan_header_dung(rf):
    """ADR-005 — Chỉ yêu cầu mang header `HX-Request: true` mới là yêu cầu htmx"""
    assert is_htmx(rf.get("/", HTTP_HX_REQUEST="true"))
    assert not is_htmx(rf.get("/"))
    assert not is_htmx(rf.get("/", HTTP_HX_REQUEST="false"))
