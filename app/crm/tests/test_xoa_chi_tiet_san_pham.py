"""Delete xoá được ô Sản phẩm, Bỏ dòng xoá được dòng cuối — chủ dự án 02.10.2026.

"Cái t cần là ấn delete thì xoá được luôn ô sản phẩm + ấn bỏ dòng cũng xoá được." Bốn ô Sản phẩm, Số
lượng, Giá tiền, Số tiền thanh toán là tổng của Chi tiết sản phẩm nên không sửa riêng từng ô (AC-18.5);
xoá chúng nghĩa là **bỏ toàn bộ chi tiết** của dòng, cùng đường với hộp Chi tiết: đơn thành "thiếu chi
tiết" như dòng nhập tệp không chi tiết (ADR-036).
"""
import uuid

import pytest

from core.constants import Rank
from core.models import AuditLog
from crm.tests.test_waybill_new import ENTRY, GRID, form_data, order, setup  # noqa: F401
from forms_builder.models import GrantAction
from forms_builder.services import grant_service
from orders.models import WaybillAssignment, WaybillItem
from orders.services import waybill_service

pytestmark = pytest.mark.django_db
BO = GRID + "bo-chi-tiet/"
TONG = ("san_pham", "so_luong", "gia_tien", "so_tien_tt")


def _o(row, *codes):
    return [{"id": row.pk, "column": c, "old": row.data.get(c)} for c in codes]


def _bo(client, cells):
    return client.post(BO, {"operation": str(uuid.uuid4()), "cells": cells}, content_type="application/json")


def _con_chi_tiet(row):
    return WaybillItem.objects.filter(record=row, deleted_at__isnull=True).count()


@pytest.mark.parametrize("rank", [Rank.STAFF, Rank.LEADER, Rank.MANAGER])
def test_delete_o_tong_bo_toan_bo_chi_tiet(client, setup, nguoi_dung, make_user, departments, rank):  # noqa: F811
    """AC-36.9 — Vận đơn (Staff, Leader, Manager) bôi đen ô Sản phẩm hay Giá tiền rồi Delete: máy chủ bỏ
    toàn bộ Chi tiết sản phẩm của dòng (xoá mềm), bốn ô Sản phẩm, Số lượng, Giá tiền, Số tiền thanh toán
    cùng trống; Trạng thái thanh toán và ô khác giữ; có nhật ký; trả dòng mới cho lưới"""
    row = order(setup, nguoi_dung["staff_sale_1"]).record
    giu = {k: row.data.get(k) for k in ("ma_don", "ten_khach", "trang_thai_tt", "loai_tien")}
    client.force_login(make_user(f"vd_{rank}", rank, departments["vd"]))
    r = _bo(client, _o(row, "gia_tien"))           # chỉ một ô tổng cũng là bỏ cả chi tiết
    assert r.status_code == 200, r.content.decode()
    row.refresh_from_db()
    assert all(row.data.get(k) in (None, "") for k in TONG), {k: row.data.get(k) for k in TONG}
    assert {k: row.data.get(k) for k in giu} == giu
    assert _con_chi_tiet(row) == 0 and WaybillItem.objects.filter(record=row).count() == 2   # xoá mềm
    assert AuditLog.objects.filter(detail__contains="Bỏ toàn bộ chi tiết sản phẩm").exists()
    dong = r.json()["rows"]
    assert [d["id"] for d in dong] == [row.pk] and dong[0]["cells"]["san_pham"]["value"] in (None, "")


def test_khong_co_quyen_sua_thi_403_khong_doi(client, setup, nguoi_dung):  # noqa: F811
    """AC-36.9 — Chỉ được xem (cấp quyền Xem) hay ngoài phạm vi (Sale không được phân công) → 403, chi
    tiết và tổng giữ nguyên; chưa đăng nhập bị chuyển về trang đăng nhập"""
    row = order(setup, nguoi_dung["staff_sale_1"]).record
    truoc = dict(row.data)
    grant_service.grant(table=setup[1], user=nguoi_dung["staff_mkt"], action=GrantAction.VIEW,
                        actor=nguoi_dung["admin"])
    assert _bo(client, _o(row, "san_pham")).status_code == 302
    for ai in ("staff_mkt", "staff_sale_2"):
        client.force_login(nguoi_dung[ai])
        assert _bo(client, _o(row, "san_pham")).status_code in (403, 404), ai
    row.refresh_from_db()
    assert row.data == truoc and _con_chi_tiet(row) == 2


def test_o_vua_bi_doi_thi_409_va_o_thuong_bi_tu_choi(client, setup, nguoi_dung):  # noqa: F811
    """AC-36.9 — So phiên bản như ô thường: giá trị cũ gửi lên khác máy chủ → 409, không bỏ gì; gửi cột
    không phải ô tổng (Ghi chú) hay gói rỗng → 400"""
    row = order(setup, nguoi_dung["staff_sale_1"]).record
    client.force_login(nguoi_dung["staff_vd"])
    cu = [{"id": row.pk, "column": "san_pham", "old": "tên cũ khác"}]
    assert _bo(client, cu).status_code == 409
    assert _con_chi_tiet(row) == 2
    assert _bo(client, _o(row, "ghi_chu")).status_code == 400
    assert _bo(client, []).status_code == 400
    assert _con_chi_tiet(row) == 2


def test_cau_hinh_luoi_ghi_cot_tong_va_duong_bo(client, setup, nguoi_dung):  # noqa: F811
    """AC-36.9 — Lưới Vận đơn biết bốn cột tổng (`detailColumns`) và đường bỏ chi tiết (`clearDetailsUrl`)
    để hỏi lại trước khi bỏ"""
    client.force_login(nguoi_dung["staff_vd"])
    html = client.get(GRID).content.decode()
    assert "clearDetailsUrl" in html and BO in html
    assert all(f'"{c}"' in html for c in TONG)


def test_bo_dong_cuoi_luu_don_khong_san_pham(client, setup, nguoi_dung):  # noqa: F811
    """AC-36.10 — Hộp Chi tiết: bỏ hết dòng (còn một dòng trống chưa chọn sản phẩm) rồi Lưu → đơn không
    còn sản phẩm, bốn ô tổng trống; dòng trống mà có tiền thì báo lỗi, không lưu"""
    row = order(setup, nguoi_dung["staff_sale_1"]).record
    client.force_login(nguoi_dung["staff_vd"])
    chi_tiet = f"/van-don/chi-tiet/{row.pk}/"
    trong = {"product": [""], "unit": [""], "quantity": ["1"], "unit_price": ["0.00"], "paid_amount": ["0.00"]}
    co_tien = {**trong, "unit_price": ["5.00"], "version": row.updated_at.isoformat()}
    r = client.post(chi_tiet, co_tien)
    assert r.status_code == 400 and "chưa chọn sản phẩm" in r.content.decode()
    assert _con_chi_tiet(row) == 2
    r = client.post(chi_tiet, {**trong, "version": row.updated_at.isoformat()})
    assert r.status_code == 200, r.content.decode()
    row.refresh_from_db()
    assert _con_chi_tiet(row) == 0 and all(row.data.get(k) in (None, "") for k in TONG)
    assert AuditLog.objects.filter(detail__contains="Bỏ toàn bộ chi tiết sản phẩm").exists()
    # Mở lại hộp: một dòng trống để chọn lại sản phẩm, lưu lại được như thường
    html = client.get(chi_tiet).content.decode()
    assert html.count('name="product"') == 1 and "data-add-item" in html
    row.refresh_from_db()
    data = {**form_data(setup[2]), "paid_amount": ["0.00", "0.00"], "version": row.updated_at.isoformat()}
    assert client.post(chi_tiet, data).status_code == 200
    row.refresh_from_db()
    assert _con_chi_tiet(row) == 2 and row.data["gia_tien"] == "40.40"


def test_len_don_van_can_mot_san_pham(client, setup, nguoi_dung):  # noqa: F811
    """AC-36.10 — Lên đơn mới vẫn phải có ít nhất một sản phẩm; chỉ đơn đã có mới được bỏ hết chi tiết"""
    client.force_login(nguoi_dung["staff_sale_1"])
    data = {**form_data(setup[2]), "product": [""], "quantity": ["1"], "unit_price": ["0.00"]}
    r = client.post(ENTRY, data)
    assert r.status_code == 400 and "ít nhất 1 sản phẩm" in r.content.decode()


def test_dich_vu_bo_chi_tiet_rong(setup, nguoi_dung):  # noqa: F811
    """AC-36.10 — `update_items` nhận danh sách rỗng: bỏ hết chi tiết, tổng trống, phân công giữ"""
    row = order(setup, nguoi_dung["staff_sale_1"]).record
    waybill_service.update_items(nguoi_dung["staff_vd"], row.pk, [], row.updated_at.isoformat())
    row.refresh_from_db()
    assert _con_chi_tiet(row) == 0 and all(row.data.get(k) in (None, "") for k in TONG)
    assert WaybillAssignment.objects.filter(record=row, delivery__isnull=False).exists()
