"""Chữ Việt gõ từ máy nào cũng lưu và tìm như nhau — AC-9.6 (săn lỗi 06.10.2026).

macOS và một số bộ gõ gửi chữ Việt dạng **tổ hợp** (NFD: "e" + dấu rời), Windows/Unikey gửi dạng **dựng sẵn** (NFC).
Nhìn giống hệt nhau nhưng máy so là khác: đo trên hệ thống thật, tên khách gõ từ Mac thì người dùng Windows tìm
"Ngọc Ánh" ra 0 kết quả. Nay mọi chữ người dùng gửi lên (form, JSON của lưới, tham số tìm kiếm, ô của tệp nhập) chuẩn
hoá về NFC ngay ở cửa vào (`core.middleware.UnicodeNFCMiddleware`, `core.excel`); ô mật khẩu giữ nguyên.
"""
import json
import unicodedata

import pytest

from core import excel
from forms_builder.models import DataRecord

from .test_waybill_new import form_data, setup  # noqa: F401 — fixture `setup` dùng chung

pytestmark = pytest.mark.django_db

NFC = "Trần Thị Ngọc Ánh"
NFD = unicodedata.normalize("NFD", NFC)


def test_len_don_ten_go_tu_mac_luu_dang_chuan(client, setup, nguoi_dung):  # noqa: F811
    """AC-9.6 — Lên đơn với tên khách dạng tổ hợp (gõ từ Mac): lưu dạng dựng sẵn, nên tìm bằng chữ gõ từ Windows ra đúng dòng"""
    assert NFD != NFC
    client.force_login(nguoi_dung["staff_sale_1"])
    client.post("/van-don/len-don/", {**form_data(setup[2]), "customer_name": NFD})
    assert DataRecord.objects.filter(data__ten_khach=NFC).count() == 1
    assert DataRecord.objects.filter(val_customer__icontains="Ngọc Ánh").count() == 1


def test_luu_o_luoi_va_tim_kiem_bang_chu_to_hop(client, setup, nguoi_dung, settings):  # noqa: F811
    """AC-9.6 — Lưới: ghi ô bằng JSON dạng tổ hợp lưu dạng dựng sẵn; tìm trong bảng bằng chữ tổ hợp vẫn ra dòng lưu dạng dựng sẵn"""
    from .test_waybill_new import order
    settings.GRID_ONLY_TABLES = set()
    dong = order(setup, nguoi_dung["staff_sale_1"]).record
    client.force_login(nguoi_dung["staff_vd"])
    meta = client.get(f"/bang-tinh/{setup[0].code}/du-lieu/?bat_dau=0").json()
    cu = dong.data.get("dia_chi")
    kq = client.post(f"/bang-tinh/{setup[0].code}/luu-json/", json.dumps({
        "operation": "6d24986b-8eed-4607-99e2-90fc32341f4d", "kind": "edit", "schema_version": meta.get("schema_version"),
        "cells": [{"id": dong.pk, "column": "dia_chi", "old": cu, "value": unicodedata.normalize("NFD", "Số 5 Đường Hoà Bình")}]}),
        content_type="application/json")
    assert kq.status_code == 200, kq.content[:300]
    dong.refresh_from_db()
    assert dong.data["dia_chi"] == "Số 5 Đường Hoà Bình"
    tim = client.get(f"/bang-tinh/{setup[0].code}/du-lieu/", {"q": unicodedata.normalize("NFD", "Hoà Bình"), "bat_dau": 0}).json()
    assert dong.pk in [r["id"] for r in tim.get("rows", [])]


def test_mat_khau_khong_bi_doi(client, nguoi_dung):
    """AC-9.6 — Ô mật khẩu không bị chuẩn hoá: mật khẩu có dấu đặt dạng nào thì đăng nhập đúng dạng đó"""
    from django.contrib.auth import get_user_model
    u = nguoi_dung["staff_sale_1"]
    u.set_password(NFD + "-9xX")
    u.save()
    kq = client.post("/dang-nhap/", {"username": u.username, "password": NFD + "-9xX"})
    assert kq.status_code == 302 and "/dang-nhap/" not in kq["Location"]
    del get_user_model


def test_o_tep_nhap_chuan_hoa():
    """AC-9.6 — Ô chữ trong tệp nhập (CSV và .xlsx) dạng tổ hợp được đọc ra dạng dựng sẵn"""
    import io
    from openpyxl import Workbook
    kq = excel.read_table(io.BytesIO(f"Tên\n{NFD}\n".encode()), "csv", max_rows=10)
    assert kq.rows[1][0] == NFC
    wb = Workbook()
    wb.active.append(["Tên"])
    wb.active.append([NFD])
    b = io.BytesIO()
    wb.save(b)
    b.seek(0)
    assert excel.read_table(b, "xlsx", max_rows=10).rows[1][0] == NFC
