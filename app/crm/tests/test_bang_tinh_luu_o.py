"""Lưu nhiều ô một lần trên Bảng tính — dán, kéo tay điền, xoá nội dung, hoàn
tác (`docs/04` AC-11.19, ADR-011).

Một đường dẫn `luu-o/` được cả hoặc không gì; quyền kiểm từng dòng ở máy chủ,
cả chiều cho phép lẫn chiều từ chối.
"""
import pytest
from django.test import override_settings

from core.constants import GRID_PASTE_CELLS_MAX, AuditAction
from core.models import AuditLog
from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, ComputeOp, DataRecord, TableDef
from forms_builder.services import record_service
from orders.services import dispatch_service

pytestmark = pytest.mark.django_db

SUA_DUOC = override_settings(GRID_ONLY_TABLES=set())    # đúng cấu hình dịch vụ bangtinh


@pytest.fixture
def bang_sale(departments, nguoi_dung):
    """Bảng của Sale: khách bắt buộc, số lượng nguyên, doanh thu tiền, một cột tính sẵn."""
    bang = TableDef.objects.create(
        name="Đơn hàng Sale", code="don_sale",
        department=departments["sale"], created_by=nguoi_dung["manager_sale"],
    )
    cot = [
        ("Ngày", "ngay", FieldType.DATE, Meaning.DATE, False),
        ("Khách hàng", "khach", FieldType.TEXT, Meaning.CUSTOMER, True),
        ("Doanh thu", "doanh_thu", FieldType.MONEY, Meaning.REVENUE, False),
        ("Số lượng", "so_luong", FieldType.INTEGER, "", False),
    ]
    for i, (ten, ma, kieu, nhan, bat_buoc) in enumerate(cot):
        ColumnDef.objects.create(table=bang, name=ten, code=ma, field_type=kieu, meaning=nhan,
                                 order=i, required=bat_buoc)
    ColumnDef.objects.create(
        table=bang, name="Giá đơn vị", code="gia_dv", field_type=FieldType.MONEY,
        order=4, is_computed=True, compute_op=ComputeOp.DIVIDE,
        compute_left="doanh_thu", compute_right="so_luong", compute_decimals=2,
    )
    return bang


@pytest.fixture
def bang_vd(departments, nguoi_dung):
    return dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])


def _dong(bang, nguoi, **gia_tri):
    return record_service.create_record(bang, gia_tri, actor=nguoi)


def _goi(*cap):
    """Gói tham số `o` và `gt` ghép theo chỉ số từ các cặp `(khoá, mã cột, giá trị)`."""
    return {"o": [f"{k}:{ma}" for k, ma, _ in cap], "gt": [gt for _, _, gt in cap]}


def _luu(client, bang, *cap):
    return client.post(f"/bang-tinh/{bang.code}/luu-o/", _goi(*cap))


# ══ Dán được cả hoặc không gì — AC-11.19 ═══════════════════════════

def test_dan_nhieu_o_luu_mot_giao_dich_va_tao_dong_moi(client, bang_sale, nguoi_dung):
    """AC-11.19 — Dán vào nhiều ô của nhiều dòng lưu một lần; ô tràn xuống dòng trống thành bản ghi mới thuộc bộ phận sở hữu bảng; cột tính sẵn tính lại; một dòng nhật ký gộp; trả về ô và dòng vẽ lại tại chỗ"""
    nv = nguoi_dung["staff_sale_1"]
    d1 = _dong(bang_sale, nv, khach="A", doanh_thu="100", so_luong="2")
    d2 = _dong(bang_sale, nv, khach="B", doanh_thu="300", so_luong="3")
    client.force_login(nv)
    truoc = AuditLog.objects.count()
    kq = _luu(
        client, bang_sale,
        (d1.pk, "khach", "An"), (d1.pk, "so_luong", "4"), (d2.pk, "doanh_thu", "900"),
        ("moi-7", "khach", "Mới"), ("moi-7", "doanh_thu", "50"), ("moi-7", "so_luong", "5"),
        ("moi-8", "khach", "   "),                     # dòng dán toàn ô trống: không tạo
    )
    assert kq.status_code == 200, kq.content[:300]
    d1.refresh_from_db(); d2.refresh_from_db()
    assert d1.data["khach"] == "An" and d1.data["so_luong"] == 4 and d1.data["gia_dv"] == "25.00"
    assert d2.data["doanh_thu"] == "900" and d2.data["gia_dv"] == "300.00"
    moi = DataRecord.objects.filter(table=bang_sale).exclude(pk__in=[d1.pk, d2.pk])
    assert moi.count() == 1
    assert moi.get().data["khach"] == "Mới" and moi.get().department_id == bang_sale.department_id
    html = kq.content.decode()
    assert f'id="o-{d1.pk}-khach"' in html and 'hx-swap-oob="outerHTML"' in html
    assert f'id="o-{d1.pk}-gia_dv"' in html            # cột tính sẵn của dòng đã đổi cũng vẽ lại
    assert 'id="dong-moi-7"' in html and 'data-dong="%d"' % moi.get().pk in html
    assert html.index('id="dong-moi-7"') < html.index(f'id="o-{d1.pk}-khach"')   # dòng trước ô, không thì trình duyệt bỏ <tr>
    nhat_ky = list(AuditLog.objects.order_by("pk")[truoc:])
    assert [n.action for n in nhat_ky] == [AuditAction.UPDATE, AuditAction.CREATE]
    assert "Sửa 3 ô trên 2 dòng" in nhat_ky[0].detail


def test_mot_o_sai_thi_khong_o_nao_doi(client, bang_sale, nguoi_dung):
    """AC-11.19 — Một ô trong gói sai kiểu hay để trống cột bắt buộc thì 400 nêu đúng ô, và không ô nào trong gói được lưu"""
    nv = nguoi_dung["staff_sale_1"]
    d1 = _dong(bang_sale, nv, khach="A", doanh_thu="100", so_luong="2")
    client.force_login(nv)
    kq = _luu(client, bang_sale, (d1.pk, "khach", "An"), (d1.pk, "so_luong", "abc"))
    assert kq.status_code == 400
    assert f'data-o="{d1.pk}:so_luong"' in kq.content.decode()
    d1.refresh_from_db()
    assert d1.data["khach"] == "A" and d1.data["so_luong"] == 2
    kq = _luu(client, bang_sale, (d1.pk, "khach", ""), ("moi-9", "khach", "X"))
    assert kq.status_code == 400 and "bắt buộc" in kq.content.decode()
    assert DataRecord.objects.filter(table=bang_sale).count() == 1
    kq = _luu(client, bang_sale, ("moi-9", "doanh_thu", "5"))    # dòng mới thiếu cột bắt buộc
    assert kq.status_code == 400 and 'data-o="moi-9:' in kq.content.decode()
    assert DataRecord.objects.filter(table=bang_sale).count() == 1


def test_bo_qua_cot_tinh_san_cot_la_va_gioi_han(client, bang_sale, nguoi_dung):
    """AC-11.19 — Cột tính sẵn và cột lạ bị bỏ qua; chỉ có chúng thì 400; quá trần ô hay thiếu giá trị thì 400; dòng đã xoá hay ngoài phạm vi thì 403 có nhật ký"""
    nv = nguoi_dung["staff_sale_1"]
    d1 = _dong(bang_sale, nv, khach="A", doanh_thu="100", so_luong="2")
    client.force_login(nv)
    assert _luu(client, bang_sale, (d1.pk, "gia_dv", "1"), (d1.pk, "khong_co", "1")).status_code == 400
    kq = _luu(client, bang_sale, (d1.pk, "gia_dv", "1"), (d1.pk, "khach", "B"))
    assert kq.status_code == 200
    d1.refresh_from_db()
    assert d1.data["khach"] == "B" and d1.data["gia_dv"] == "50.00"
    qua = [(d1.pk, "khach", "x")] * (GRID_PASTE_CELLS_MAX + 1)
    assert _luu(client, bang_sale, *qua).status_code == 400
    assert client.post(f"/bang-tinh/{bang_sale.code}/luu-o/", {"o": [f"{d1.pk}:khach"]}).status_code == 400
    assert client.post(f"/bang-tinh/{bang_sale.code}/luu-o/", {}).status_code == 400
    truoc = AuditLog.objects.filter(action=AuditAction.DENIED).count()
    assert _luu(client, bang_sale, (d1.pk + 999, "khach", "x")).status_code == 403
    assert AuditLog.objects.filter(action=AuditAction.DENIED).count() == truoc + 1


# ══ Phân quyền: cả chiều cho phép lẫn chiều từ chối — AC-11.19 ═════

def test_phan_quyen_luu_o_ba_cap_bac(client, bang_sale, bang_vd, nguoi_dung):
    """AC-11.19 — Staff chỉ dán vào dòng của mình (dòng người khác 403 có nhật ký), Leader không sửa dòng người khác, Manager và Admin cả bộ phận; bộ phận khác 404; bảng vận đơn chỉ xem ở dịch vụ chính 403, ở dịch vụ bangtinh thì được"""
    nv, nv_b = nguoi_dung["staff_sale_1"], nguoi_dung["staff_sale_1b"]
    d_nv = _dong(bang_sale, nv, khach="A", doanh_thu="100", so_luong="2")
    d_b = _dong(bang_sale, nv_b, khach="B", doanh_thu="100", so_luong="2")

    client.force_login(nv)
    assert _luu(client, bang_sale, (d_nv.pk, "khach", "A2")).status_code == 200
    truoc = AuditLog.objects.filter(action=AuditAction.DENIED).count()
    assert _luu(client, bang_sale, (d_nv.pk, "khach", "A3"), (d_b.pk, "khach", "B2")).status_code == 403
    assert AuditLog.objects.filter(action=AuditAction.DENIED).count() == truoc + 1
    d_nv.refresh_from_db(); d_b.refresh_from_db()
    assert d_nv.data["khach"] == "A2" and d_b.data["khach"] == "B"   # cả gói không đổi

    client.force_login(nguoi_dung["leader_sale_1"])
    assert _luu(client, bang_sale, (d_b.pk, "khach", "B3")).status_code == 403
    client.force_login(nguoi_dung["manager_sale"])
    assert _luu(client, bang_sale, (d_b.pk, "khach", "B3"), ("moi-5", "khach", "Q")).status_code == 200
    client.force_login(nguoi_dung["admin"])
    assert _luu(client, bang_sale, (d_nv.pk, "khach", "A4")).status_code == 200
    client.force_login(nguoi_dung["staff_mkt"])
    assert _luu(client, bang_sale, (d_nv.pk, "khach", "A5")).status_code == 404

    # Bảng vận đơn: chỉ xem ở dịch vụ chính, sửa ở dịch vụ bangtinh (ADR-009)
    vd = nguoi_dung["staff_vd"]
    d_vd = _dong(bang_vd, vd, ma_don="DH-1", ten_khach="K", so_dien_thoai="0911")
    client.force_login(vd)
    assert _luu(client, bang_vd, (d_vd.pk, "ten_khach", "K2")).status_code == 403
    with SUA_DUOC:
        assert _luu(client, bang_vd, (d_vd.pk, "ten_khach", "K2"), ("moi-3", "ma_don", "DH-2")).status_code == 200
    assert DataRecord.objects.filter(table=bang_vd, data__ma_don="DH-2").exists()

    client.logout()
    kq = _luu(client, bang_sale, (d_nv.pk, "khach", "x"))
    assert kq.status_code == 302 and "/dang-nhap/" in kq["Location"]


def test_update_cells_dich_vu_mot_giao_dich(bang_sale, nguoi_dung):
    """AC-11.19 — Dịch vụ `update_cells`: ô không đổi không tính, ô sai ném `CellError` mang dòng và cột, và không dòng nào được lưu"""
    nv = nguoi_dung["staff_sale_1"]
    d1 = _dong(bang_sale, nv, khach="A", doanh_thu="100", so_luong="2")
    d2 = _dong(bang_sale, nv, khach="B", doanh_thu="100", so_luong="2")
    cot = list(bang_sale.columns.all())
    assert record_service.update_cells([(d1, "khach", "A")], actor=nv, columns=cot) == 0
    with pytest.raises(record_service.CellError) as loi:
        record_service.update_cells(
            [(d1, "khach", "A1"), (d2, "so_luong", "x")], actor=nv, columns=cot,
        )
    assert loi.value.pk == d2.pk and loi.value.column == "so_luong"
    d1.refresh_from_db()
    assert d1.data["khach"] == "A"
    assert record_service.update_cells([(d1, "khach", "A1"), (d2, "khach", "B1")], actor=nv, columns=cot) == 2
