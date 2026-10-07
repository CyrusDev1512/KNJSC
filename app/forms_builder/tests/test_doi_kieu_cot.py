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
