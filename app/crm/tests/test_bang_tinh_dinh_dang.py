"""Định dạng ô trên Bảng tính — `docs/04` mục 11, ADR-010 (Giai đoạn B).

Định dạng lưu trong `DataRecord.style`, mọi người cùng thấy; quyền = quyền
sửa ô. Mỗi bài phân quyền kiểm cả hai chiều.
"""
import uuid
import pytest
from django.test import override_settings

from core.constants import GRID_FORMAT_CELLS_MAX, AuditAction
from core.exceptions import BusinessError
from core.models import AuditLog
from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, DataRecord, TableDef
from forms_builder.services import record_service
from orders.services import dispatch_service

pytestmark = pytest.mark.django_db

SUA_DUOC = override_settings(GRID_ONLY_TABLES=set())


@pytest.fixture
def bang_sale(departments, nguoi_dung):
    bang = TableDef.objects.create(
        name="Đơn hàng Sale", code="don_sale",
        department=departments["sale"], created_by=nguoi_dung["manager_sale"],
    )
    for i, (ten, ma, kieu, nhan) in enumerate([
        ("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
        ("Khách hàng", "khach", FieldType.TEXT, Meaning.CUSTOMER),
        ("Ghi chú", "ghi_chu", FieldType.LONG_TEXT, ""),
    ]):
        ColumnDef.objects.create(table=bang, name=ten, code=ma, field_type=kieu, meaning=nhan, order=i)
    return bang


@pytest.fixture
def bang_vd(departments, nguoi_dung):
    return dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])


def _dong(bang, nguoi, **gia_tri):
    return record_service.create_record(bang, gia_tri, actor=nguoi)


def _o(*cap):
    return [f"{ban_ghi.pk}:{ma}" for ban_ghi, ma in cap]


# ══ Sổ định dạng — quy tắc 7 ═══════════════════════════════════════

def test_normalise_style_chi_nhan_gia_tri_trong_so():
    """AC-11.15 — Sổ định dạng đóng: khoá hay giá trị lạ bị từ chối, giá trị rỗng nghĩa là bỏ, số được ép kiểu"""
    assert record_service.normalise_style({"b": "1", "bg": "vang", "fs": "14", "al": "c"}) == {"b": 1, "bg": "vang", "fs": 14, "al": "c"}
    assert record_service.normalise_style({"b": "", "bg": "", "fs": "0"}) == {}
    for xau in ({"bg": "#ff0000"}, {"fs": "15"}, {"al": "justify"}, {"color": "red"}, {"b": "x"},
                {"c": "#000000"}, {"c": "m41"}, {"fmt": "eur"}, {"i": "2"}):
        with pytest.raises(BusinessError):
            record_service.normalise_style(xau)
    with pytest.raises(BusinessError):
        record_service.normalise_style("b=1")
    # Sổ mở rộng theo mẫu KN Demo (ADR-011): bật/tắt, bảng 40 màu, cỡ 13, định dạng số
    assert record_service.normalise_style(
        {"i": "1", "u": "1", "st": "1", "wr": "1", "bd": "1", "c": "m11", "bg": "m40", "fs": "13", "fmt": "vnd"}
    ) == {"i": 1, "u": 1, "st": 1, "wr": 1, "bd": 1, "c": "m11", "bg": "m40", "fs": 13, "fmt": "vnd"}
    assert record_service.normalise_style({"i": "", "c": "", "fmt": ""}) == {}
    assert len(record_service.PALETTE) == 40 and len(record_service.PALETTE_KEYS) == 40


# ══ Lưu và cùng thấy — AC-11.15 ════════════════════════════════════

def test_dinh_dang_o_luu_va_nguoi_khac_thay(client,bang_sale,nguoi_dung):
    st=nguoi_dung['staff_sale_1'];d=_dong(bang_sale,st,khach='A');d.style={'khach':{'b':1,'fmt':'text'}};d.save()
    client.force_login(st);url=f'/bang-tinh/{bang_sale.code}/luu-json/'
    response=client.post(url,{'operation':str(uuid.uuid4()),'cells':[{'id':d.pk,'column':'khach','property':'fs','old':None,'value':14}]},content_type='application/json')
    assert response.status_code==200,response.content
    d.refresh_from_db();assert d.style['khach']=={'b':1,'fmt':'text','fs':14}
    client.force_login(nguoi_dung['manager_sale'])
    data=client.get(f'/bang-tinh/{bang_sale.code}/du-lieu/').json()
    assert data['rows'][0]['cells']['khach']['style']==d.style['khach']


def test_dinh_dang_theo_quyen_sua_o(client,bang_sale,bang_vd,nguoi_dung):
    d=_dong(bang_sale,nguoi_dung['staff_sale_1'],khach='A')
    for role,status in [('staff_sale_2',403),('staff_mkt',403),('leader_sale_1',200),('manager_sale',200)]:
        client.force_login(nguoi_dung[role]);d.refresh_from_db()
        response=client.post(f'/bang-tinh/{bang_sale.code}/luu-json/',{'operation':str(uuid.uuid4()),'cells':[{'id':d.pk,'column':'khach','property':'fs','old':d.style.get('khach',{}).get('fs'),'value':14}]},content_type='application/json')
        assert response.status_code==status,(role,response.content)


# ══ Sổ định dạng mở rộng theo demo — AC-11.23 ══════════════════════

def test_dinh_dang_mo_rong_va_dinh_dang_so(client,bang_sale,nguoi_dung):
    d=_dong(bang_sale,nguoi_dung['staff_sale_1'],khach='A');client.force_login(nguoi_dung['staff_sale_1'])
    response=client.post(f'/bang-tinh/{bang_sale.code}/luu-json/',{'operation':str(uuid.uuid4()),'cells':[{'id':d.pk,'column':'khach','property':'b','old':None,'value':1}]},content_type='application/json')
    assert response.status_code==400
    d.refresh_from_db();assert d.style=={}
