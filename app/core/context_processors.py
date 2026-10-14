"""Biến dùng chung cho mọi template."""
from pathlib import Path

from django.conf import settings
from django.utils.functional import SimpleLazyObject

from .lien_ket import crm_url
from .exceptions import NoProfileError
from .navigation import visible_navigation
from .scope import get_user_scope
from .permissions import has_rank, is_admin, is_crm_request
from .constants import Rank


def _phien_ban_tinh():
    """Số phiên bản gắn sau đường dẫn CSS và JS (`?v=...`) để trình duyệt tải
    tệp mới khi mã đổi, thay vì dùng bản cũ trong bộ đệm. Lấy từ thời điểm
    sửa gần nhất của các tệp tĩnh. Máy chủ thật tính một lần lúc khởi động
    (phát hành là khởi động lại); máy chạy thử xem `phien_ban_hien_tai`."""
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


def phien_ban_hien_tai():
    """Máy chạy thử (DEBUG) quét lại mỗi lần tải trang: runserver chỉ tự khởi
    động lại khi mã Python đổi, nên sửa riêng CSS/JS thì số tính lúc khởi động
    đứng yên và trình duyệt dùng bản cũ (AC-10.11). Thư mục tĩnh vài chục tệp,
    quét chỉ tốn vài phần nghìn giây."""
    return _phien_ban_tinh() if settings.DEBUG else PHIEN_BAN_TINH


def khung_chung(request):
    """Thanh điều hướng và phạm vi quyền, có ở mọi màn hình."""
    if not request.user.is_authenticated:
        return {"phien_ban_tinh": phien_ban_hien_tai()}
    try:
        scope = get_user_scope(request.user)
    except NoProfileError:
        # Chỉ nuốt đúng lỗi này, để thanh điều hướng vẫn vẽ được trên trang
        # từ chối. Mọi lỗi khác phải nổi lên, không được che.
        scope = None
    # Mục "Nộp báo cáo ngày" theo biểu mẫu có thật (chủ dự án 13–14.10): một truy vấn (Kế toán hai), tính lười và một lần
    # cho cả menu lẫn nút ở Lịch sử. KN CRM không có trang nộp báo cáo nên không hỏi
    from reports.services.daily_service import can_submit_reports
    nop_bao_cao = False if is_crm_request(request) else SimpleLazyObject(lambda: can_submit_reports(request.user))
    return {
        "crm_app_url": crm_url(request),
        "nav_groups": SimpleLazyObject(lambda: visible_navigation(request.user, can_submit_reports=bool(nop_bao_cao))),
        "nav_current": getattr(request, "nav_current", ""),
        "scope": scope,
        "can_open_tables": is_crm_request(request) or has_rank(request.user, Rank.MANAGER),
        "can_list_jobs": is_crm_request(request) or is_admin(request.user),
        "can_submit_reports": nop_bao_cao,
        "profile": getattr(request.user, "profile", None),
        "phien_ban_tinh": phien_ban_hien_tai(),
    }
