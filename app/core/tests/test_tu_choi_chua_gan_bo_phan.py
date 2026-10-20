"""Manager mất bộ phận: mỗi lần 403 có đúng một dòng Từ chối, lưới nhận JSON, trang 403 có lối ra — TL-106.

P0-9 (#125) đổi danh sách rỗng thành 403 "Tài khoản chưa được gán bộ phận". Diễn tập chặng 2 bằng máy (14.10.2026) thấy
bốn chỗ chưa xong: Trang chủ KN CRM ghi 3 dòng ERROR kèm traceback; không có dòng Từ chối dù trang 403 nói đã ghi; lưới
nhận trang 403 HTML nên chỉ báo câu chung; trang 403 chỉ có "Về Tổng quan" dẫn sang một 403 khác.
"""
import json
import logging
import re

import pytest
from django.contrib.auth import get_user_model

from core.constants import AuditAction
from core.models import AuditLog
from crm.tests.test_waybill_feedback import feedback  # noqa: F401  (fixture dùng lại)

pytestmark = pytest.mark.django_db

ERP, CRM = "knjsc.urls", "knjsc.urls_bangtinh"
LOI = "Tài khoản chưa được gán bộ phận. Liên hệ quản trị viên."


def _dich_vu(settings, conf):
    settings.ROOT_URLCONF = conf
    if conf == CRM:
        settings.BANGTINH_URL = ""


def _mat_bo_phan(user):
    """Gỡ bộ phận bằng update() để phiên không bị đẩy ra (như dữ liệu cũ hay lệnh), rồi đọc lại tài khoản."""
    from org.models import UserProfile

    UserProfile.objects.filter(pk=user.profile.pk).update(department=None)
    return get_user_model().objects.get(pk=user.pk)


def _tu_choi(user):
    return list(AuditLog.objects.filter(action=AuditAction.DENIED, actor=user).order_by("pk").values_list("target_id", flat=True))


def _error(caplog):
    return [r.getMessage() for r in caplog.records if r.levelno >= logging.ERROR]


def test_trang_chu_crm_chua_gan_bo_phan_mot_dong_tu_choi_khong_log_error(client, settings, nguoi_dung, caplog):
    """AC-3.6 — Manager mất bộ phận mở Trang chủ KN CRM: 403 trang tiếng Việt kèm lời "chưa được gán bộ phận", đúng một
    dòng Từ chối trong Nhật ký, nhật ký ứng dụng không có dòng ERROR nào. Manager có bộ phận vẫn vào 200, không có dòng
    Từ chối, không có ERROR (FR-3.5, TL-106)"""
    _dich_vu(settings, CRM)
    ql = _mat_bo_phan(nguoi_dung["manager_vd"])
    client.force_login(ql)
    with caplog.at_level(logging.WARNING):
        r = client.get("/")
    assert r.status_code == 403 and "chưa được gán bộ phận" in r.content.decode()
    assert _error(caplog) == [], _error(caplog)
    assert _tu_choi(ql) == ["/"]

    caplog.clear()
    binh_thuong = nguoi_dung["manager_mkt"]
    client.force_login(binh_thuong)
    with caplog.at_level(logging.WARNING):
        assert client.get("/").status_code == 200
    assert _error(caplog) == [] and _tu_choi(binh_thuong) == []


def test_erp_chua_gan_bo_phan_403_dung_mot_dong_tu_choi(client, settings, nguoi_dung):
    """AC-3.7 — Manager mất bộ phận gọi thẳng Tổng quan và Nhân sự của KN ERP: 403 kèm lời "chưa được gán bộ phận" và
    đúng một dòng Từ chối mang đúng đường dẫn. Lần từ chối đã ghi ngay ở chỗ kiểm quyền không bị ghi thêm. Manager có
    bộ phận 200, không có dòng Từ chối (FR-3.5, TL-106)"""
    _dich_vu(settings, ERP)
    ql = _mat_bo_phan(nguoi_dung["manager_sale"])
    client.force_login(ql)
    for duong in ("/", "/nhan-su/"):
        r = client.get(duong)
        assert r.status_code == 403 and "chưa được gán bộ phận" in r.content.decode(), duong
    assert _tu_choi(ql) == ["/", "/nhan-su/"]
    # /tac-vu/ chặn ở assert_admin (ghi ngay chỗ kiểm, ném OutOfScopeError): trang 403 không ghi thêm dòng thứ hai
    assert client.get("/tac-vu/").status_code == 403
    assert _tu_choi(ql) == ["/", "/nhan-su/", "/tac-vu/"]

    client.force_login(nguoi_dung["manager_mkt"])
    assert client.get("/nhan-su/").status_code == 200
    assert _tu_choi(nguoi_dung["manager_mkt"]) == []


def test_luoi_crm_chua_gan_bo_phan_nhan_403_json_dung_loi(client, settings, nguoi_dung, feedback):  # noqa: F811
    """AC-3.6 — Lưới KN CRM của Manager mất bộ phận: du-lieu/ (GET mang X-KNJSC-User như het-phien.js gắn vào mọi fetch
    cùng nguồn) và luu-json/ (thân JSON) trả 403 JSON {error, code: "no_profile"} để lưới báo đúng lời, mỗi lần đúng một
    dòng Từ chối. Mở trang thường vẫn nhận trang 403 HTML; lỗi quyền khác có header vẫn là trang HTML như cũ. Leader
    Vận đơn có bộ phận đọc du-lieu/ được 200 (TL-106)"""
    _dich_vu(settings, CRM)
    bang, _, rows = feedback
    goc = f"/bang-tinh/{bang.code}/"
    ql = _mat_bo_phan(nguoi_dung["manager_vd"])
    client.force_login(ql)
    dau = {"HTTP_X_KNJSC_USER": str(ql.pk)}

    r = client.get(goc + "du-lieu/", **dau)
    assert r.status_code == 403 and r["Content-Type"].startswith("application/json"), r["Content-Type"]
    assert r.json() == {"error": LOI, "code": "no_profile"}
    r = client.post(goc + "luu-json/", json.dumps({"operation": "tl106", "cells": [
        {"id": rows[0].pk, "column": "ghi_chu", "old": None, "value": "x"}]}), content_type="application/json", **dau)
    assert r.status_code == 403 and r.json()["code"] == "no_profile"
    r = client.get(goc)
    assert r.status_code == 403 and r["Content-Type"].startswith("text/html")
    assert _tu_choi(ql) == [goc + "du-lieu/", goc + "luu-json/", goc]

    # Bài canh: lỗi quyền khác (assert_admin) có header vẫn là trang HTML, một dòng — JSON chỉ cho chưa gán bộ phận
    r = client.get("/tac-vu/", **dau)
    assert r.status_code == 403 and r["Content-Type"].startswith("text/html")
    assert _tu_choi(ql).count("/tac-vu/") == 1

    client.force_login(nguoi_dung["leader_vd"])
    assert client.get(goc + "du-lieu/").status_code == 200
    assert _tu_choi(nguoi_dung["leader_vd"]) == []


@pytest.mark.parametrize("conf", [ERP, CRM])
def test_trang_403_co_nut_dang_xuat(client, settings, nguoi_dung, conf):
    """AC-3.6 — Trang 403 của KN ERP và KN CRM có nút Đăng xuất (form POST /dang-xuat/ kèm mã CSRF). Manager mất bộ phận
    bị từ chối ngay ở Tổng quan, nên đây là lối ra duy nhất vì /dang-nhap/ đẩy người đã đăng nhập về "/". Bấm Đăng xuất
    là về được trang đăng nhập (TL-106)"""
    _dich_vu(settings, conf)
    ql = _mat_bo_phan(nguoi_dung["manager_sale"])
    client.force_login(ql)
    html = client.get("/").content.decode()
    form = re.search(r'<form method="post" action="/dang-xuat/">(.*?)</form>', html, re.S)
    assert form and "csrfmiddlewaretoken" in form.group(1) and "Đăng xuất" in form.group(1), html[-1500:]
    r = client.post("/dang-xuat/")
    assert r.status_code == 302 and r.url == "/dang-nhap/"
