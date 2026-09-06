"""Menu chuột phải của Bảng tính: xoá và khôi phục dòng, chèn và bỏ cột,
mốc mới nhất để tự cập nhật (`docs/04` AC-11.21, AC-11.22, AC-11.26 — ADR-011).

Mỗi đường dẫn kiểm cả ba cấp bậc, cả chiều cho phép lẫn chiều từ chối.
"""
import pytest
from django.test import override_settings

from core.constants import AuditAction
from core.models import AuditLog
from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, ComputeOp, DataRecord, TableDef
from forms_builder.services import record_service, table_service
from orders.services import dispatch_service

pytestmark = pytest.mark.django_db

SUA_DUOC = override_settings(GRID_ONLY_TABLES=set())


@pytest.fixture
def bang_sale(departments, nguoi_dung):
    bang = TableDef.objects.create(
        name="Đơn hàng Sale", code="don_sale",
        department=departments["sale"], created_by=nguoi_dung["manager_sale"],
    )
    cot = [
        ("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
        ("Khách hàng", "khach", FieldType.TEXT, Meaning.CUSTOMER),
        ("Doanh thu", "doanh_thu", FieldType.MONEY, Meaning.REVENUE),
        ("Số lượng", "so_luong", FieldType.INTEGER, ""),
    ]
    for i, (ten, ma, kieu, nhan) in enumerate(cot, start=1):
        ColumnDef.objects.create(table=bang, name=ten, code=ma, field_type=kieu, meaning=nhan,
                                 order=i, is_key=(ma == "khach"))
    ColumnDef.objects.create(
        table=bang, name="Giá đơn vị", code="gia_dv", field_type=FieldType.MONEY,
        order=5, is_computed=True, compute_op=ComputeOp.DIVIDE,
        compute_left="doanh_thu", compute_right="so_luong", compute_decimals=2,
    )
    return bang


@pytest.fixture
def bang_vd(departments, nguoi_dung):
    return dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])


def _dong(bang, nguoi, **gia_tri):
    return record_service.create_record(bang, gia_tri, actor=nguoi)


# ══ Xoá và khôi phục dòng — AC-11.21 ═══════════════════════════════

def test_xoa_dong_la_xoa_mem_va_khoi_phuc_duoc(client, bang_sale, nguoi_dung):
    """AC-11.21 — Xoá dòng từ menu chuột phải chỉ đánh dấu xoá (BR-4), có nhật ký; khôi phục trả lại đúng dòng dưới dạng `<tr>` để lưới đặt lại chỗ cũ, có nhật ký"""
    nv = nguoi_dung["staff_sale_1"]
    d1 = _dong(bang_sale, nv, khach="A", doanh_thu="10", so_luong="1")
    d2 = _dong(bang_sale, nv, khach="B", doanh_thu="10", so_luong="1")
    client.force_login(nv)
    kq = client.post(f"/bang-tinh/{bang_sale.code}/xoa-dong/", {"pk": [d1.pk, d2.pk]})
    assert kq.status_code == 200 and sorted(kq.json()["da_xoa"]) == sorted([d1.pk, d2.pk])
    assert DataRecord.objects.filter(table=bang_sale).count() == 0
    assert DataRecord.all_objects.filter(table=bang_sale, deleted_at__isnull=False).count() == 2
    assert AuditLog.objects.filter(action=AuditAction.DELETE).count() >= 2
    kq = client.post(f"/bang-tinh/{bang_sale.code}/khoi-phuc-dong/", {"pk": [d2.pk, d1.pk]})
    assert kq.status_code == 200
    html = kq.content.decode()
    assert html.index(f'data-dong="{d2.pk}"') < html.index(f'data-dong="{d1.pk}"')   # đúng thứ tự gửi lên
    assert DataRecord.objects.filter(table=bang_sale).count() == 2
    assert AuditLog.objects.filter(detail__startswith="Khôi phục dòng").count() == 2
    # Khôi phục lần nữa: dòng không còn bị xoá thì là ngoài phạm vi yêu cầu → 403
    assert client.post(f"/bang-tinh/{bang_sale.code}/khoi-phuc-dong/", {"pk": [d1.pk]}).status_code == 403
    assert client.post(f"/bang-tinh/{bang_sale.code}/xoa-dong/", {}).status_code == 400


def test_phan_quyen_xoa_dong_ba_cap_bac(client, bang_sale, bang_vd, nguoi_dung):
    """AC-11.21 — Staff chỉ xoá dòng của mình (dòng người khác 403 có nhật ký, cả gói không xoá), Leader không xoá dòng người khác, Manager và Admin cả bộ phận; bộ phận khác 404; bảng vận đơn chỉ xem ở dịch vụ chính 403"""
    nv, nv_b = nguoi_dung["staff_sale_1"], nguoi_dung["staff_sale_1b"]
    d_nv = _dong(bang_sale, nv, khach="A", doanh_thu="10", so_luong="1")
    d_b = _dong(bang_sale, nv_b, khach="B", doanh_thu="10", so_luong="1")
    client.force_login(nv)
    truoc = AuditLog.objects.filter(action=AuditAction.DENIED).count()
    assert client.post(f"/bang-tinh/{bang_sale.code}/xoa-dong/", {"pk": [d_nv.pk, d_b.pk]}).status_code == 403
    assert AuditLog.objects.filter(action=AuditAction.DENIED).count() == truoc + 1
    assert DataRecord.objects.filter(table=bang_sale).count() == 2          # cả gói không xoá
    client.force_login(nguoi_dung["leader_sale_1"])
    assert client.post(f"/bang-tinh/{bang_sale.code}/xoa-dong/", {"pk": [d_b.pk]}).status_code == 403
    client.force_login(nguoi_dung["staff_mkt"])
    assert client.post(f"/bang-tinh/{bang_sale.code}/xoa-dong/", {"pk": [d_b.pk]}).status_code == 404
    client.force_login(nguoi_dung["manager_sale"])
    assert client.post(f"/bang-tinh/{bang_sale.code}/xoa-dong/", {"pk": [d_b.pk]}).status_code == 200
    client.force_login(nguoi_dung["admin"])
    assert client.post(f"/bang-tinh/{bang_sale.code}/xoa-dong/", {"pk": [d_nv.pk]}).status_code == 200
    assert client.post(f"/bang-tinh/{bang_sale.code}/khoi-phuc-dong/", {"pk": [d_nv.pk, d_b.pk]}).status_code == 200

    vd = nguoi_dung["staff_vd"]
    d_vd = _dong(bang_vd, vd, ma_don="DH-1", ten_khach="K", so_dien_thoai="0911")
    client.force_login(vd)
    assert client.post(f"/bang-tinh/{bang_vd.code}/xoa-dong/", {"pk": [d_vd.pk]}).status_code == 403
    with SUA_DUOC:
        assert client.post(f"/bang-tinh/{bang_vd.code}/xoa-dong/", {"pk": [d_vd.pk]}).status_code == 200
    client.logout()
    kq = client.post(f"/bang-tinh/{bang_sale.code}/xoa-dong/", {"pk": [d_nv.pk]})
    assert kq.status_code == 302 and "/dang-nhap/" in kq["Location"]


# ══ Chèn và bỏ cột — AC-11.22 ══════════════════════════════════════

def test_manager_chen_cot_canh_cot_dang_chon(client, bang_sale, nguoi_dung):
    """AC-11.22 — Manager của bộ phận sở hữu chèn N cột chữ ngắn bên trái hoặc bên phải cột đang chọn; thứ tự cột đánh lại theo vị trí mới; tên và mã cột mới không trùng; có nhật ký"""
    client.force_login(nguoi_dung["manager_sale"])
    kq = client.post(f"/bang-tinh/{bang_sale.code}/them-cot/", {"canh": "khach", "ben": "phai", "so": 2})
    assert kq.status_code == 200 and kq.json()["da_them"] == ["cot_moi_1", "cot_moi_2"]
    thu_tu = list(bang_sale.columns.order_by("order", "id").values_list("code", flat=True))
    assert thu_tu == ["ngay", "khach", "cot_moi_1", "cot_moi_2", "doanh_thu", "so_luong", "gia_dv"]
    assert bang_sale.columns.get(code="cot_moi_1").name == "Cột mới 1"
    kq = client.post(f"/bang-tinh/{bang_sale.code}/them-cot/", {"canh": "ngay", "ben": "trai", "so": 1})
    assert kq.status_code == 200 and kq.json()["da_them"] == ["cot_moi_3"]
    assert list(bang_sale.columns.order_by("order", "id").values_list("code", flat=True))[0] == "cot_moi_3"
    kq = client.post(f"/bang-tinh/{bang_sale.code}/them-cot/", {"so": 1})           # không cột cạnh: chèn cuối
    assert kq.status_code == 200
    assert list(bang_sale.columns.order_by("order", "id").values_list("code", flat=True))[-1] == "cot_moi_4"
    assert client.post(f"/bang-tinh/{bang_sale.code}/them-cot/", {"canh": "khong_co", "so": 1}).status_code == 400
    assert AuditLog.objects.filter(detail__startswith="Chèn cột").count() == 4
    kq = client.get(f"/bang-tinh/{bang_sale.code}/")
    assert kq.status_code == 200 and 'data-cot="cot_moi_1"' in kq.content.decode()


def test_bo_cot_giu_gia_tri_va_tu_choi_cot_khoa_cot_tinh(client, bang_sale, bang_vd, nguoi_dung):
    """AC-11.22 — Bỏ cột xoá định nghĩa cột nhưng giữ giá trị trong bản ghi (BR-4); cột khoá, cột là vế của cột tính sẵn và cột hệ thống của bảng vận đơn bị từ chối"""
    nv = nguoi_dung["manager_sale"]
    d = _dong(bang_sale, nv, khach="A", doanh_thu="10", so_luong="2", ngay="2026-01-01")
    client.force_login(nv)
    kq = client.post(f"/bang-tinh/{bang_sale.code}/xoa-cot/", {"cot": ["ngay"]})
    assert kq.status_code == 200 and kq.json()["da_bo"] == ["ngay"]
    assert not bang_sale.columns.filter(code="ngay").exists()
    d.refresh_from_db()
    assert d.data["ngay"] == "2026-01-01"                                    # giá trị vẫn còn
    assert client.post(f"/bang-tinh/{bang_sale.code}/xoa-cot/", {"cot": ["khach"]}).status_code == 400
    kq = client.post(f"/bang-tinh/{bang_sale.code}/xoa-cot/", {"cot": ["so_luong"]})
    assert kq.status_code == 400 and "cột tính sẵn" in kq.content.decode()
    assert client.post(f"/bang-tinh/{bang_sale.code}/xoa-cot/", {"cot": ["khong_co"]}).status_code == 400
    assert client.post(f"/bang-tinh/{bang_sale.code}/xoa-cot/", {}).status_code == 400
    assert bang_sale.columns.count() == 4
    client.force_login(nguoi_dung["admin"])
    kq = client.post(f"/bang-tinh/{bang_vd.code}/xoa-cot/", {"cot": ["ten_khach"]})
    assert kq.status_code == 400 and "tệp vận đơn" in kq.content.decode()


def test_phan_quyen_chen_bo_cot_ba_cap_bac(client, bang_sale, nguoi_dung):
    """AC-11.22 — Staff và Leader không chèn hay bỏ cột (403 có nhật ký); Manager bộ phận khác 404; Manager của bộ phận sở hữu và Admin thì được"""
    truoc = AuditLog.objects.filter(action=AuditAction.DENIED).count()
    for ai in ("staff_sale_1", "leader_sale_1"):
        client.force_login(nguoi_dung[ai])
        assert client.post(f"/bang-tinh/{bang_sale.code}/them-cot/", {"canh": "khach", "so": 1}).status_code == 403
        assert client.post(f"/bang-tinh/{bang_sale.code}/xoa-cot/", {"cot": ["so_luong"]}).status_code == 403
    assert AuditLog.objects.filter(action=AuditAction.DENIED).count() == truoc + 4
    client.force_login(nguoi_dung["manager_mkt"])
    assert client.post(f"/bang-tinh/{bang_sale.code}/them-cot/", {"so": 1}).status_code == 404
    client.force_login(nguoi_dung["admin"])
    assert client.post(f"/bang-tinh/{bang_sale.code}/them-cot/", {"canh": "khach", "so": 1}).status_code == 200
    assert bang_sale.columns.filter(code="cot_moi_1").exists()
    assert client.post(f"/bang-tinh/{bang_sale.code}/xoa-cot/", {"cot": ["cot_moi_1"]}).status_code == 200
    assert not bang_sale.columns.filter(code="cot_moi_1").exists()


def test_insert_columns_dich_vu(bang_sale, nguoi_dung):
    """AC-11.22 — Dịch vụ `insert_columns` đánh lại `order` liên tục và không đụng cột đã có; `removable_reason` nêu lý do giữ cột"""
    moi = table_service.insert_columns(bang_sale, count=2, anchor="doanh_thu", after=False, actor=nguoi_dung["manager_sale"])
    assert [c.code for c in moi] == ["cot_moi_1", "cot_moi_2"]
    assert list(bang_sale.columns.order_by("order").values_list("order", flat=True)) == [1, 2, 3, 4, 5, 6, 7]
    assert list(bang_sale.columns.order_by("order").values_list("code", flat=True))[2:4] == ["cot_moi_1", "cot_moi_2"]
    assert table_service.removable_reason(bang_sale.columns.get(code="khach"))
    assert "cột tính sẵn" in table_service.removable_reason(bang_sale.columns.get(code="doanh_thu"))
    assert table_service.removable_reason(bang_sale.columns.get(code="cot_moi_1")) == ""


# ══ Mốc mới nhất để tự cập nhật — AC-11.26 ════════════════════════

def test_moi_nhat_tra_moc_trong_pham_vi(client, bang_sale, nguoi_dung):
    """AC-11.26 — `moi-nhat/` trả mốc sửa gần nhất, số dòng và số cột **trong phạm vi người xem**, không có dữ liệu; đổi ô thì mốc đổi; bộ phận khác 404; chưa đăng nhập thì chuyển về đăng nhập"""
    nv, nv_b = nguoi_dung["staff_sale_1"], nguoi_dung["staff_sale_1b"]
    d1 = _dong(bang_sale, nv, khach="A", doanh_thu="10", so_luong="1")
    _dong(bang_sale, nv_b, khach="B", doanh_thu="10", so_luong="1")
    client.force_login(nv)
    kq = client.get(f"/bang-tinh/{bang_sale.code}/moi-nhat/")
    assert kq.status_code == 200
    d = kq.json()
    assert d["so"] == 1 and d["cot"] == 5 and d["moc"] and "A" not in kq.content.decode()
    record_service.update_cell(d1, "khach", "A2", actor=nv)
    assert client.get(f"/bang-tinh/{bang_sale.code}/moi-nhat/").json()["moc"] >= d["moc"]
    client.force_login(nguoi_dung["manager_sale"])
    assert client.get(f"/bang-tinh/{bang_sale.code}/moi-nhat/").json()["so"] == 2
    client.force_login(nguoi_dung["staff_mkt"])
    assert client.get(f"/bang-tinh/{bang_sale.code}/moi-nhat/").status_code == 404
    client.logout()
    assert client.get(f"/bang-tinh/{bang_sale.code}/moi-nhat/").status_code == 302
