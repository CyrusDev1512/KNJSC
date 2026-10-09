"""Dòng vận đơn và đơn gốc đi cùng nhau — chốt 06.10.2026.

`order_service.cancel_order` (Bỏ đơn) đã xoá mềm cả đơn lẫn dòng. Chiều ngược lại thì hở: xoá dòng bằng tầng dịch vụ
bảng (`record_service.delete_record`) để lại đơn còn sống mà không còn dòng nào trên bảng — đơn mồ côi, vẫn được đếm
ở chỗ đọc `Order`. Chủ dự án chốt: xoá dòng thì bỏ luôn đơn; khôi phục dòng thì khôi phục đơn.
"""
import pytest

from core.constants import AuditAction
from core.models import AuditLog
from forms_builder.models import DataRecord
from forms_builder.services import record_service
from orders.models import Order, Product, ProductGroup
from orders.services import order_service
from orders.tests.test_len_don import _len_don, bang_van_don  # noqa: F401 — fixture dùng chung

pytestmark = pytest.mark.django_db


@pytest.fixture
def sp(db):
    nhom = ProductGroup.objects.create(name="Nhóm thử")
    return {"massage": Product.objects.create(name="Máy thử", code="may_thu", group=nhom)}


def test_xoa_dong_thi_bo_don_khoi_phuc_thi_lay_lai(bang_van_don, sp, nguoi_dung, settings):
    """AC-6.12 — Xoá dòng vận đơn của một đơn thì đơn bị bỏ (xoá mềm, có nhật ký nêu mã đơn); khôi phục dòng thì
    đơn sống lại, cũng có nhật ký"""
    settings.GRID_ONLY_TABLES = set()          # đúng cấu hình dịch vụ CRM: bảng vận đơn sửa được
    nv, vd = nguoi_dung["staff_sale_1"], nguoi_dung["staff_vd"]
    don = _len_don(nv, sp)
    dong = DataRecord.objects.get(pk=don.record_id)

    record_service.delete_record(dong, actor=vd)
    assert Order.all_objects.get(pk=don.pk).deleted_at is not None
    assert not Order.objects.filter(pk=don.pk).exists()
    assert AuditLog.objects.filter(action=AuditAction.DELETE, detail__contains=don.code).exists()

    record_service.restore_record(DataRecord.all_objects.get(pk=dong.pk), actor=vd)
    assert Order.objects.filter(pk=don.pk).exists()
    assert AuditLog.objects.filter(action=AuditAction.UPDATE, detail__contains=don.code).exists()


def test_bo_don_van_xoa_ca_dong(bang_van_don, sp, nguoi_dung):
    """AC-6.12 — Chiều cũ giữ nguyên: Bỏ đơn xoá mềm cả đơn lẫn dòng; dòng của đơn khác không bị đụng"""
    nv = nguoi_dung["staff_sale_1"]
    a, b = _len_don(nv, sp), _len_don(nv, sp, phone="0911111111")
    order_service.cancel_order(a, actor=nguoi_dung["admin"])
    assert DataRecord.all_objects.get(pk=a.record_id).deleted_at is not None
    assert DataRecord.objects.filter(pk=b.record_id).exists() and Order.objects.filter(pk=b.pk).exists()
