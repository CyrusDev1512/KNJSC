"""Ghi nhật ký hoạt động.

Nhật ký chỉ ghi ai làm gì với đối tượng nào. Tuyệt đối không ghi mật khẩu,
số thẻ, hay thông tin cá nhân đầy đủ vào đây, kể cả khi gỡ lỗi (điều cấm 6).
"""
from .constants import AuditAction
from .models import AuditLog

# Những từ khoá không bao giờ được xuất hiện trong phần chi tiết
SENSITIVE_KEYS = (
    "password", "mat_khau", "token", "secret", "api_key",
    "card", "cvv", "the", "otp",
)

MAX_DETAIL = 500


def _client_ip(request):
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _scrub(detail):
    """Bỏ đi phần chi tiết nếu nó lỡ chứa từ khoá nhạy cảm."""
    if not detail:
        return ""
    thap = str(detail).lower()
    if any(k in thap for k in SENSITIVE_KEYS):
        return "[đã lược bỏ vì chứa dữ liệu nhạy cảm]"
    return str(detail)[:MAX_DETAIL]


def record(action, actor=None, target=None, detail="", request=None, actor_label=""):
    """Ghi một dòng vào nhật ký. Luôn thành công, không làm hỏng nghiệp vụ.

    `target` có thể là một model đã lưu, hoặc một cặp (loại, mã).
    """
    target_type, target_id = "", ""
    if target is not None:
        if isinstance(target, (tuple, list)) and len(target) == 2:
            target_type, target_id = str(target[0]), str(target[1])
        else:
            target_type = target.__class__.__name__
            target_id = str(getattr(target, "pk", "") or "")

    if not actor_label and actor is not None:
        actor_label = getattr(actor, "get_full_name", lambda: "")() or actor.get_username()

    return AuditLog.objects.create(
        actor=actor if getattr(actor, "pk", None) else None,
        actor_label=actor_label[:150],
        action=action,
        target_type=target_type[:80],
        target_id=target_id[:80],
        detail=_scrub(detail),
        ip_address=_client_ip(request),
    )


def record_denied(user, path, request=None):
    """Ghi lại một lần truy cập bị từ chối (FR-3.5, AC-3.7)."""
    return record(
        AuditAction.DENIED,
        actor=user if getattr(user, "is_authenticated", False) else None,
        target=("path", path),
        detail="Ngoài phạm vi quyền, trả lỗi 403",
        request=request,
        actor_label="" if getattr(user, "is_authenticated", False) else "chưa đăng nhập",
    )
