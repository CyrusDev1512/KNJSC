"""Danh tính hiển thị — FR-4.6, Q55. Một luật cho cả hệ thống."""
import pytest

from core.identity import display_name

pytestmark = pytest.mark.django_db


def test_display_name_uu_tien_ho_ten(nguoi_dung):
    """FR-4.6 — Họ tên trong hồ sơ; không có thì tên đăng nhập; không có người thì rỗng"""
    nv = nguoi_dung["staff_sale_1"]
    assert display_name(nv) == "Staff Sale 1"

    nv.profile.full_name = "   "
    nv.profile.save(update_fields=["full_name"])
    assert display_name(nv) == "staff_sale_1"

    assert display_name(None) == ""
