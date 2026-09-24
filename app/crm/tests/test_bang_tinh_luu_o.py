"""Lưu nhiều ô một lần trên Bảng tính — dán, kéo tay điền, xoá nội dung, hoàn
tác (`docs/04` AC-11.19, ADR-011).

Một đường dẫn `luu-o/` được cả hoặc không gì; quyền kiểm từng dòng ở máy chủ,
cả chiều cho phép lẫn chiều từ chối.
"""
import uuid
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
        # KN CRM chỉ phục vụ bảng vận đơn (ADR-040) — bảng đạo cụ mang workflow
        # để lưới phục vụ; cột tuỳ ý nên profile vận đơn không đổi hành vi bài
        workflow="waybill",
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
    # Bảng vận đơn duy nhất mang profile (ADR-036): đủ cột bắt buộc, tiền theo quốc gia.
    mac_dinh = {"ma_don": f"DH-{len(gia_tri)}-{gia_tri.get('ten_khach', 'x')}", "ngay": "2026-08-01",
                "ten_khach": "Khách", "so_dien_thoai": "0900", "quoc_gia": "Hoa Kỳ", "loai_tien": "USD"}
    return record_service.create_record(bang, {**mac_dinh, **gia_tri}, actor=nguoi)


def _goi(*cap):
    """Gói tham số `o` và `gt` ghép theo chỉ số từ các cặp `(khoá, mã cột, giá trị)`."""
    return {"o": [f"{k}:{ma}" for k, ma, _ in cap], "gt": [gt for _, _, gt in cap]}


def _luu(client, bang, *cap):
    cells=[]
    for pk,code,value in cap:
        temporary=isinstance(pk,str)
        pk=-int(pk.split('-')[-1]) if temporary else pk
        old=None if temporary else DataRecord.objects.get(pk=pk).data.get(code)
        cells.append({'id':pk,'column':code,'old':old,'value':value})
    return client.post(f'/bang-tinh/{bang.code}/luu-json/',{'operation':str(uuid.uuid4()),'cells':cells},content_type='application/json')



# ══ Dán được cả hoặc không gì — AC-11.19 ═══════════════════════════

def test_dan_nhieu_o_luu_mot_giao_dich_va_tu_choi_dong_nhap(client,bang_sale,nguoi_dung):
    # Bảng đạo cụ mang workflow vận đơn (ADR-040): dán nhiều ô trên dòng có sẵn
    # vẫn một giao dịch; dòng nháp bị từ chối vì dòng vận đơn chỉ sinh từ Lên đơn
    # (`protect_table`) — kiểm cả chiều bị từ chối (quy tắc 3)
    # `so_luong` trùng mã cột chuẩn nên bị profile khoá trên lưới — dán vào
    # `khach`/`doanh_thu` (mã riêng của bảng đạo cụ)
    nv=nguoi_dung['staff_sale_1'];d=_dong(bang_sale,nv,khach='A',doanh_thu='100',so_luong='2');client.force_login(nv)
    response=_luu(client,bang_sale,(d.pk,'khach','B'),(d.pk,'doanh_thu','200'))
    assert response.status_code==200,response.content
    d.refresh_from_db();assert d.data['khach']=='B' and d.data['gia_dv']=='100.00'
    tu_choi=_luu(client,bang_sale,(d.pk,'khach','C'),('moi-1','khach','Mới'))
    assert tu_choi.status_code==403
    d.refresh_from_db();assert d.data['khach']=='B' and DataRecord.objects.filter(table=bang_sale).count()==1


def test_mot_o_sai_thi_khong_o_nao_doi(client,bang_sale,nguoi_dung):
    nv=nguoi_dung['staff_sale_1'];d=_dong(bang_sale,nv,khach='A',doanh_thu='100',so_luong='2');client.force_login(nv)
    # `doanh_thu` là cột không bị profile khoá — lỗi trả về đúng là sai kiểu dữ liệu
    response=_luu(client,bang_sale,(d.pk,'khach','Không'),(d.pk,'doanh_thu','abc'))
    assert response.status_code==400 and response.json()['cell']=={'id':d.pk,'column':'doanh_thu'}
    d.refresh_from_db();assert d.data['khach']=='A' and DataRecord.objects.filter(table=bang_sale).count()==1


def test_bo_qua_cot_tinh_san_cot_la_va_gioi_han(client,bang_sale,nguoi_dung):
    nv=nguoi_dung['staff_sale_1'];d=_dong(bang_sale,nv,khach='A',doanh_thu='100',so_luong='2');client.force_login(nv)
    for code in ['gia_dv','khong_co']:
        assert _luu(client,bang_sale,(d.pk,'khach','Không'),(d.pk,code,'10')).status_code==400
        d.refresh_from_db();assert d.data['khach']=='A'
    assert _luu(client,bang_sale,*[(d.pk,'khach','X')]*(GRID_PASTE_CELLS_MAX+1)).status_code==400


# ══ Phân quyền: cả chiều cho phép lẫn chiều từ chối — AC-11.19 ═════

def test_phan_quyen_luu_o_ba_cap_bac(client,bang_sale,bang_vd,nguoi_dung):
    nv=nguoi_dung['staff_sale_1'];d=_dong(bang_sale,nv,khach='A')
    for role,allowed in [('staff_sale_2',False),('staff_sale_1',True),('leader_sale_1',True),('manager_sale',True),('admin',True),('staff_mkt',False)]:
        client.force_login(nguoi_dung[role]);response=_luu(client,bang_sale,(d.pk,'khach',role))
        assert response.status_code==(200 if allowed else 403),(role,response.content)


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
