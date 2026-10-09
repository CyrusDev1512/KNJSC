"""Lỗi máy chủ, trang không có, đĩa đầy: luôn nói tiếng Việt — AC-10.14 (săn lỗi 06.10.2026).

Đo trên hệ thống thật với thư mục `storage` trên một ổ 1 MB đã đầy: tải tài liệu và nhập tệp là trang lỗi 500, tệp
người dùng chọn mất, không ai biết vì sao; người vận hành không được báo. Và dự án không có `500.html`, `404.html`:
DEBUG tắt (VPS) thì Django in trang trắng chữ Anh "Server Error (500)", "Not Found" — trái NFR-6.
"""
import errno
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from documents.services import document_service
from documents.tests.test_tai_lieu import PDF, cac_muc  # noqa: F401 — fixture `cac_muc` dùng chung

pytestmark = pytest.mark.django_db


def _tai_len(client, cac_muc):  # noqa: F811
    return client.post("/tai-lieu/tai-len/", {
        "category": cac_muc["sale"].pk, "title": "Quy định", "description": "",
        "file": SimpleUploadedFile("qd.pdf", PDF, content_type="application/octet-stream"),
    })


def test_loi_500_hien_trang_tieng_viet(cac_muc, nguoi_dung, settings):  # noqa: F811
    """AC-10.14 — Lỗi không lường trước khi DEBUG tắt: trang lỗi 500 tiếng Việt nói dữ liệu vừa gửi có thể chưa lưu và cách làm tiếp, không phải trang trắng "Server Error (500)" """
    settings.DEBUG = False
    client = Client(raise_request_exception=False)
    client.force_login(nguoi_dung["manager_sale"])
    with patch.object(document_service, "upload_document", side_effect=RuntimeError("hong")):
        r = _tai_len(client, cac_muc)
    assert r.status_code == 500
    html = r.content.decode()
    assert 'lang="vi"' in html and "Hệ thống gặp lỗi" in html
    assert "Server Error" not in html


def test_trang_khong_co_hien_404_tieng_viet(client, nguoi_dung, settings):
    """AC-10.14 — Đường dẫn không có (gõ sai, bảng đã bỏ khỏi KN CRM): trang 404 tiếng Việt có nút về Tổng quan, không phải "Not Found" chữ Anh"""
    settings.DEBUG = False
    client.force_login(nguoi_dung["staff_sale_1"])
    r = client.get("/khong-co-trang-nay/")
    assert r.status_code == 404
    html = r.content.decode()
    assert "Không tìm thấy trang" in html and 'href="/"' in html
    assert "The requested resource" not in html


def test_dia_day_bao_ro_va_bao_nguoi_van_hanh(cac_muc, nguoi_dung, settings):  # noqa: F811
    """AC-10.14 — Máy chủ hết chỗ lưu tệp (ENOSPC) khi tải lên: trả 507 với lời tiếng Việt "hết chỗ lưu tệp, tệp chưa được lưu", và thư cảnh báo người vận hành — không phải trang lỗi 500 chung chung"""
    settings.DEBUG = False
    client = Client(raise_request_exception=False)
    client.force_login(nguoi_dung["manager_sale"])
    cache.delete("canh-bao-het-dia")
    het = OSError(errno.ENOSPC, "No space left on device")
    with patch.object(document_service, "upload_document", side_effect=het), \
            patch("core.alerts.mail_admins") as bao:
        r = _tai_len(client, cac_muc)
    assert r.status_code == 507
    assert "hết chỗ lưu tệp" in r.content.decode()
    assert bao.called
