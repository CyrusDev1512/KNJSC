"""Dịch vụ `bangtinh` — cùng mã, cấu hình thu hẹp (ADR-009, backlog Q38).

Dựng lại đúng cấu hình của `knjsc/settings/bangtinh.py` bằng override: URLconf
thu hẹp, bảng vận đơn sửa được, mục Bảng tính trên thanh bên là liên kết trong.
"""
import re
import uuid

import pytest
from django.test import override_settings

from forms_builder.services import record_service
from orders.services import dispatch_service

pytestmark = pytest.mark.django_db

DICH_VU_BANGTINH = override_settings(
    ROOT_URLCONF="knjsc.urls_bangtinh", GRID_ONLY_TABLES=set(), BANGTINH_URL="",
)


@pytest.fixture
def bang_vd(departments, nguoi_dung):
    return dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])


def _links_to(html, href):
    return [tag for tag in re.findall(r"<a\b[^>]*>", html) if f'href="{href}"' in tag]


def test_dich_vu_bangtinh_chi_co_bang_tinh_va_dang_nhap(client, bang_vd, nguoi_dung):
    """AC-11.7 — Ở app KN CRM: gốc là trang chủ, lưới sửa được, các màn hình khác không tồn tại"""
    dong = record_service.create_record(
        bang_vd, {"ma_don": "DH-1", "ten_khach": "A", "so_dien_thoai": "0911"},
        actor=nguoi_dung["staff_vd"],
    )
    client.force_login(nguoi_dung["staff_vd"])
    with DICH_VU_BANGTINH:
        kq = client.get("/")
        html_goc = kq.content.decode()
        assert kq.status_code == 200 and "KN CRM" in html_goc and 'id="thanh-ben"' in html_goc
        kq = client.get("/bang-tinh/van_don/")
        assert kq.status_code == 200
        assert kq.context["config"]["saveUrl"] == "/bang-tinh/van_don/luu-json/"
        html = kq.content.decode()
        assert 'id="master-grid"' in html and 'id="mg-config"' in html
        # Thanh bên: có Bảng tính (liên kết trong); các mục của dịch vụ chính
        # không vẽ vì đường dẫn không tồn tại ở đây (nút "Bảng dữ liệu" trên
        # lưới là liên kết ngoài về dịch vụ chính, không tính)
        assert any('class="bt-hieu"' in tag for tag in _links_to(html, "/"))
        assert "KN CRM" in html
        for vang in ('href="/bang/"', 'href="/len-don/"', 'href="/bieu-mau/"', 'href="/bao-cao-ngay/"'):
            assert vang not in html, f"dịch vụ bangtinh không được có mục {vang}"
        payload = {"operation": str(uuid.uuid4()), "cells": [{
            "id": dong.pk, "column": "ghi_chu", "old": dong.data.get("ghi_chu"),
            "value": "sửa ở Bảng tính",
        }]}
        assert client.post(
            "/bang-tinh/van_don/luu-json/", payload, content_type="application/json",
        ).status_code == 200
        assert client.get("/bang/").status_code == 404
        assert client.get("/len-don/").status_code == 404
        assert client.get("/tac-vu/").status_code == 403, "danh sách tác vụ chỉ dành cho Admin"
    dong.refresh_from_db()
    assert dong.data["ghi_chu"] == "sửa ở Bảng tính"


def test_erp_dung_logo_kn_jsc(client, nguoi_dung):
    """AC-11.31 — KN ERP dùng logo KN JSC ở header (bấm về Tổng quan), ADR-028."""
    client.force_login(nguoi_dung["staff_vd"])
    with override_settings(ROOT_URLCONF="knjsc.urls"):
        html = client.get("/").content.decode()
    assert 'class="sp-brand" href="/"' in html and "img/kn-jsc.svg" in html and "img/kn-crm.svg" not in html
    assert 'rel="icon" type="image/svg+xml" href="/static/img/kn-jsc.svg' in html


def test_erp_chi_con_lien_ket_sang_kn_crm(client, bang_vd, nguoi_dung, settings):
    """AC-11.30 — Ở KN ERP mục KN CRM trên thanh bên của mọi bộ phận là liên kết ngoài mở tab mới, lưới không tồn tại ở ERP, Bảng dữ liệu có nút mở đúng bảng trong KN CRM; ở KN CRM mục này là liên kết trong cùng tab"""
    settings.ROOT_URLCONF = "knjsc.urls"                     # KN ERP
    settings.BANGTINH_URL = "http://localhost:8021/"
    for ma in ("staff_vd", "staff_sale_1", "staff_mkt", "admin"):
        client.force_login(nguoi_dung[ma])
        html = client.get("/").content.decode()
        crm_links = _links_to(html, "http://localhost:8021/")
        assert crm_links, f"{ma} không thấy mục KN CRM mở tab mới"
        assert 'target="_blank"' in crm_links[0] and 'rel="noopener"' in crm_links[0]
        assert "KN CRM" in html
    client.force_login(nguoi_dung["staff_vd"])
    assert client.get("/bang-tinh/").status_code == 404, "lưới không còn ở ERP"
    assert client.get("/bang-tinh/van_don/").status_code == 404
    assert client.get("/bang/van_don/").status_code == 403
    client.force_login(nguoi_dung["admin"])
    html = client.get("/bang/van_don/").content.decode()
    assert 'href="http://localhost:8021/bang-tinh/van_don/" target="_blank" rel="noopener">Mở trong KN CRM</a>' in html

    # Ở chính KN CRM: mục là liên kết trong, không mở tab mới
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.BANGTINH_URL = ""
    html = client.get("/bang-tinh/").content.decode()
    crm_links = _links_to(html, "/")
    assert crm_links and "KN CRM" in html
    assert all('target="_blank"' not in tag for tag in crm_links)
