"""Số phiên bản `?v=` của CSS/JS tự đổi khi tệp tĩnh đổi — AC-10.11.

Máy chạy thử (DEBUG) chỉ tự khởi động lại khi mã Python đổi; sửa riêng CSS/JS thì số tính lúc khởi
động giữ nguyên và trình duyệt dùng bản cũ trong bộ đệm (chủ dự án 28.09.2026 phải Ctrl+F5 mới thấy).
"""
import os

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from core import context_processors


def _phien_ban(settings):
    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    return context_processors.khung_chung(request)["phien_ban_tinh"]


def _tao_tinh(tmp_path, settings):
    (tmp_path / "static" / "js").mkdir(parents=True)
    tep = tmp_path / "static" / "js" / "luoi.js"
    tep.write_text("// cũ")
    os.utime(tep, (1_700_000_000, 1_700_000_000))
    settings.BASE_DIR = tmp_path
    return tep


def test_debug_sua_js_thi_phien_ban_doi_khong_can_khoi_dong_lai(tmp_path, settings):
    """AC-10.11 — Máy chạy thử (DEBUG): sửa một tệp JS/CSS thì `phien_ban_tinh` của lần tải trang kế
    tiếp đổi ngay, không phải khởi động lại tiến trình hay Ctrl+F5"""
    settings.DEBUG = True
    tep = _tao_tinh(tmp_path, settings)
    truoc = _phien_ban(settings)
    os.utime(tep, (1_700_000_500, 1_700_000_500))
    assert _phien_ban(settings) != truoc


def test_may_chu_that_giu_so_tinh_luc_khoi_dong(tmp_path, settings, monkeypatch):
    """AC-10.11 — Máy chủ thật (DEBUG tắt) giữ số tính một lần lúc khởi động, không quét tệp mỗi
    lần tải trang; phát hành là khởi động lại nên số vẫn đổi"""
    settings.DEBUG = False
    monkeypatch.setattr(context_processors, "PHIEN_BAN_TINH", "khoi-dong")
    tep = _tao_tinh(tmp_path, settings)
    os.utime(tep, (1_700_000_500, 1_700_000_500))
    assert _phien_ban(settings) == "khoi-dong"
