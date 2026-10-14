"""Đổi kiểu dữ liệu của cột không bỏ rơi dữ liệu cũ — AC-8.11 (06.10.2026).

Trước đây Sửa cột đổi `field_type` mà không đụng giá trị đã nhập: cột Chữ có "1.500" đổi sang Số nguyên thì ô vẫn là
chuỗi "1.500", sắp xếp và cộng theo cột ra sai; ô "abc" nằm lại trong cột số mà không ai biết. Nay đổi kiểu thì thử
chuyển **mọi** giá trị cũ (kể cả dòng đã xoá — khôi phục là hiện lại): có giá trị không chuyển được thì từ chối, nói
số dòng và ví dụ; chuyển được hết thì ghi lại giá trị theo kiểu mới.
"""
import pytest

from core.exceptions import BusinessError
from forms_builder.meaning import FieldType
from forms_builder.models import ColumnDef, DataRecord, TableDef
from forms_builder.services import record_service, table_service

pytestmark = pytest.mark.django_db


@pytest.fixture
def bang(departments, nguoi_dung):
    bang = TableDef.objects.create(name="Kho", code="kho", department=departments["sale"],
                                   created_by=nguoi_dung["manager_sale"])
    ColumnDef.objects.create(table=bang, name="Số lượng", code="sl", field_type=FieldType.TEXT, order=1)
    return bang


def _dong(bang, nguoi, gia_tri):
    return record_service.create_record(bang, {"sl": gia_tri}, actor=nguoi)


def test_doi_kieu_tu_choi_khi_con_gia_tri_khong_chuyen_duoc(bang, nguoi_dung):
    """AC-8.11 — Cột Chữ có "abc" (ở cả dòng đã xoá) đổi sang Số nguyên: từ chối, lời nêu số dòng hỏng và ví dụ; kiểu
    cột và dữ liệu giữ nguyên"""
    nv = nguoi_dung["manager_sale"]
    _dong(bang, nv, "12")
    xoa = _dong(bang, nv, "abc")
    record_service.delete_record(xoa, actor=nv)
    cot = bang.columns.get(code="sl")
    with pytest.raises(BusinessError, match=r"1 dòng.*abc"):
        table_service.update_column(cot, {"field_type": FieldType.INTEGER}, actor=nv)
    assert ColumnDef.objects.get(pk=cot.pk).field_type == FieldType.TEXT
    assert DataRecord.all_objects.get(pk=xoa.pk).data["sl"] == "abc"


def test_doi_kieu_chuyen_het_gia_tri_cu(bang, nguoi_dung):
    """AC-8.11 — Mọi giá trị cũ chuyển được thì đổi kiểu và ghi lại theo kiểu mới ("1.500" → 1500); ô trống giữ trống;
    đổi ngược sang Chữ vẫn đọc được"""
    nv = nguoi_dung["manager_sale"]
    a, b, c = _dong(bang, nv, "12"), _dong(bang, nv, "1.500"), _dong(bang, nv, "")
    cot = bang.columns.get(code="sl")
    table_service.update_column(cot, {"field_type": FieldType.INTEGER}, actor=nv)
    assert [DataRecord.objects.get(pk=x.pk).data.get("sl") for x in (a, b, c)] == [12, 1500, None]
    table_service.update_column(ColumnDef.objects.get(pk=cot.pk), {"field_type": FieldType.TEXT}, actor=nv)
    assert [DataRecord.objects.get(pk=x.pk).data.get("sl") for x in (a, b)] == ["12", "1500"]


@pytest.fixture
def bang_tien(departments, nguoi_dung):
    bang = TableDef.objects.create(name="Thu chi", code="thu_chi", department=departments["sale"],
                                   created_by=nguoi_dung["manager_sale"])
    ColumnDef.objects.create(table=bang, name="Tiền", code="tien", field_type=FieldType.MONEY, order=1)
    return bang


def _tien(bang, nguoi, *gia_tri):
    return [record_service.create_record(bang, {"tien": g}, actor=nguoi) for g in gia_tri]


def test_sua_nhan_cot_tien_khong_doi_so_da_luu(client, bang_tien, nguoi_dung):
    """AC-8.11 — Sửa nhãn cột Tiền (Sửa cột gửi kèm kiểu không đổi) không viết lại số đã lưu: "0.125" và
    "1234.567" giữ nguyên ở mọi dòng, kể cả dòng đã xoá; Staff bị 403 (TL-03 — trước đây cả cột bị nhân nghìn)"""
    from decimal import Decimal

    ql = nguoi_dung["manager_sale"]
    a, b, xoa = _tien(bang_tien, ql, Decimal("0.125"), Decimal("1234.567"), Decimal("7.5"))
    record_service.delete_record(xoa, actor=ql)
    goc = bang_tien.columns.get(code="tien")
    table_service.update_column(goc, {"name": "Tiền mới", "field_type": FieldType.MONEY}, actor=ql)
    assert [DataRecord.all_objects.get(pk=x.pk).data["tien"] for x in (a, b, xoa)] == ["0.125", "1234.567", "7.5"]

    client.force_login(ql)
    form = {"name": "Tiền lần hai", "code": "tien", "field_type": "money", "meaning": "", "order": 1,
            "compute_decimals": 2, "compute_op": "", "compute_left": "", "compute_right": ""}
    assert client.post(f"/bang/{bang_tien.code}/cot/?cot={goc.pk}", form).status_code == 302
    assert [DataRecord.all_objects.get(pk=x.pk).data["tien"] for x in (a, b, xoa)] == ["0.125", "1234.567", "7.5"]
    client.force_login(nguoi_dung["staff_sale_1"])
    assert client.post(f"/bang/{bang_tien.code}/cot/?cot={goc.pk}", {**form, "name": "x"}).status_code == 403
    assert ColumnDef.objects.get(pk=goc.pk).name == "Tiền lần hai"


def test_doi_kieu_tien_sang_so_nguyen_doc_dung_chuoi_may(bang_tien, nguoi_dung):
    """AC-8.11 — Đổi kiểu đọc giá trị đã lưu của cột số theo chuỗi máy: Tiền còn số lẻ ("0.125", "1234.5") sang
    Số nguyên bị từ chối kèm số dòng; Tiền "1234.00" sang Số nguyên ra 1234; Số thập phân "0.125" sang Tiền giữ
    "0.125" (TL-03 — trước đây ra 125, 12345, 123400)"""
    from decimal import Decimal

    ql = nguoi_dung["manager_sale"]
    _tien(bang_tien, ql, Decimal("0.125"), Decimal("1234.5"))
    cot = bang_tien.columns.get(code="tien")
    with pytest.raises(BusinessError, match=r"2 dòng.*0\.125"):
        table_service.update_column(cot, {"field_type": FieldType.INTEGER}, actor=ql)
    assert ColumnDef.objects.get(pk=cot.pk).field_type == FieldType.MONEY
    assert sorted(d.data["tien"] for d in DataRecord.objects.filter(table=bang_tien)) == ["0.125", "1234.5"]

    cot_tron = ColumnDef.objects.create(table=bang_tien, name="Tiền chẵn", code="tien_chan",
                                        field_type=FieldType.MONEY, order=3)
    tron = record_service.create_record(bang_tien, {"tien_chan": Decimal("1234.00")}, actor=ql)
    table_service.update_column(cot_tron, {"field_type": FieldType.INTEGER}, actor=ql)
    assert DataRecord.objects.get(pk=tron.pk).data["tien_chan"] == 1234

    so = ColumnDef.objects.create(table=bang_tien, name="Tỉ lệ", code="ti_le", field_type=FieldType.DECIMAL, order=2)
    d = record_service.create_record(bang_tien, {"ti_le": Decimal("0.125")}, actor=ql)
    table_service.update_column(so, {"field_type": FieldType.MONEY}, actor=ql)
    assert DataRecord.objects.get(pk=d.pk).data["ti_le"] == "0.125"
