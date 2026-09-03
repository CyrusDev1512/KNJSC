"""Gom số liệu cho màn hình Tổng quan, theo phạm vi người xem.

**Nguyên tắc chịu lỗi** (kien-truc.md): Tổng quan không được phụ thuộc bắt
buộc vào bất kỳ khối nào. Một khối hỏng thì khối đó báo "tạm chưa khả dụng",
các khối còn lại vẫn hiện bình thường.

Vì vậy mỗi khối được gọi trong một lớp bọc riêng, không dùng chung một
try lớn — một lỗi không kéo cả màn hình xuống.
"""
import logging

from django.db.models import Count

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
    """Khối bảng dữ liệu do người dùng tạo, trong phạm vi quyền.

    Nhập muộn để `dashboard` không phụ thuộc cứng vào `forms_builder`:
    `kien-truc.md` đòi Tổng quan vẫn chạy khi một khối hỏng, nên khối này
    phải hỏng được mà không kéo cả trang theo.
    """
    from forms_builder.models import DataRecord, TableDef

    bang = list(
        TableDef.objects.in_scope(user)
        .select_related("department")
        .annotate(so_dong=Count("records", distinct=True))
        .order_by("-updated_at")[:5]
    )
    return {
        "cac_bang": bang,
        "so_bang": TableDef.objects.in_scope(user).count(),
        "so_dong": DataRecord.objects.in_scope(user).count(),
    }


def _tac_vu(user):
    """Khối tác vụ nền trong phạm vi người xem: đang chờ, đang chạy, kẹt."""
    from core.constants import JobStatus
    from core.models import BackgroundJob

    ds = BackgroundJob.objects.in_scope(user)
    return {
        "cho": ds.filter(status=JobStatus.PENDING).count(),
        "chay": ds.filter(status=JobStatus.RUNNING).count(),
        "ket": ds.filter(status=JobStatus.STALE).count(),
        "gan_day": list(ds.select_related("created_by")[:5]),
    }


def _sao_luu():
    """Khối sao lưu — chỉ Admin. Đêm qua có bản không, còn bao nhiêu bản."""
    from core.services import backup_service

    job = backup_service.last_backup()
    cac_ban = backup_service.list_backups()
    return {
        "job": job,
        "so_ban": len(cac_ban),
        "moi_nhat": cac_ban[0].name if cac_ban else "",
        "thu_muc": str(backup_service.backup_dir()),
    }


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
        "tac_vu": _khoi("tac_vu", lambda: _tac_vu(user)),
        "sao_luu": _khoi("sao_luu", _sao_luu) if scope.is_admin else None,
    }
