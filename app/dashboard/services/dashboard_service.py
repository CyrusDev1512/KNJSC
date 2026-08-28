"""Gom số liệu cho màn hình Tổng quan, theo phạm vi người xem.

**Nguyên tắc chịu lỗi** (kien-truc.md): Tổng quan không được phụ thuộc bắt
buộc vào bất kỳ khối nào. Một khối hỏng thì khối đó báo "tạm chưa khả dụng",
các khối còn lại vẫn hiện bình thường.

Vì vậy mỗi khối được gọi trong một lớp bọc riêng, không dùng chung một
try lớn — một lỗi không kéo cả màn hình xuống.
"""
import logging

from core.models import AuditLog
from core.scope import get_user_scope

logger = logging.getLogger(__name__)


def _khoi(ten, ham):
    """Chạy một khối. Hỏng thì trả cờ lỗi chứ không ném ra ngoài."""
    try:
        return {"ok": True, "data": ham()}
    except Exception:
        # Ghi nhật ký ứng dụng để người vận hành biết, nhưng không lộ chi
        # tiết kỹ thuật ra giao diện
        logger.exception("Khối Tổng quan '%s' lỗi", ten)
        return {"ok": False, "data": None}


def _so_nhan_su(user):
    from org.models import UserProfile

    ds = UserProfile.objects.in_scope(user)
    return {
        "tong": ds.count(),
        "hoat_dong": ds.filter(user__is_active=True).count(),
        "bi_khoa": ds.filter(user__is_active=False).count(),
    }


def _co_cau(user):
    """Số bộ phận và team trong phạm vi người xem.

    Phải đi qua `in_scope`, không được tự viết điều kiện lọc ở đây. Bản đầu
    tự lọc bằng `department_ids` cho mọi cấp bậc phi-admin, khiến Staff và
    Leader đếm được cả bộ phận — vừa sai phạm vi, vừa tạo chỗ thứ hai cài
    đặt phân quyền (điều cấm 1 và 11).
    """
    from org.models import Department, Team

    return {
        "so_bo_phan": Department.objects.in_scope(user).count(),
        "so_team": Team.objects.in_scope(user).count(),
    }


def _hoat_dong_gan_day(user):
    return list(
        AuditLog.objects.in_scope(user)
        .select_related("actor")
        .order_by("-created_at")[:8]
    )


def _bang_dong(user):
    """Khối bảng dữ liệu do người dùng tạo.

    Module forms_builder chưa có model nào — giai đoạn 3 mới làm. Ở đây cố
    tình báo chưa khả dụng để thấy được cách màn hình chịu lỗi.
    """
    raise NotImplementedError("Module forms_builder chưa có ở giai đoạn 2")


def tong_quan(user):
    """Toàn bộ số liệu của màn hình Tổng quan."""
    scope = get_user_scope(user)
    return {
        "scope": scope,
        "la_admin": scope.is_admin,
        "nhan_su": _khoi("nhan_su", lambda: _so_nhan_su(user)),
        "co_cau": _khoi("co_cau", lambda: _co_cau(user)),
        "hoat_dong": _khoi("hoat_dong", lambda: _hoat_dong_gan_day(user)),
        "bang_dong": _khoi("bang_dong", lambda: _bang_dong(user)),
    }
