"""Biến dùng chung cho mọi template."""
from .exceptions import NoProfileError
from .navigation import visible_navigation
from .scope import get_user_scope


def khung_chung(request):
    """Thanh điều hướng và phạm vi quyền, có ở mọi màn hình."""
    if not request.user.is_authenticated:
        return {}
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
    }
