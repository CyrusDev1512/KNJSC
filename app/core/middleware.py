"""Middleware của core.

Bốn việc: hết phiên khi không thao tác, buộc đổi mật khẩu lần đầu, chặn
trình duyệt lưu lại trang có dữ liệu, và đưa chữ người dùng gửi lên về dạng NFC.
"""
import json
import time
import unicodedata

from django.conf import settings
from django.contrib.auth import logout
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.cache import add_never_cache_headers

from .alerts import bao_het_dia, la_het_dia
from .htmx import is_htmx

# Những đường dẫn luôn cho qua, nếu không sẽ chuyển hướng vòng tròn
EXEMPT_PREFIXES = ("/dang-nhap", "/dang-xuat", "/doi-mat-khau", "/static", "/media")


def _is_exempt(path):
    return any(path.startswith(p) for p in EXEMPT_PREFIXES)


def _ve_dang_nhap(request, ly_do):
    """Về trang đăng nhập. Yêu cầu HTMX (bấm Thích, đổi trạng thái…) thì bảo
    trình duyệt tự chuyển trang bằng header `HX-Redirect` — trả 302 thì htmx
    đi theo rồi nhét cả trang đăng nhập vào chỗ nút."""
    url = f"{settings.LOGIN_URL}?{ly_do}=1"
    if is_htmx(request):
        return HttpResponse(status=200, headers={"HX-Redirect": url})
    return redirect(url)


class SessionTimeoutMiddleware:
    """Phiên hết hạn hoặc mất hiệu lực.

    Hai việc:

    1. Hết phiên sau một khoảng không thao tác.
    2. Nguyên tắc P4 — đổi quyền hoặc khoá tài khoản thì phiên đang mở mất
       hiệu lực **ngay**, không đợi lần đăng nhập sau. Hồ sơ nhân sự giữ một
       số mốc `session_epoch`, tăng lên mỗi lần đổi quyền. Phiên nào mang
       mốc cũ thì bị đẩy ra.
    """

    #: Chỉ ghi lại dấu thời gian khi đã trôi quá ngần này giây. Ghi ở mọi yêu
    #: cầu thì mỗi lần mở trang đều kèm một lệnh UPDATE vào bảng phiên — tốn
    #: vô ích, và làm màn hình danh sách vượt ngưỡng số truy vấn ở AC-10.2.
    GHI_LAI_SAU = 60

    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout = getattr(settings, "SESSION_IDLE_TIMEOUT_SECONDS", 3600)

    def __call__(self, request):
        if request.user.is_authenticated:
            now = int(time.time())
            last = request.session.get("last_seen_at")
            if last and now - last > self.timeout:
                logout(request)
                return _ve_dang_nhap(request, "het_phien")

            profile = getattr(request.user, "profile", None)
            if profile is not None:
                moc_phien = request.session.get("auth_epoch")
                if moc_phien is not None and moc_phien != profile.session_epoch:
                    logout(request)
                    return _ve_dang_nhap(request, "doi_quyen")

            if last is None or now - last >= self.GHI_LAI_SAU:
                request.session["last_seen_at"] = now
        return self.get_response(request)


class ForcePasswordChangeMiddleware:
    """Buộc đổi mật khẩu trước khi dùng hệ thống (FR-1.3)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and not _is_exempt(request.path):
            profile = getattr(user, "profile", None)
            if profile is not None and getattr(profile, "must_change_password", False):
                return redirect(reverse("doi_mat_khau"))
        return self.get_response(request)


class NoCacheForAuthenticatedMiddleware:
    """Không cho trình duyệt lưu lại trang của người đã đăng nhập.

    Nếu không có, bấm nút Lùi sau khi đăng xuất vẫn thấy dữ liệu cũ.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated and not request.path.startswith("/static"):
            add_never_cache_headers(response)
        return response


#: Ô không chuẩn hoá: mật khẩu phải giữ đúng từng byte người dùng gõ, không thì mật khẩu đặt từ máy này
#: không đăng nhập được từ máy kia nếu hai bên khác dạng (AC-9.6)
_KHONG_CHUAN_HOA = ("password", "mat_khau", "mat-khau", "csrfmiddlewaretoken")


def _nfc_querydict(qd):
    """Bản sao của QueryDict với mọi giá trị chữ ở dạng NFC; trả None khi không có gì phải đổi."""
    doi = False
    moi = qd.copy()
    for khoa, cac_gia_tri in qd.lists():
        if any(k in khoa.lower() for k in _KHONG_CHUAN_HOA):
            continue
        chuan = [unicodedata.normalize("NFC", v) if isinstance(v, str) else v for v in cac_gia_tri]
        if chuan != cac_gia_tri:
            moi.setlist(khoa, chuan)
            doi = True
    if not doi:
        return None
    moi._mutable = False
    return moi


def _nfc_json(v):
    if isinstance(v, str):
        return unicodedata.normalize("NFC", v)
    if isinstance(v, list):
        return [_nfc_json(x) for x in v]
    if isinstance(v, dict):
        return {(_nfc_json(k) if isinstance(k, str) else k): _nfc_json(x) for k, x in v.items()}
    return v


def tra_loi_400(request, loi):
    """Lời từ chối dữ liệu đầu vào đúng kiểu người gọi đợi: JSON cho lưới, chữ thuần cho HTMX (khung trang hiện nó),
    trang tiếng Việt có nút quay lại cho lần mở trang thường. Dựng trang không qua context processor: middleware chuẩn
    hoá chữ chạy trước khi biết người dùng là ai (AC-10.16)."""
    from django.template.loader import render_to_string

    if request.META.get("CONTENT_TYPE", "").startswith("application/json"):
        return JsonResponse({"error": loi, "code": "business_error"}, status=400)
    if request.headers.get("HX-Request"):
        return HttpResponseBadRequest(loi, content_type="text/plain; charset=utf-8")
    return HttpResponseBadRequest(render_to_string("500.html", {"loi_400": loi}))


#: Lời khi đầu vào có ký tự NUL — không có cách gõ hợp lệ nào ra ký tự này (AC-10.16)
CO_NUL = "Dữ liệu gửi lên có ký tự điều khiển không hợp lệ (NUL). Xoá ký tự đó rồi gửi lại."


def _co_nul_querydict(qd):
    return any("\x00" in k or any(isinstance(v, str) and "\x00" in v for v in vs) for k, vs in qd.lists())


def _co_nul_json(v):
    if isinstance(v, str):
        return "\x00" in v
    if isinstance(v, list):
        return any(_co_nul_json(x) for x in v)
    if isinstance(v, dict):
        return any(_co_nul_json(k) or _co_nul_json(x) for k, x in v.items())
    return False


class UnicodeNFCMiddleware:
    """Mọi chữ người dùng gửi lên về một dạng Unicode NFC — AC-9.6 (săn lỗi 06.10.2026); có ký tự NUL thì trả 400 —
    AC-10.16.

    macOS gửi chữ Việt dạng tổ hợp ("e" + dấu rời), Windows dạng dựng sẵn: nhìn y hệt nhưng so là khác, nên tên khách
    gõ từ Mac thì người dùng Windows tìm không ra, tra trùng và gộp nhóm trượt. Chuẩn hoá ở cửa vào để mọi tầng sau
    (ghi, tìm, lọc) chỉ thấy một dạng: tham số GET (tìm kiếm, lọc), form POST, thân JSON (lưới). Ô mật khẩu giữ
    nguyên. Tệp tải lên do `core.excel` chuẩn hoá khi đọc ô.

    Ký tự NUL thì Postgres không chứa được: lọt vào câu truy vấn là lỗi 500 (fuzz đo 26 chỗ). Chặn một lần ở đây cho
    mọi view; ô của tệp nhập do `record_service.parse_value` chặn.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.GET:
            if _co_nul_querydict(request.GET):
                return tra_loi_400(request, CO_NUL)
            moi = _nfc_querydict(request.GET)
            if moi is not None:
                request.GET = moi
        if request.method in ("POST", "PUT", "PATCH"):
            loai = request.META.get("CONTENT_TYPE", "")
            if loai.startswith("application/json"):
                # Đọc ra rồi chuẩn hoá từng chuỗi: JSON có thể mã hoá chữ thành "\u0302", chuẩn hoá văn bản thô không thấy
                try:
                    goc = json.loads(request.body or b"null")
                except (ValueError, UnicodeDecodeError):
                    goc = None
                if goc is not None:
                    if _co_nul_json(goc):
                        return tra_loi_400(request, CO_NUL)
                    chuan = _nfc_json(goc)
                    if chuan != goc:
                        request._body = json.dumps(chuan, ensure_ascii=False).encode("utf-8")
            elif loai.startswith(("application/x-www-form-urlencoded", "multipart/form-data")):
                if _co_nul_querydict(request.POST):
                    return tra_loi_400(request, CO_NUL)
                moi = _nfc_querydict(request.POST)
                if moi is not None:
                    request.POST = moi
        return self.get_response(request)


class DiskFullMiddleware:
    """Ghi tệp thất bại vì đĩa đầy: trả 507 với lời tiếng Việt và báo người vận hành, thay vì trang lỗi 500 chung chung
    (AC-10.14, săn lỗi 06.10.2026). Tải tài liệu, nhập tệp, chứng từ đều ghi vào `storage`."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not la_het_dia(exception):
            return None
        bao_het_dia(request.path)
        return render(request, "500.html", {"het_dia": True}, status=507)


#: SQLSTATE của Postgres → lời cho người dùng khi dữ liệu gửi lên vượt khuôn của cột (AC-10.16)
LOI_DU_LIEU = {
    "22001": "Nội dung quá dài so với chỗ lưu của ô này. Rút gọn rồi gửi lại.",
    "22003": "Số quá lớn so với chỗ lưu của ô này. Kiểm tra lại số rồi gửi lại.",
}


class DataLimitMiddleware:
    """Chuỗi dài hơn cột hay số tràn cột lọt tới cơ sở dữ liệu: trả 400 với lời tiếng Việt thay vì trang lỗi 500
    (fuzz đo: tên mục Tài nguyên 5.000 ký tự). Nhiều view đưa thẳng chuỗi form vào tầng dịch vụ (thư mục, mục tài liệu,
    mục tài nguyên, nhãn); chặn một lần ở đây cho mọi chỗ, kể cả chỗ viết sau này — AC-10.16."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        from django.db import DataError

        if not isinstance(exception, DataError):
            return None
        loi = LOI_DU_LIEU.get(getattr(exception.__cause__, "sqlstate", None))
        if loi is None:
            return None
        return tra_loi_400(request, loi)
