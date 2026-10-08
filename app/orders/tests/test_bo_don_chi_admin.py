"""AC-6.13 — Bỏ đơn chỉ Admin (ADR-049, chủ dự án 08.10.2026).

Bỏ đơn xoá mềm cả dòng vận đơn đang chạy (AC-6.12), nên cùng luật với nút Xoá dòng trên lưới: chỉ Quản trị. Trước đây
người lên đơn tự bỏ được đơn của mình. Quy tắc nằm ở `order_service.cancel_order` (tầng dịch vụ); view chỉ báo lỗi.
"""
import pytest

from core.constants import AuditAction
from core.exceptions import OutOfScopeError
from core.models import AuditLog
from forms_builder.models import DataRecord
from orders.models import Order
from orders.services import order_service
from orders.tests.test_len_don import _len_don, bang_van_don  # noqa: F401 — fixture dùng chung
from orders.tests.test_xoa_dong_huy_don import sp  # noqa: F401

pytestmark = pytest.mark.django_db


def test_bo_don_chi_admin(client, bang_van_don, sp, nguoi_dung, settings):  # noqa: F811
    """AC-6.13 — Người lên đơn và Manager Sale không thấy nút Bỏ đơn; gửi thẳng yêu cầu thì bị từ chối có nhật ký, đơn và
    dòng vận đơn còn nguyên; tầng dịch vụ cũng từ chối. Admin thấy nút và bỏ được: đơn và dòng xoá mềm"""
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.GRID_ONLY_TABLES = set()
    don = _len_don(nguoi_dung["staff_sale_1"], sp)
    trang, bo = f"/van-don/don-goc/{don.code}/", f"/van-don/don-goc/{don.code}/bo/"

    for ten in ("staff_sale_1", "manager_sale"):
        nguoi = nguoi_dung[ten]
        client.force_login(nguoi)
        r = client.get(trang)
        assert r.status_code == 200 and "Bỏ đơn này" not in r.content.decode(), ten
        truoc = AuditLog.objects.filter(action=AuditAction.DENIED, actor=nguoi).count()
        client.post(bo)
        assert Order.objects.filter(pk=don.pk).exists(), ten
        assert DataRecord.objects.filter(pk=don.record_id).exists(), ten
        assert AuditLog.objects.filter(action=AuditAction.DENIED, actor=nguoi).count() == truoc + 1, ten

    with pytest.raises(OutOfScopeError):
        order_service.cancel_order(don, actor=nguoi_dung["staff_sale_1"])
    assert Order.objects.filter(pk=don.pk).exists()

    client.force_login(nguoi_dung["admin"])
    assert "Bỏ đơn này" in client.get(trang).content.decode()
    client.post(bo)
    assert Order.all_objects.get(pk=don.pk).deleted_at is not None
    assert DataRecord.all_objects.get(pk=don.record_id).deleted_at is not None
