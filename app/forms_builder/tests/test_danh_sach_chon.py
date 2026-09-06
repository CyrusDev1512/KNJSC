"""Danh sách chọn của cột kiểu *Chọn một* — FR-8.7, Q54.

Bước 1 kiểm phần định nghĩa: Manager đặt danh sách trong Sửa cột, model chặn
danh sách sai. Phần điền, sửa ô và "Thêm mới…" kiểm ở các bài phía dưới cùng
tệp (thêm dần theo giai đoạn).
"""
import pytest
from django.core.exceptions import ValidationError

from forms_builder.forms import ColumnForm
from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import CHOICE_OPTION_MAX_LENGTH, ColumnDef, TableDef
from forms_builder.services import table_service

pytestmark = pytest.mark.django_db


@pytest.fixture
def bang_sale(departments, nguoi_dung):
    """Bảng của bộ phận Sale, chưa có cột nào."""
    return TableDef.objects.create(
        name="Kênh bán Sale", code="kenh_sale",
        department=departments["sale"], created_by=nguoi_dung["manager_sale"],
    )


# ══ Định nghĩa danh sách — Sửa cột ═══════════════════════════════

def test_danh_sach_chi_cho_kieu_chon_mot(bang_sale):
    """AC-8.7 — Danh sách chọn chỉ đặt được cho cột kiểu Chọn một"""
    cot = ColumnDef(
        table=bang_sale, name="Kênh", code="kenh",
        field_type=FieldType.TEXT, options=["Facebook", "TikTok"],
    )
    with pytest.raises(ValidationError) as loi:
        cot.full_clean()
    assert "options" in loi.value.message_dict

    cot.field_type = FieldType.CHOICE
    cot.full_clean()          # kiểu Chọn một thì nhận
    cot.save()
    assert ColumnDef.objects.get(pk=cot.pk).options == ["Facebook", "TikTok"]


def test_danh_sach_bo_trung_va_dong_trong(bang_sale):
    """AC-8.7 — Sửa cột gõ mỗi dòng một giá trị: bỏ dòng trống, khoảng trắng thừa và giá trị trùng"""
    form = ColumnForm({
        "name": "Kênh", "code": "kenh", "field_type": FieldType.CHOICE,
        "meaning": "", "order": 1, "compute_decimals": 2,
        "options": "Facebook\n\n  TikTok  \nfacebook\nZalo\n",
    }, table=bang_sale)
    assert form.is_valid(), form.errors
    assert form.cleaned_data["options"] == ["Facebook", "TikTok", "Zalo"]

    cot = table_service.add_column(bang_sale, **form.cleaned_data)
    assert cot.options == ["Facebook", "TikTok", "Zalo"]

    # Mở lại để sửa thì thấy đúng từng dòng
    form_sua = ColumnForm(instance=cot, table=bang_sale)
    assert form_sua.initial["options"] == "Facebook\nTikTok\nZalo"


def test_model_chan_danh_sach_trung_va_qua_dai(bang_sale):
    """FR-8.7 — Danh sách đến từ dịch vụ hay JSON tay đều bị chặn nếu trùng, trống hoặc quá dài"""
    cot = ColumnDef(table=bang_sale, name="Kênh", code="kenh", field_type=FieldType.CHOICE)

    for sai in (["A", "a"], ["A", ""], ["A", "x" * (CHOICE_OPTION_MAX_LENGTH + 1)], " có dấu cách "):
        cot.options = sai if isinstance(sai, list) else [sai]
        with pytest.raises(ValidationError) as loi:
            cot.full_clean()
        assert "options" in loi.value.message_dict, sai


def test_cot_mang_nhan_san_pham_khong_nhap_danh_sach_tay(bang_sale):
    """FR-8.7 — Cột Chọn một mang nhãn có nguồn hệ thống thì không nhập danh sách tay"""
    from forms_builder import choice_registry

    cot = ColumnDef(
        table=bang_sale, name="Sản phẩm", code="san_pham",
        field_type=FieldType.CHOICE, meaning=Meaning.PRODUCT, options=["Kem"],
    )
    if choice_registry.has_meaning_source(Meaning.PRODUCT):
        with pytest.raises(ValidationError) as loi:
            cot.full_clean()
        assert "không nhập tay" in str(loi.value.message_dict["options"])
    else:
        # Chưa module nào đăng ký nguồn (giai đoạn sau) thì cột nhận danh sách tay
        cot.full_clean()
