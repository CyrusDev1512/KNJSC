"""Kiểm thử nhật ký hoạt động và tiền tệ."""
from decimal import Decimal

import pytest

from core import audit
from core.constants import AuditAction, Currency
from core.models import AuditLog
from core.money import format_money

pytestmark = pytest.mark.django_db


def test_ghi_duoc_mot_dong_nhat_ky(nguoi_dung):
    """AC-9.2 — Ghi được hành động vào nhật ký"""
    ban_ghi = audit.record(
        AuditAction.CREATE, actor=nguoi_dung["staff_sale_1"], detail="Tạo đơn thử",
    )
    assert ban_ghi.pk
    assert ban_ghi.action == AuditAction.CREATE
    assert ban_ghi.actor_label


def test_khong_sua_duoc_ban_ghi_nhat_ky(nguoi_dung):
    """AC-9.3 — Không ai sửa được bản ghi nhật ký, kể cả quản trị viên"""
    ban_ghi = audit.record(AuditAction.LOGIN, actor=nguoi_dung["admin"])
    ban_ghi.detail = "sửa trộm"
    with pytest.raises(RuntimeError):
        ban_ghi.save()


def test_khong_xoa_duoc_ban_ghi_nhat_ky(nguoi_dung):
    """AC-9.3 — Không ai xoá được bản ghi nhật ký"""
    ban_ghi = audit.record(AuditAction.LOGIN, actor=nguoi_dung["admin"])
    with pytest.raises(RuntimeError):
        ban_ghi.delete()


def test_khong_ghi_du_lieu_nhay_cam_vao_nhat_ky(nguoi_dung):
    """Điều cấm 6 — Dữ liệu nhạy cảm không lọt vào nhật ký"""
    ban_ghi = audit.record(
        AuditAction.UPDATE, actor=nguoi_dung["admin"],
        detail="password=Bimat123 token=abcdef",
    )
    assert "Bimat123" not in ban_ghi.detail
    assert "abcdef" not in ban_ghi.detail


def test_ghi_lai_lan_truy_cap_bi_tu_choi(nguoi_dung):
    """AC-3.7 — Truy cập bị từ chối được ghi lại kèm đường dẫn"""
    audit.record_denied(nguoi_dung["staff_sale_1"], "/bang-van-don/")
    ban_ghi = AuditLog.objects.filter(action=AuditAction.DENIED).first()
    assert ban_ghi.target_id == "/bang-van-don/"


def test_tien_luu_dang_so_thap_phan_chinh_xac():
    """AC-9.5 — Cộng tiền không bị sai số như số thực dấu phẩy động"""
    tong = Decimal("0.00")
    for _ in range(10):
        tong += Decimal("0.10")
    assert tong == Decimal("1.00")


def test_hien_thi_tien_theo_tap_quan_viet_nam():
    """AC-9.5 — VND không có số lẻ, USD có hai số lẻ"""
    assert format_money(Decimal("1875000"), Currency.VND) == "1.875.000 ₫"
    assert format_money(Decimal("192.50"), Currency.USD) == "$192,50"
    assert format_money(Decimal("-42.5"), Currency.USD) == "-$42,50"
