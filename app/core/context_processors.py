"""Biến dùng chung cho mọi template."""
from pathlib import Path

from django.conf import settings

from .exceptions import NoProfileError
from .navigation import visible_navigation
from .scope import get_user_scope


def _phien_ban_tinh():
    """Số phiên bản gắn sau đường dẫn CSS và JS (`?v=...`) để trình duyệt tải
    tệp mới khi mã đổi, thay vì dùng bản cũ trong bộ đệm. Lấy từ thời điểm
    sửa gần nhất của các tệp tĩnh, tính một lần lúc tiến trình khởi động —
    máy phát triển tự khởi động lại khi đổi mã, máy chủ khởi động lại khi
    cập nhật."""
    moi_nhat = 0
    for goc in [settings.BASE_DIR / "static"]:
        for tep in Path(goc).rglob("*"):
            if tep.suffix in (".css", ".js"):
                try:
                    moi_nhat = max(moi_nhat, int(tep.stat().st_mtime))
                except OSError:
                    continue
    return str(moi_nhat or 1)


PHIEN_BAN_TINH = _phien_ban_tinh()


def khung_chung(request):
    """Thanh điều hướng và phạm vi quyền, có ở mọi màn hình."""
    if not request.user.is_authenticated:
        return {"phien_ban_tinh": PHIEN_BAN_TINH}
    try:
        scope = get_user_scope(request.user)
    except NoProfileError:
        # Chỉ nuốt đúng lỗi này, để thanh điều hướng vẫn vẽ được trên trang
        # từ chối. Mọi lỗi khác phải nổi lên, không được che.
        scope = None
    return {
        "nav_groups": visible_navigation(request.user),
        "nav_current": getattr(request, "nav_current", ""),
        "scope": scope,
        "profile": getattr(request.user, "profile", None),
        "phien_ban_tinh": PHIEN_BAN_TINH,
    }
