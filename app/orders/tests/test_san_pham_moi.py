"""Thêm sản phẩm vào danh mục — FR-6.8, Q57.

Bước 2 kiểm tầng dịch vụ; đường dẫn "Thêm mới…" trên màn hình Lên đơn kiểm ở
các bài thêm sau trong cùng tệp.
"""
import pytest

from core.constants import AuditAction
from core.exceptions import BusinessError
from core.models import AuditLog
from orders.models import Product, ProductGroup
from orders.services import dispatch_service, product_service

pytestmark = pytest.mark.django_db


@pytest.fixture
def san_pham(db):
    nhom = ProductGroup.objects.create(name="Đồ gia dụng")
    return {
        "massage": Product.objects.create(name="Máy massage cầm tay HM-200", code="hm200", group=nhom),
    }


def test_ma_san_pham_tu_sinh_khong_trung(san_pham, nguoi_dung):
    """AC-6.9 — Mã sản phẩm tự sinh từ tên (bỏ dấu), trùng thì thêm số, và mỗi lần thêm có nhật ký"""
    truoc = AuditLog.objects.filter(action=AuditAction.CREATE).count()
    a = product_service.create_product(name="Đèn ngủ cảm ứng", actor=nguoi_dung["manager_sale"])
    b = product_service.create_product(name="Đèn ngủ  cảm ứng  Pro", actor=nguoi_dung["manager_sale"])
    assert a.code == "den-ngu-cam-ung"
    assert b.name == "Đèn ngủ cảm ứng Pro" and b.code == "den-ngu-cam-ung-pro"
    assert AuditLog.objects.filter(action=AuditAction.CREATE).count() == truoc + 2

    # Cùng gốc mã thì hậu tố tăng dần
    Product.objects.create(name="Tạm", code="den-ngu")
    c = product_service.create_product(name="Đèn ngủ", actor=nguoi_dung["manager_sale"])
    assert c.code == "den-ngu-2"


def test_them_san_pham_dong_bo_cot_sl_tren_bang_van_don(san_pham, nguoi_dung):
    """AC-6.9 — Thêm sản phẩm xong thì bảng vận đơn có ngay cột số lượng của sản phẩm đó"""
    bang = dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    assert not bang.columns.filter(code="sl_kem_chong_nang").exists()
    product_service.create_product(name="Kem chống nắng", actor=nguoi_dung["manager_sale"])
    cot = bang.columns.get(code="sl_kem_chong_nang")
    assert cot.name == "Kem chống nắng"


def test_chua_co_bang_van_don_van_them_duoc(san_pham, nguoi_dung):
    """AC-6.9 — Máy chưa có bảng vận đơn thì thêm sản phẩm vẫn được, không lỗi"""
    sp = product_service.create_product(name="Serum mới", actor=nguoi_dung["manager_sale"])
    assert Product.objects.filter(pk=sp.pk).exists()


def test_trung_ten_hoac_rong_bi_tu_choi(san_pham, nguoi_dung):
    """AC-6.9 — Tên trùng sản phẩm đang bán (không phân biệt hoa thường) hoặc tên rỗng thì bị từ chối"""
    with pytest.raises(BusinessError) as loi:
        product_service.create_product(name="máy massage cầm tay hm-200", actor=nguoi_dung["manager_sale"])
    assert "đã có trong danh mục" in str(loi.value)
    with pytest.raises(BusinessError):
        product_service.create_product(name="   ", actor=nguoi_dung["manager_sale"])
    assert Product.objects.count() == 1
