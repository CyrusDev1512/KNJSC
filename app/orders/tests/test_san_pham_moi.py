"""Thêm sản phẩm vào danh mục — FR-6.8, Q61.

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


# ══ Màn hình Lên đơn — "Thêm mới…" tại ô chọn sản phẩm ═══════════════

def test_manager_sale_them_san_pham_tai_o_chon(client, san_pham, nguoi_dung):
    """AC-6.9 — Manager Sale thêm sản phẩm qua đường dẫn của màn hình Lên đơn; danh sách trả về có mục mới chọn sẵn theo mã"""
    client.force_login(nguoi_dung["manager_sale"])
    kq = client.post("/len-don/san-pham-moi/", {"nhan_moi": "Đèn ngủ cảm ứng"})
    assert kq.status_code == 200
    html = kq.content.decode()
    assert '<option value="den-ngu-cam-ung" selected>Đèn ngủ cảm ứng</option>' in html
    assert '<option value="hm200">' in html and '<option value="__them__">' in html
    assert Product.objects.filter(code="den-ngu-cam-ung").exists()

    kq = client.post("/len-don/san-pham-moi/", {"nhan_moi": ""})
    assert kq.status_code == 400 and "không được để trống" in kq.content.decode()


def test_staff_va_leader_sale_bi_403_co_nhat_ky(client, san_pham, nguoi_dung):
    """AC-6.9 — Staff và Leader gửi thẳng đường dẫn thêm sản phẩm thì bị từ chối và có nhật ký"""
    for ma in ("staff_sale_1", "leader_sale_1"):
        truoc = AuditLog.objects.filter(action=AuditAction.DENIED).count()
        client.force_login(nguoi_dung[ma])
        assert client.post("/len-don/san-pham-moi/", {"nhan_moi": "Mới"}).status_code == 403, ma
        assert AuditLog.objects.filter(action=AuditAction.DENIED).count() == truoc + 1
    assert Product.objects.count() == 1


def test_manager_bo_phan_khac_bi_chan(client, san_pham, nguoi_dung):
    """AC-6.9 — Manager Marketing không vào được màn hình Lên đơn nên cũng không thêm sản phẩm ở đó"""
    client.force_login(nguoi_dung["manager_mkt"])
    assert client.post("/len-don/san-pham-moi/", {"nhan_moi": "Mới"}).status_code == 403
    assert client.get("/len-don/san-pham-moi/").status_code == 405


def test_len_don_hien_them_moi_chi_cho_manager(client, san_pham, nguoi_dung):
    """AC-6.9 — Ô chọn sản phẩm trên Lên đơn có mục Thêm mới và hộp thêm cho Manager; Staff không thấy"""
    client.force_login(nguoi_dung["manager_sale"])
    html = client.get("/len-don/").content.decode()
    assert '<option value="__them__">' in html and 'id="them-sp"' in html
    assert '<option value="hm200">Máy massage cầm tay HM-200</option>' in html

    client.force_login(nguoi_dung["staff_sale_1"])
    html = client.get("/len-don/").content.decode()
    assert '<option value="__them__">' not in html and 'id="them-sp"' not in html
    assert '<option value="hm200">Máy massage cầm tay HM-200</option>' in html
