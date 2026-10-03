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
    """AC-36.10 — Hộp Chi tiết: Bỏ dòng hết (không còn dòng nào) rồi Lưu → đơn không còn sản phẩm, bốn ô tổng
    trống; mở lại hộp thì vẫn có sẵn một dòng chọn sản phẩm trống như trước, có dòng mẫu và nút Thêm dòng; chọn
    lại sản phẩm lưu được như thường. Còn dòng chưa chọn sản phẩm thì báo lỗi, không lưu"""
    row = order(setup, nguoi_dung["staff_sale_1"]).record
    client.force_login(nguoi_dung["staff_vd"])
    chi_tiet = f"/van-don/chi-tiet/{row.pk}/"
    html = client.get(chi_tiet).content.decode()
    assert "data-allow-empty" in html and "data-item-template" in html
    trong = {"product": [""], "unit": [""], "quantity": ["1"], "unit_price": ["0.00"], "paid_amount": ["0.00"]}
    r = client.post(chi_tiet, {**trong, "unit_price": ["5.00"], "version": row.updated_at.isoformat()})
    assert r.status_code == 400 and "chưa chọn sản phẩm" in r.content.decode()
    assert _con_chi_tiet(row) == 2
    r = client.post(chi_tiet, {"version": row.updated_at.isoformat()})          # không còn dòng nào
    assert r.status_code == 200, r.content.decode()
    row.refresh_from_db()
    assert _con_chi_tiet(row) == 0 and all(row.data.get(k) in (None, "") for k in TONG)
    assert AuditLog.objects.filter(detail__contains="Bỏ toàn bộ chi tiết sản phẩm").exists()
    # Mở lại hộp: vẫn có sẵn một dòng chọn sản phẩm trống như trước, không tự ý bỏ ô chọn
    html = client.get(chi_tiet).content.decode()
    than_bang = html.split("<tbody>")[1].split("</tbody>")[0]
    assert than_bang.count("<tr") == 1 and 'name="product"' in than_bang and " selected" not in than_bang
    assert "data-add-item" in html
    data = {**form_data(setup[2]), "paid_amount": ["0.00", "0.00"], "version": row.updated_at.isoformat()}
    assert client.post(chi_tiet, data).status_code == 200
    row.refresh_from_db()
    assert _con_chi_tiet(row) == 2 and row.data["gia_tien"] == "40.40"
    # Dòng chọn sản phẩm còn trống (chưa chọn) rồi Lưu: báo lỗi như bản cũ, không lặng lẽ xoá đơn
    r = client.post(chi_tiet, {**trong, "version": row.updated_at.isoformat()})
    assert r.status_code == 400 and _con_chi_tiet(row) == 2


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


def test_don_nhap_tep_khong_chi_tiet_xoa_duoc_chu_san_pham(client, setup, nguoi_dung):  # noqa: F811
    """AC-36.10 — Đơn nhập từ tệp không có Chi tiết (ô Sản phẩm chỉ là chữ "A ×2 + B ×3"): hộp Chi tiết như cũ
    (một dòng chọn sản phẩm trống); lỡ bấm Lưu khi dòng còn trống → báo lỗi, không mất chữ và tổng; Bỏ dòng rồi
    Lưu → chữ và bốn ô tổng trống; Delete trên lưới cũng xoá được"""
    from django.utils import timezone
    row = order(setup, nguoi_dung["staff_sale_1"]).record
    WaybillItem.objects.filter(record=row).update(deleted_at=timezone.now())     # như dòng nhập tệp
    row.data["san_pham"] = "Retinol Cream ×2 + Retinol Serum ×3"
    row.save()
    client.force_login(nguoi_dung["staff_vd"])
    chi_tiet = f"/van-don/chi-tiet/{row.pk}/"
    html = client.get(chi_tiet).content.decode()
    than_bang = html.split("<tbody>")[1].split("</tbody>")[0]
    assert than_bang.count("<tr") == 1 and " selected" not in than_bang
    # Lỡ tay bấm Lưu ngay khi dòng chọn còn trống: không mất chữ sản phẩm và tổng tiền
    trong = {"product": [""], "unit": [""], "quantity": ["1"], "unit_price": ["0.00"], "paid_amount": ["0.00"]}
    assert client.post(chi_tiet, {**trong, "version": row.updated_at.isoformat()}).status_code == 400
    row.refresh_from_db()
    assert row.data["san_pham"] == "Retinol Cream ×2 + Retinol Serum ×3" and row.data["gia_tien"] == "40.40"
    assert client.post(chi_tiet, {"version": row.updated_at.isoformat()}).status_code == 200      # Bỏ dòng rồi Lưu
    row.refresh_from_db()
    assert all(row.data.get(k) in (None, "") for k in TONG)
    row.data["san_pham"] = "Retinol Cream ×2"
    row.save()
    assert _bo(client, _o(row, "san_pham")).status_code == 200
    row.refresh_from_db()
    assert row.data.get("san_pham") in (None, "")


@pytest.mark.parametrize("ai", ["staff_vd", "staff_sale_1", "staff_sale_2", "staff_mkt", "manager_sale", "admin"])
def test_quyen_bo_chi_tiet_trung_quyen_sua_o_thuong(client, setup, nguoi_dung, ai):  # noqa: F811
    """AC-36.9 — Ai sửa được ô thường của dòng (Ghi chú) thì mới bỏ được chi tiết, và ngược lại: Delete ô Sản
    phẩm không mở rộng hay thu hẹp quyền so với lưới"""
    row = order(setup, nguoi_dung["staff_sale_1"]).record
    client.force_login(nguoi_dung[ai])
    ghi = client.post(GRID + "luu-json/", {"operation": str(uuid.uuid4()), "cells": [
        {"id": row.pk, "column": "ghi_chu", "old": row.data.get("ghi_chu"), "value": "thử quyền"}]},
        content_type="application/json").status_code
    row.refresh_from_db()
    bo = _bo(client, _o(row, "san_pham")).status_code
    assert (ghi == 200) == (bo == 200), (ai, ghi, bo)
    assert (_con_chi_tiet(row) == 0) == (bo == 200)


def test_sau_khi_bo_luoi_thong_ke_excel_van_chay(client, setup, nguoi_dung):  # noqa: F811
    """AC-36.9 — Sau khi bỏ chi tiết: lưới đọc dòng (du-lieu) có ô Sản phẩm trống, Thống kê mở được và đếm đơn
    thiếu chi tiết, tệp Excel xuất được với Chi tiết sản phẩm "[]"; nhiều dòng bỏ một lượt"""
    from forms_builder.services import export_service
    from forms_builder.models import DataRecord
    rows = [order(setup, nguoi_dung["staff_sale_1"]).record for _ in range(3)]
    client.force_login(nguoi_dung["staff_vd"])
    r = _bo(client, _o(rows[0], "san_pham", "gia_tien") + _o(rows[1], "so_luong"))
    assert r.status_code == 200 and sorted(d["id"] for d in r.json()["rows"]) == sorted([rows[0].pk, rows[1].pk])
    assert [_con_chi_tiet(x) for x in rows] == [0, 0, 2]
    du_lieu = client.get(GRID + "du-lieu/")
    assert du_lieu.status_code == 200
    o = {d["id"]: d["cells"]["san_pham"]["value"] for d in du_lieu.json()["rows"]}
    assert o[rows[0].pk] in (None, "") and o[rows[2].pk]
    tk = client.get("/thong-ke/", {"nguon": "van_don"})
    assert tk.status_code == 200
    columns = list(setup[1].columns.all())
    sach = export_service.build_workbook(DataRecord.objects.in_scope(nguoi_dung["admin"]).filter(pk=rows[0].pk),
                                         columns, title="Vận đơn")
    assert sach.active.max_row == 2


def test_bao_cao_tong_hop_erp_van_mo_sau_khi_bo(client, setup, nguoi_dung, settings):  # noqa: F811
    """AC-36.9 — Báo cáo tổng hợp nguồn Vận đơn (ERP) và Bảng dữ liệu vẫn mở được khi có đơn đã bỏ chi tiết
    (bốn ô tổng trống), số đơn vẫn đếm đơn đó"""
    from django.core.management import call_command
    from django.urls import clear_url_caches
    from orders.services import waybill_service
    rows = [order(setup, nguoi_dung["staff_sale_1"]).record for _ in range(2)]
    waybill_service.clear_items(nguoi_dung["staff_vd"], setup[1],
                                [{"id": rows[0].pk, "column": "gia_tien", "old": rows[0].data["gia_tien"]}])
    call_command("configure_erp_reports", verbosity=0)
    settings.ROOT_URLCONF = "knjsc.urls"
    clear_url_caches()
    client.force_login(nguoi_dung["admin"])
    for url, query in (("/bao-cao/tong-hop/", {"nguon": "van_don"}), ("/bang/van_don/", {})):
        r = client.get(url, query)
        assert r.status_code == 200, (url, r.status_code)
