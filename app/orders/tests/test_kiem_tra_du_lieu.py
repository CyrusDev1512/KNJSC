"""Lệnh rà toàn vẹn dữ liệu `kiem_tra_du_lieu` — AC-36.14 (06.10.2026).

Chỉ đọc: chạy trên VPS trước và sau phát hành. Bài cố ý làm lệch dữ liệu bằng `.update()` (đi vòng tầng dịch vụ, như
lệnh SQL tay hay bản cũ để lại) rồi xem lệnh có bắt được không.
"""
import pytest
from django.core.management import call_command

from forms_builder.models import DataRecord
from orders.models import Order, Product, ProductGroup
from orders.services import dispatch_service
from orders.tests.test_len_don import _len_don, bang_van_don  # noqa: F401 — fixture dùng chung

pytestmark = pytest.mark.django_db


@pytest.fixture
def don(bang_van_don, nguoi_dung):
    nhom = ProductGroup.objects.create(name="Nhóm thử")
    sp = {"massage": Product.objects.create(name="Máy thử", code="may-thu", group=nhom)}
    dispatch_service.sync_product_columns()         # cột sl_may_thu như khi bật máy
    return _len_don(nguoi_dung["staff_sale_1"], sp)


def _chay(capsys, *tham_so):
    try:
        call_command("kiem_tra_du_lieu", *tham_so)
        ma = 0
    except SystemExit as e:
        ma = e.code
    return ma, capsys.readouterr().out


def test_du_lieu_sach_thi_dat_va_khong_ghi_gi(don, capsys):
    """AC-36.14 — Dữ liệu vừa tạo qua tầng dịch vụ: mọi phép rà ĐẠT, thoát mã 0, không dòng nào bị ghi"""
    moc = DataRecord.all_objects.get(pk=don.record_id).updated_at
    ma, ra = _chay(capsys)
    assert ma == 0 and "Dữ liệu khớp" in ra and "LỆCH" not in ra, ra
    assert DataRecord.all_objects.get(pk=don.record_id).updated_at == moc


def test_bat_duoc_tung_loai_lech_va_sua_cot_tach(don, capsys):
    """AC-36.14 — Bắt được: cột tách lệch data, giá trị ngoài danh sách chọn, sl_* lệch Chi tiết, mã đơn trùng, đơn
    mồ côi; thoát mã 1 (sl_* chỉ để biết, không tính). `--sua` tính lại cột tách, các lỗi còn lại chỉ báo"""
    dong = DataRecord.objects.get(pk=don.record_id)
    DataRecord.objects.filter(pk=dong.pk).update(val_customer="Sai")
    DataRecord.objects.filter(pk=dong.pk).update(data={**dong.data, "quoc_gia": "Sao Hoả", "sl_may_thu": 9})
    ma, ra = _chay(capsys, "--bang", "van_don")
    assert ma == 1
    assert "LỆCH · cột tách / cột tính sẵn lệch data: 1" in ra
    assert 'quoc_gia: "Sao Hoả"' in ra
    assert "BIẾT · sl_* lệch Chi tiết sản phẩm (không tính vào mã thoát): 1" in ra

    ma, ra = _chay(capsys, "--bang", "van_don", "--sua")
    assert "Đã tính lại 1 dòng" in ra and "ĐẠT · cột tách / cột tính sẵn lệch data: 0" in ra
    assert DataRecord.objects.get(pk=dong.pk).val_customer == "Nguyễn Văn An"

    # Dòng xoá vòng tầng dịch vụ: đơn còn sống thành mồ côi; mã đơn trùng do dữ liệu cũ (không qua ràng buộc)
    DataRecord.objects.filter(pk=dong.pk).update(deleted_at=dong.created_at)
    ma, ra = _chay(capsys)
    assert ma == 1 and f"đơn {don.code} còn sống" in ra
    assert Order.objects.filter(pk=don.pk).exists()


def test_bang_khong_co_bao_loi(capsys, db):
    """AC-36.14 — Gõ sai mã bảng: báo lỗi rõ, không rà"""
    from django.core.management.base import CommandError
    with pytest.raises(CommandError, match="khong_co"):
        call_command("kiem_tra_du_lieu", "--bang", "khong_co")
