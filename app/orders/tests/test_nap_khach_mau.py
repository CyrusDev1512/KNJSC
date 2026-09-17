"""Lệnh `nap_khach_mau` — nạp khách giả theo lô, có khách mua lại, vào bảng vận đơn."""
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from forms_builder.models import DataRecord, TableDef
from orders.constants import ACTIVE_WAYBILL_TABLE_CODE, WAYBILL_TABLE_CODE
from orders.management.commands import nap_khach_mau
from orders.models import Product, ProductGroup, WaybillAssignment
from orders.services import dispatch_service

pytestmark = pytest.mark.django_db


@pytest.fixture
def san_sang(nguoi_dung):
    nhom = ProductGroup.objects.create(name="Nhóm thử")
    Product.objects.create(name="Kem A", code="kem-a", group=nhom)
    Product.objects.create(name="Serum B", code="serum-b", group=nhom)
    dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    return TableDef.objects.get(code=ACTIVE_WAYBILL_TABLE_CODE)


def _goi(*tham_so):
    ra = StringIO()
    with override_settings(DEBUG=True):
        call_command("nap_khach_mau", *tham_so, stdout=ra)
    return ra.getvalue()


def test_nap_khach_co_mua_lai_va_phan_cong(san_sang):
    """AC-10.9 — 50 khách với 20% mua lại thành 62 dòng KH-*, mỗi khách ít nhất
    một dòng, có số điện thoại trùng cho cột Trùng, mỗi dòng có phân công; chạy
    lại xoá sạch."""
    ra = _goi("--bang", ACTIVE_WAYBILL_TABLE_CODE, "--so-khach", "50")
    def ds():           # queryset mới mỗi lần, không dùng lại bộ đệm của lần duyệt trước
        return DataRecord.objects.filter(table=san_sang, data__ma_don__startswith=nap_khach_mau.PREFIX)
    assert ds().count() == 62 == round(50 / 0.8)
    assert "62 dòng" in ra
    so = list(ds().values_list("val_phone", flat=True))
    assert 50 <= len(set(so)) < 62, "khách mua lại phải dùng lại số điện thoại"
    assert WaybillAssignment.objects.filter(record__in=ds()).count() == 62
    assert all(r.val_date and r.val_customer and r.val_revenue is not None for r in ds())

    # Xoá cũ rồi nạp lại với hạt giống cũ: cùng số dòng, không trùng mã đơn
    _goi("--bang", ACTIVE_WAYBILL_TABLE_CODE, "--so-khach", "50", "--xoa-cu")
    assert ds().count() == 62
    assert ds().values("data__ma_don").distinct().count() == 62
    assert "Đã xoá 62 dòng" in _goi("--bang", ACTIVE_WAYBILL_TABLE_CODE, "--so-khach", "0", "--xoa-cu")
    assert ds().count() == 0
    assert not WaybillAssignment.objects.exists()


def test_bang_khong_co_profile_van_don_thi_khong_phan_cong(nguoi_dung, san_sang):
    """AC-10.9 — bảng vận đơn cũ (không profile) vẫn nạp được nhưng không tạo
    phân công; tỉ lệ 0 thì không có số nào trùng."""
    _goi("--bang", WAYBILL_TABLE_CODE, "--so-khach", "20", "--ti-le-mua-lai", "0")
    ds = DataRecord.objects.filter(table__code=WAYBILL_TABLE_CODE, data__ma_don__startswith="KH-")
    assert ds.count() == 20
    assert ds.values("val_phone").distinct().count() == 20
    assert not WaybillAssignment.objects.exists()


def test_tu_choi_khi_debug_tat_hoac_bang_sai(san_sang):
    """AC-10.9 — DEBUG tắt thì từ chối như `seed_perf`; bảng không có thì báo rõ."""
    with override_settings(DEBUG=False), pytest.raises(CommandError, match="DEBUG"):
        call_command("nap_khach_mau", "--so-khach", "1")
    with pytest.raises(CommandError, match="khong_co"):
        _goi("--bang", "khong_co", "--so-khach", "1")
    with pytest.raises(CommandError, match="ti-le"):
        _goi("--bang", ACTIVE_WAYBILL_TABLE_CODE, "--so-khach", "1", "--ti-le-mua-lai", "1")
