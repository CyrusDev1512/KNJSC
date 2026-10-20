"""Trang KN CRM do người A mở mà phiên hiện là người B — ADR-053 (sửa một điều khoản của ADR-030), TL-02, TL-18.

Trang lấy mã CSRF mới trong cookie lúc gửi (het-phien.js), nên đăng nhập lại rồi bấm Thử lại/Lưu là lưu được. Đổi lại,
mọi fetch và htmx của trang mang mã người mở trang (`X-KNJSC-User`); người đang đăng nhập khác người đó thì máy chủ trả
409 `nguoi_dung_doi` trước mọi view (`core.middleware.PageOwnerMiddleware`): nháp của A không ghi dưới tên B, trang của
A không đọc theo phạm vi của B. Mã CSRF lệch từ trang KN CRM trả 403 JSON `code: csrf` để trang giữ nháp và báo đúng;
form HTML thường vẫn nhận trang 403 của Django như ADR-030.
"""
import re
import time
import uuid

import pytest
from django.conf import settings
from django.test import Client

from core.middleware import NGUOI_DUNG_DOI, PHIEN_CSRF
from core.models import SubmissionReceipt
from crm.models import GridCellHistory, GridMutationReceipt
from forms_builder.models import ColumnDef, DataRecord
from orders.models import Order, PaymentDocument, Product, WaybillAssignment, WaybillItem

from .test_master_grid import BASE
from .test_payment_documents import create_document, image_upload
from .test_waybill_feedback import feedback  # noqa: F401  (fixture dùng lại)
from .test_waybill_new import ENTRY, form_data, setup  # noqa: F401  (fixture dùng lại)

pytestmark = pytest.mark.django_db

MAT_KHAU = "matkhau-kiem-thu-1"
TU_CHOI = {"error": NGUOI_DUNG_DOI, "code": "nguoi_dung_doi"}


def _ma(user):
    """Header mã người mở trang, như het-phien.js gắn vào mọi fetch và htmx cùng nguồn."""
    return {"HTTP_X_KNJSC_USER": str(user.pk)}


def _luu(client, row, value, column="ghi_chu", **extra):
    return client.post(BASE + "luu-json/", {"operation": str(uuid.uuid4()), "cells": [
        {"id": row.pk, "column": column, "old": row.data.get(column), "value": value}]},
        content_type="application/json", **extra)


@pytest.fixture
def chung_tu(settings, tmp_path):
    settings.STORAGE_DIR = tmp_path
    settings.PAYMENT_DOCUMENTS_ENABLED = True


def _anh_chup(rows):
    """Mọi thứ một lượt ghi từ trang lưới có thể đổi — so trước và sau để chắc view không chạy."""
    return {
        "dong": {r.pk: DataRecord.objects.get(pk=r.pk).data for r in rows},
        "chi_tiet": sorted(WaybillItem.objects.filter(deleted_at__isnull=True).values_list("pk", "quantity")),
        "phan_cong": sorted(WaybillAssignment.objects.values_list("record_id", "delivery_id", "care_id", "version")),
        "cot_an": sorted(ColumnDef.objects.filter(is_hidden=True).values_list("pk", flat=True)),
        "chung_tu": sorted(PaymentDocument.objects.values_list("pk", "reference", "deleted_at", "version")),
        "bien_nhan": GridMutationReceipt.objects.count(),
        "lich_su": GridCellHistory.objects.count(),
    }


def test_trang_nguoi_khac_luu_luoi_bi_409_khong_ghi_khong_gia_han(client, feedback, nguoi_dung):  # noqa: F811
    """AC-21.4 — ADR-053: lưu lưới từ trang do người khác mở (X-KNJSC-User lệch người đang đăng nhập) trả 409
    nguoi_dung_doi kèm lời cố định, không ghi ô, không biên nhận, không lịch sử, không gia hạn phiên người đang đăng
    nhập; đúng người mở trang thì lưu được"""
    vd, admin = nguoi_dung["staff_vd"], nguoi_dung["admin"]
    row = feedback[2][0]
    client.force_login(vd)
    phien = client.session
    moc = int(time.time()) - 120
    phien["last_seen_at"] = moc
    phien.save()
    truoc = _anh_chup(feedback[2])

    r = _luu(client, row, "Ghi dưới tên người khác", **_ma(admin))
    assert r.status_code == 409 and r.json() == TU_CHOI
    assert "no-cache" in r["Cache-Control"]
    assert _anh_chup(feedback[2]) == truoc
    assert client.session["last_seen_at"] == moc, "409 không được gia hạn phiên của người đang đăng nhập"

    r = _luu(client, row, "Đúng người mở trang", **_ma(vd))
    assert r.status_code == 200, r.content.decode()
    assert DataRecord.objects.get(pk=row.pk).data["ghi_chu"] == "Đúng người mở trang"


def _duong_luoi(client, ten, feedback, pk_chung_tu, ma, nguoi_nhan):  # noqa: F811
    """Gọi một đường của trang lưới với payload hợp lệ — không có chốt 409 thì view chạy và đổi dữ liệu."""
    _, products, rows = feedback
    row = DataRecord.objects.get(pk=rows[0].pk)
    if ten == "luu-json":
        return _luu(client, row, "X", **ma)
    if ten == "bo-chi-tiet":
        return client.post(BASE + "bo-chi-tiet/", {"operation": str(uuid.uuid4()), "cells": [
            {"id": row.pk, "column": "san_pham", "old": row.data.get("san_pham")}]},
            content_type="application/json", **ma)
    if ten == "phan-cong":
        return client.post("/van-don/phan-cong/", {"versions": {r.pk: 0 for r in rows},
            "changes": {"delivery": nguoi_nhan.pk}}, content_type="application/json", **ma)
    if ten == "chi-tiet":
        return client.post(f"/van-don/chi-tiet/{row.pk}/", {"product": [products[0].code], "quantity": ["3"],
            "unit_price": ["10.00"], "paid_amount": ["0.00"], "version": row.updated_at.isoformat()},
            HTTP_HX_REQUEST="true", **ma)
    if ten == "an-cot":
        return client.post(BASE + "an-cot/", {"cot": ["thanh_pho"], "an": "1"}, **ma)
    if ten == "quyen-dong":
        return client.post(BASE + "quyen-dong/", {"ids": [r.pk for r in rows]}, content_type="application/json", **ma)
    if ten == "du-lieu":
        return client.get(BASE + "du-lieu/", **ma)
    if ten == "moi-nhat":
        return client.get(BASE + "moi-nhat/", **ma)
    if ten == "loc":
        return client.get(BASE + "loc/ten_khach/", HTTP_HX_REQUEST="true", **ma)
    if ten == "chung-tu-sua":
        return client.post(f"/chung-tu-thanh-toan/{pk_chung_tu}/sua/", {"version": 1, "action": "edit",
            "reference": "DOI-TEN"}, **ma)
    if ten == "chung-tu-tao":
        return client.post("/chung-tu-thanh-toan/tao/", {"record": row.pk, "reference": "000999",
            "operation": str(uuid.uuid4()), "images": image_upload()}, **ma)
    raise AssertionError(ten)


@pytest.mark.parametrize("ten", ["luu-json", "bo-chi-tiet", "phan-cong", "chi-tiet", "an-cot", "quyen-dong",
                                 "du-lieu", "moi-nhat", "loc", "chung-tu-sua", "chung-tu-tao"])
def test_moi_duong_cua_luoi_tu_trang_nguoi_khac_bi_409_khong_doi_du_lieu(client, feedback, nguoi_dung, chung_tu,  # noqa: F811
                                                                       ten):
    """AC-21.4 — ADR-053: mọi đường đọc/ghi mà trang lưới gọi bằng fetch/htmx (lưu, bỏ chi tiết, phân công, chi tiết
    sản phẩm, ẩn cột, quyền dòng, khối dữ liệu, mốc mới nhất, hộp lọc, sửa và tạo chứng từ) gọi từ trang của người
    khác đều 409, dữ liệu không đổi"""
    admin, vd = nguoi_dung["admin"], nguoi_dung["staff_vd"]
    rows = feedback[2]
    client.force_login(admin)
    tao = create_document(client, rows[0])
    assert tao.status_code == 200, tao.content
    truoc = _anh_chup(rows)
    r = _duong_luoi(client, ten, feedback, tao.json()["id"], _ma(vd), vd)
    assert r.status_code == 409, (ten, r.status_code, r.content[:300])
    assert r.json() == TU_CHOI
    if r.wsgi_request.headers.get("HX-Request"):
        assert r["HX-Reswap"] == "none"
    assert _anh_chup(rows) == truoc, ten


@pytest.mark.parametrize("ten", ["luu-don", "tom-tat", "san-pham-moi", "kiem-khach"])
def test_len_don_tu_trang_nguoi_khac_bi_409_khong_ra_don(client, setup, nguoi_dung, ten):  # noqa: F811
    """AC-6.11 — ADR-053: Lên đơn từ trang do người khác mở (Lưu đơn, tóm tắt, tạo sản phẩm, tra khách) trả 409
    nguoi_dung_doi trước khi view chạy: không đơn, không biên nhận mã lần nộp, không sản phẩm mới"""
    client.force_login(nguoi_dung["leader_sale_1"])
    ma = _ma(nguoi_dung["staff_sale_1"])
    bien_nhan, san_pham = SubmissionReceipt.objects.count(), Product.objects.count()
    if ten == "luu-don":
        r = client.post(ENTRY, {**form_data(setup[2]), "ma_lan_nop": str(uuid.uuid4())}, HTTP_HX_REQUEST="true", **ma)
    elif ten == "tom-tat":
        r = client.post(ENTRY + "tom-tat/", form_data(setup[2]), **ma)
    elif ten == "san-pham-moi":
        r = client.post(ENTRY + "san-pham-moi/", {"nhan_moi": "Sản phẩm của người khác"}, HTTP_ACCEPT="application/json",
                        **ma)
    else:
        r = client.get(ENTRY + "kiem-khach/", {"phone": "0901234567"}, HTTP_HX_REQUEST="true", **ma)
    assert r.status_code == 409 and r.json() == TU_CHOI, (ten, r.status_code)
    if ten in ("luu-don", "kiem-khach"):
        assert r["HX-Reswap"] == "none"
    assert Order.objects.count() == 0
    assert SubmissionReceipt.objects.count() == bien_nhan and Product.objects.count() == san_pham


def test_ma_nguoi_mo_trang_rong_hay_sai_dang_bi_409_an_danh_ve_dang_nhap(client, feedback, nguoi_dung):  # noqa: F811
    """AC-21.4 — ADR-053: header mã người mở trang rỗng hay sai dạng bị coi là khác người (409); người chưa đăng nhập
    kèm header vẫn đi đường đăng nhập, không 409"""
    row = feedback[2][0]
    client.force_login(nguoi_dung["staff_vd"])
    for gia_tri in ("", "abc"):
        r = _luu(client, row, "X", HTTP_X_KNJSC_USER=gia_tri)
        assert r.status_code == 409 and r.json()["code"] == "nguoi_dung_doi", gia_tri
    assert DataRecord.objects.get(pk=row.pk).data.get("ghi_chu") != "X"

    client.logout()
    r = _luu(client, row, "X", **_ma(nguoi_dung["staff_vd"]))
    assert r.status_code == 302 and r["Location"].startswith("/dang-nhap/")
    r = client.get(BASE + "loc/ten_khach/", HTTP_HX_REQUEST="true", **_ma(nguoi_dung["staff_vd"]))
    assert r.status_code != 409
    dich = r["Location"] if r.status_code == 302 else r["HX-Redirect"]
    assert dich.startswith("/dang-nhap/")


def _dang_nhap(c, user):
    c.get("/dang-nhap/")
    r = c.post("/dang-nhap/", {"username": user.username, "password": MAT_KHAU,
                                "csrfmiddlewaretoken": c.cookies[settings.CSRF_COOKIE_NAME].value})
    assert r.status_code == 302 and "/dang-nhap/" not in r["Location"], r.content[:300]
    return c.cookies[settings.CSRF_COOKIE_NAME].value


def test_dang_nhap_lai_ma_csrf_moi_cung_nguoi_luu_duoc_nguoi_khac_409(feedback, nguoi_dung):  # noqa: F811
    """AC-21.4 — ADR-053 sửa ADR-030: sau đăng nhập lại, mã CSRF cũ của trang bị từ chối (403 JSON code csrf), mã mới
    trong cookie với đúng người lưu được, người khác đăng nhập thì 409 không ghi; form HTML thường mang mã cũ vẫn bị
    trang 403 của Django chặn"""
    vd, admin = nguoi_dung["staff_vd"], nguoi_dung["admin"]
    row = feedback[2][0]
    c = Client(enforce_csrf_checks=True)
    t1 = _dang_nhap(c, vd)
    assert c.post("/dang-xuat/", {"csrfmiddlewaretoken": t1}).status_code == 302
    t2 = _dang_nhap(c, vd)
    assert t2 != t1

    r = _luu(c, row, "Mã cũ", HTTP_X_CSRFTOKEN=t1, **_ma(vd))
    assert r.status_code == 403 and r.json() == {"error": PHIEN_CSRF, "code": "csrf"}
    assert DataRecord.objects.get(pk=row.pk).data.get("ghi_chu") != "Mã cũ"

    r = _luu(c, row, "Mã mới", HTTP_X_CSRFTOKEN=t2, **_ma(vd))
    assert r.status_code == 200, r.content.decode()
    row.refresh_from_db()
    assert row.data["ghi_chu"] == "Mã mới"

    assert c.post("/dang-xuat/", {"csrfmiddlewaretoken": t2}).status_code == 302
    t3 = _dang_nhap(c, admin)
    r = _luu(c, row, "Ghi dưới tên admin", HTTP_X_CSRFTOKEN=t3, **_ma(vd))
    assert r.status_code == 409 and r.json() == TU_CHOI
    assert DataRecord.objects.get(pk=row.pk).data["ghi_chu"] == "Mã mới"
    assert not GridMutationReceipt.objects.filter(actor=admin).exists()

    cot = ColumnDef.objects.get(table=feedback[0], code="thanh_pho")
    r = c.post(BASE + "an-cot/", {"cot": ["thanh_pho"], "an": "1", "csrfmiddlewaretoken": t2})
    assert r.status_code == 403 and "application/json" not in r["Content-Type"]
    cot.refresh_from_db()
    assert cot.is_hidden is False


def test_ma_bao_mat_lech_tu_trang_crm_tra_json_form_thuong_van_trang_403(feedback, nguoi_dung, chung_tu):  # noqa: F811
    """AC-21.4 — ADR-053: mã CSRF lệch từ fetch/htmx của trang KN CRM (mang mã người mở trang, dù thân là JSON, form hay
    FormData) hay từ thân JSON trả 403 JSON code csrf (lưới, chứng từ giữ nháp, báo đúng); form HTML thường và htmx không
    mang mã người mở trang (KN ERP) vẫn nhận trang 403 CSRF của Django như ADR-030; không ghi gì"""
    vd, admin = nguoi_dung["staff_vd"], nguoi_dung["admin"]
    row = feedback[2][0]
    sai = "x" * 32
    tao = Client()
    tao.force_login(admin)
    pk = create_document(tao, row).json()["id"]
    c = Client(enforce_csrf_checks=True)
    c.force_login(admin)
    assert c.get(BASE).status_code == 200
    ma = _ma(admin)
    truoc = _anh_chup(feedback[2])
    csrf = {"error": PHIEN_CSRF, "code": "csrf"}

    # Mang mã người mở trang: JSON (lưới), form urlencoded (ẩn cột), FormData (sửa chứng từ), htmx (Chi tiết)
    assert _luu(c, row, "X", HTTP_X_CSRFTOKEN=sai, **ma).json() == csrf
    r = c.post(BASE + "an-cot/", {"cot": ["thanh_pho"], "an": "1", "csrfmiddlewaretoken": sai}, **ma)
    assert r.status_code == 403 and r.json() == csrf
    r = c.post(f"/chung-tu-thanh-toan/{pk}/sua/", {"version": 1, "action": "edit", "reference": "DOI",
                                                  "csrfmiddlewaretoken": sai}, **ma)
    assert r.status_code == 403 and r.json() == csrf
    r = c.post(f"/van-don/chi-tiet/{row.pk}/", {"product": [], "csrfmiddlewaretoken": sai}, HTTP_HX_REQUEST="true", **ma)
    assert r.status_code == 403 and r.json() == csrf
    # Thân JSON không mang mã người mở trang (trang chưa nạp het-phien.js): vẫn JSON để lưới không coi là mất quyền
    r = _luu(c, row, "X", HTTP_X_CSRFTOKEN=sai)
    assert r.status_code == 403 and r.json() == csrf

    # Form HTML thường và htmx không mang mã người mở trang (KN ERP): trang 403 CSRF của Django, không JSON
    for r in (c.post(BASE + "an-cot/", {"cot": ["thanh_pho"], "an": "1", "csrfmiddlewaretoken": sai}),
              c.post(f"/van-don/chi-tiet/{row.pk}/", {"product": [], "csrfmiddlewaretoken": sai}, HTTP_HX_REQUEST="true")):
        assert r.status_code == 403 and "application/json" not in r["Content-Type"] and b"CSRF" in r.content
    assert _anh_chup(feedback[2]) == truoc


def _the_het_phien(html):
    the = re.search(r'<script src="[^"]*het-phien\.js\?v=\d+"[^>]*>', html)
    assert the, "khung KN CRM chưa nạp het-phien.js kèm số phiên bản"
    return the.group(0)


def test_khung_crm_nap_het_phien_kem_ma_nguoi_mo_trang(client, feedback, nguoi_dung, settings):  # noqa: F811
    """AC-21.4 — ADR-053: hai khung KN CRM nạp het-phien.js sau loi-mang.js và trước htmx/lưới, mang mã người mở trang,
    mã nhân sự, đường đăng nhập/đổi mật khẩu và tên cookie CSRF theo settings; cookie CSRF đọc được bằng JS;
    CSRF_FAILURE_VIEW trỏ core.views.csrf_failure"""
    from core.identity import employee_code

    vd = nguoi_dung["staff_vd"]
    client.force_login(vd)
    for duong in (BASE, "/"):
        html = client.get(duong).content.decode()
        the = _the_het_phien(html)
        for thuoc_tinh in (f'data-nguoi="{vd.pk}"', f'data-ma="{employee_code(vd)}"', 'data-dang-nhap="/dang-nhap/"',
                           'data-doi-mat-khau="/doi-mat-khau/"', f'data-csrf-cookie="{settings.CSRF_COOKIE_NAME}"'):
            assert thuoc_tinh in the, (duong, thuoc_tinh, the)
        thu_tu = [html.index("js/loi-mang.js"), html.index("js/het-phien.js"), html.index("js/htmx.min.js")]
        if duong == BASE:
            thu_tu.append(html.index("js/master-grid.js"))
        assert thu_tu == sorted(thu_tu), (duong, thu_tu)

    settings.CSRF_COOKIE_NAME = "knjsc_csrf_v2"
    assert 'data-csrf-cookie="knjsc_csrf_v2"' in _the_het_phien(client.get(BASE).content.decode())
    assert settings.CSRF_COOKIE_HTTPONLY is False
    assert settings.CSRF_FAILURE_VIEW == "core.views.csrf_failure"


def test_script_khung_crm_co_so_phien_ban(client, feedback, nguoi_dung, settings, chung_tu):  # noqa: F811
    """AC-10.11 — Script và CSS của Lên đơn và chứng từ mang số phiên bản ?v= như mọi tệp tĩnh khác: phát hành xong
    trình duyệt không chạy payments.js/order-entry.js cũ cạnh het-phien.js mới"""
    client.force_login(nguoi_dung["staff_sale_1"])
    html = client.get(ENTRY).content.decode()
    for tep in ("js/order-entry.js", "js/waybill.js", "css/waybill.css"):
        assert re.search(re.escape(tep) + r"\?v=\d+", html), tep

    client.force_login(nguoi_dung["admin"])
    for duong in (BASE, "/chung-tu-thanh-toan/"):
        html = client.get(duong).content.decode()
        for tep in ("js/payments.js", "css/payments.css"):
            assert re.search(re.escape(tep) + r"\?v=\d+", html), (duong, tep)
