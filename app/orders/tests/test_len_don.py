"""Kiểm thử lên đơn và ghi sang bảng vận đơn — Giai đoạn 5.

Ba thứ khó nhất, kiểm kỹ nhất:

1. **AC-6.5** — ghi sang bảng vận đơn hỏng thì đơn cũng không được lưu.
   Không bao giờ có đơn mồ côi
2. **AC-6.7** — đơn đã lưu không sửa được, chặn ở cả ba tầng
3. **AC-6.8** — nhận diện khách mua lại theo số điện thoại

Mỗi bài phân quyền kiểm **cả hai chiều**.
"""
from decimal import Decimal
from unittest import mock

import pytest
from django.test import override_settings

from core.constants import AuditAction, Currency
from core.exceptions import BusinessError
from core.models import AuditLog
from forms_builder.models import DataRecord, TableDef
from orders.constants import Market, PaymentMethod, WAYBILL_TABLE_CODE
from orders.models import Customer, Order, OrderLine, Product, ProductGroup
from orders.services import dispatch_service, order_service

pytestmark = pytest.mark.django_db


@pytest.fixture
def bang_van_don(departments, nguoi_dung):
    """Bảng vận đơn theo đúng cấu trúc chuẩn."""
    return dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])


@pytest.fixture
def san_pham(db):
    nhom = ProductGroup.objects.create(name="Đồ gia dụng")
    return {
        "massage": Product.objects.create(
            name="Máy massage cầm tay HM-200", code="hm200", group=nhom),
        "den": Product.objects.create(
            name="Đèn ngủ cảm ứng", code="den_ngu", group=nhom),
    }


def _len_don(nguoi, san_pham, phone="0912345678", **thay_doi):
    tham_so = dict(
        phone=phone, customer_name="Nguyễn Văn An",
        email="an@vidu.com", facebook="fb.com/an",
        market=Market.US, state="California", city="San Jose", zipcode="95112",
        payment_method=PaymentMethod.CARD, currency=Currency.USD,
        lines=[{"product": san_pham["massage"], "quantity": 2, "unit_price": "150.00"}],
        actor=nguoi,
    )
    tham_so.update(thay_doi)
    return order_service.create_order(**tham_so)


# ══ Lên đơn — FR-6.1, FR-6.2 ═══════════════════════════════════════

def test_len_don_luu_du_thong_tin(bang_van_don, san_pham, nguoi_dung):
    """AC-6.1 — Tạo đơn với đủ thông tin khách, sản phẩm, giá và thanh toán"""
    don = _len_don(nguoi_dung["staff_sale_1"], san_pham)

    assert don.code.startswith("DH-")
    assert don.customer.phone == "0912345678"
    assert don.total == Decimal("300.00")          # 2 × 150
    assert don.department == nguoi_dung["staff_sale_1"].profile.department


def test_don_nhieu_dong_san_pham(bang_van_don, san_pham, nguoi_dung):
    """AC-6.2 — Đơn có 5 sản phẩm lưu được đầy đủ, không mất dòng nào"""
    dong = [
        {"product": san_pham["massage"], "quantity": i, "unit_price": "100.00"}
        for i in range(1, 6)
    ]
    don = _len_don(nguoi_dung["staff_sale_1"], san_pham, lines=dong)

    assert don.lines.count() == 5
    assert don.total == Decimal("1500.00")         # (1+2+3+4+5) × 100


def test_thieu_truong_bat_buoc_thi_tu_choi(bang_van_don, san_pham, nguoi_dung):
    """AC-6.1 — Thiếu trường bắt buộc thì bị từ chối, không tạo đơn dở dang"""
    with pytest.raises(BusinessError):
        _len_don(nguoi_dung["staff_sale_1"], san_pham, phone="")

    with pytest.raises(BusinessError):
        _len_don(nguoi_dung["staff_sale_1"], san_pham, lines=[])

    assert not Order.objects.exists()
    assert not Customer.objects.exists()


def test_tong_tien_cong_bang_so_thap_phan(bang_van_don, san_pham, nguoi_dung):
    """AC-9.5 — Cộng tiền bằng số thập phân chính xác, không sai số — BR-8"""
    dong = [
        {"product": san_pham["massage"], "quantity": 1, "unit_price": "0.10"}
        for _ in range(10)
    ]
    don = _len_don(nguoi_dung["staff_sale_1"], san_pham, lines=dong)

    assert don.total == Decimal("1.00")            # số thực sẽ ra 0.9999999
    assert isinstance(don.total, Decimal)


# ══ Ghi sang bảng vận đơn — FR-6.3, FR-6.4 ═════════════════════════

def test_luu_don_sinh_dung_mot_dong_tren_bang(bang_van_don, san_pham, nguoi_dung):
    """AC-6.3 — Lưu đơn xong thì bảng vận đơn có thêm đúng một dòng"""
    don = _len_don(nguoi_dung["staff_sale_1"], san_pham)

    ds = DataRecord.all_objects.filter(table=bang_van_don)
    assert ds.count() == 1
    assert ds.first().data["ma_don"] == don.code


def test_don_nhieu_san_pham_van_chi_mot_dong(bang_van_don, san_pham, nguoi_dung):
    """AC-6.3 — Đơn nhiều sản phẩm vẫn chỉ sinh một dòng, gộp lại"""
    don = _len_don(nguoi_dung["staff_sale_1"], san_pham, lines=[
        {"product": san_pham["massage"], "quantity": 2, "unit_price": "150.00"},
        {"product": san_pham["den"], "quantity": 3, "unit_price": "20.00"},
    ])

    assert DataRecord.all_objects.filter(table=bang_van_don).count() == 1
    o = don.record.data
    assert "Máy massage cầm tay HM-200 ×2" in o["san_pham"]
    assert "Đèn ngủ cảm ứng ×3" in o["san_pham"]
    assert o["so_luong"] == 5
    assert o["gia_tien"] == "360.00"               # 300 + 60


def test_luu_ma_lien_ket_giua_don_va_dong(bang_van_don, san_pham, nguoi_dung):
    """AC-6.4 — Mã liên kết giữa đơn và dòng trên bảng được lưu và tra được"""
    don = _len_don(nguoi_dung["staff_sale_1"], san_pham)

    assert don.record is not None
    assert don.record.data["ma_don"] == don.code
    # Tra ngược từ dòng về đơn cũng phải được
    assert don.record.order == don


def test_ghi_sang_bang_hong_thi_don_cung_khong_luu(san_pham, nguoi_dung, departments):
    """AC-6.5 — Ghi sang bảng vận đơn thất bại thì đơn hàng cũng không được lưu

    Đây là bài quan trọng nhất của giai đoạn: hai việc phải cùng một giao dịch,
    không bao giờ có đơn mồ côi không ai đi giao.
    """
    dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])

    with mock.patch.object(
        dispatch_service, "push", side_effect=BusinessError("bảng hỏng")
    ):
        with pytest.raises(BusinessError):
            _len_don(nguoi_dung["staff_sale_1"], san_pham)

    assert not Order.all_objects.exists()
    assert not OrderLine.objects.exists()


def test_chua_co_bang_van_don_thi_bao_loi_ro(san_pham, nguoi_dung):
    """AC-6.5 — Chưa có bảng vận đơn thì báo lỗi rõ ràng, không nổ trang trắng"""
    assert not TableDef.all_objects.filter(code=WAYBILL_TABLE_CODE).exists()

    with pytest.raises(BusinessError) as loi:
        _len_don(nguoi_dung["staff_sale_1"], san_pham)
    assert "bảng vận đơn" in str(loi.value)
    assert not Order.all_objects.exists()


def test_sau_cot_them_co_tren_bang_van_don(bang_van_don, san_pham, nguoi_dung):
    """Q24 — Sáu cột thêm vào bảng vận đơn có mặt và nhận đúng dữ liệu"""
    don = _len_don(nguoi_dung["staff_sale_1"], san_pham)
    o = don.record.data

    assert o["quoc_gia"] == "Hoa Kỳ"
    assert o["loai_tien"] == Currency.USD
    assert o["facebook"] == "fb.com/an"
    assert o["email"] == "an@vidu.com"
    assert o["nguoi_ban"]                          # tên người bán, không rỗng
    assert "don_vi_phu" in o


def test_bo_phan_van_don_thay_don_cua_sale(bang_van_don, san_pham, nguoi_dung):
    """Q26 — Bộ phận Vận đơn thấy dòng do bên Sale lên, không phân biệt cấp bậc

    Bài này đỏ nếu dòng vận đơn quay lại thuộc bộ phận của **người ghi**. Lúc
    đó Vận đơn mở bảng ra thấy rỗng và không có gì để đi giao — lỗi đã xảy ra
    thật khi chạy thử tay.
    """
    don = _len_don(nguoi_dung["staff_sale_1"], san_pham)

    assert don.record.department == bang_van_don.department      # Vận đơn

    # Nhân viên Vận đơn không tạo dòng nào, nhưng phải thấy để đi giao
    thay = DataRecord.objects.in_scope(nguoi_dung["staff_vd"])
    assert thay.filter(pk=don.record_id).exists()


def test_van_don_sua_duoc_trang_thai_tren_bang(client, bang_van_don, san_pham, nguoi_dung):
    """Q26 (sửa theo ADR-009) — Bảng vận đơn chỉ xem ở Bảng dữ liệu, sửa ở Bảng tính; đơn gốc vẫn khoá

    Q26 sửa ngày 03.09.2026 (ADR-009): Bảng dữ liệu là nơi xem, Bảng tính là
    nơi Vận đơn làm việc. Dịch vụ `bangtinh` dùng cùng mã nhưng
    `GRID_ONLY_TABLES` rỗng — bài này dựng lại đúng điều kiện đó.
    """
    don = _len_don(nguoi_dung["staff_sale_1"], san_pham)
    duong_dan = f"/bang/{bang_van_don.code}/o/{don.record_id}/trang_thai_vc/"

    client.force_login(nguoi_dung["staff_vd"])
    kq = client.post(duong_dan, {"gia_tri": "Đang giao"})
    assert kq.status_code == 403, "ở dịch vụ chính, bảng vận đơn chỉ xem"
    don.record.refresh_from_db()
    assert don.record.data.get("trang_thai_vc") != "Đang giao"

    with override_settings(GRID_ONLY_TABLES=set()):          # dịch vụ Bảng tính
        kq = client.post(duong_dan, {"gia_tri": "Đang giao"})
    assert kq.status_code == 200

    don.record.refresh_from_db()
    assert don.record.data["trang_thai_vc"] == "Đang giao"
    don.refresh_from_db()
    assert don.total == Decimal("300.00")          # đơn gốc không đổi — BR-3


def test_bo_phan_khac_khong_thay_bang_van_don(bang_van_don, san_pham, nguoi_dung):
    """AC-3.5 — Chiều bị từ chối: bộ phận Marketing không thấy dòng vận đơn"""
    don = _len_don(nguoi_dung["staff_sale_1"], san_pham)
    thay = DataRecord.objects.in_scope(nguoi_dung["staff_mkt"])
    assert not thay.filter(pk=don.record_id).exists()


def test_bang_khong_dung_chung_van_theo_cap_bac(departments, nguoi_dung):
    """Bảng thường vẫn giữ phạm vi theo cấp bậc, cờ dùng chung không lan sang

    Nếu bài này đỏ thì mọi bảng báo cáo đã thành công khai trong bộ phận.
    """
    from forms_builder.services import record_service

    bang = TableDef.objects.create(
        name="Báo cáo riêng", code="bc_rieng", department=departments["sale"],
        created_by=nguoi_dung["manager_sale"],
    )
    assert bang.is_shared is False
    bg = record_service.create_record(
        bang, {}, actor=nguoi_dung["staff_sale_1"])

    assert DataRecord.objects.in_scope(nguoi_dung["staff_sale_1"]).filter(pk=bg.pk).exists()
    assert not DataRecord.objects.in_scope(nguoi_dung["staff_sale_2"]).filter(pk=bg.pk).exists()


def test_trang_thai_ban_dau_la_cho_xu_ly(bang_van_don, san_pham, nguoi_dung):
    """Q26 — Dòng mới sinh ra ở trạng thái Chờ xử lý, Vận đơn tự sửa sau"""
    don = _len_don(nguoi_dung["staff_sale_1"], san_pham)
    assert don.record.data["trang_thai_vc"] == "Chờ xử lý"
    assert don.record.data["trang_thai_tt"] == "Chờ thanh toán"
    assert don.record.val_status == "Chờ xử lý"    # cột tách có chỉ mục


# ══ Khoá sau khi lưu — FR-6.6, BR-3 ════════════════════════════════

def test_sua_don_bang_ma_thi_no_ngay(bang_van_don, san_pham, nguoi_dung):
    """AC-6.7 — Đơn đã lưu không sửa được, kể cả sửa bằng mã"""
    don = _len_don(nguoi_dung["staff_sale_1"], san_pham)
    don.note = "sửa trộm"

    with pytest.raises(RuntimeError):
        don.save()


def test_khong_co_duong_dan_sua_don(client, bang_van_don, san_pham, nguoi_dung):
    """AC-6.7 — Không có đường dẫn sửa đơn, gọi thẳng cũng không có gì"""
    don = _len_don(nguoi_dung["staff_sale_1"], san_pham)
    client.force_login(nguoi_dung["staff_sale_1"])

    for duong_dan in (f"/don-hang/{don.code}/sua/", f"/don-hang/{don.code}/cap-nhat/"):
        assert client.get(duong_dan).status_code == 404


def test_bo_don_la_danh_dau_va_go_ca_dong_tren_bang(bang_van_don, san_pham, nguoi_dung):
    """AC-9.1 — Bỏ đơn là đánh dấu xoá, và gỡ luôn dòng trên bảng vận đơn

    Quên gỡ dòng là để lại đơn mồ côi mà bộ phận Vận đơn vẫn thấy và vẫn đi giao.
    """
    don = _len_don(nguoi_dung["staff_sale_1"], san_pham)
    ma_dong = don.record_id
    order_service.cancel_order(don, actor=nguoi_dung["staff_sale_1"])

    assert not Order.objects.filter(pk=don.pk).exists()
    assert Order.all_objects.get(pk=don.pk).deleted_at is not None
    assert not DataRecord.objects.filter(pk=ma_dong).exists()
    assert DataRecord.all_objects.get(pk=ma_dong).deleted_at is not None


# ══ Khách mua lại và danh sách đen — FR-6.7, Q25 ═══════════════════

def test_nhan_dien_khach_mua_lai(bang_van_don, san_pham, nguoi_dung):
    """AC-6.8 — Nhập đơn với số điện thoại đã có thì báo khách đã mua trước đó"""
    assert order_service.customer_notice("0912345678") == {}

    _len_don(nguoi_dung["staff_sale_1"], san_pham, phone="0912345678")
    nhac = order_service.customer_notice("0912345678")

    assert nhac["mua_lai"] is True
    assert nhac["so_don_cu"] == 1


def test_khach_moi_thi_khong_bao_gi(bang_van_don, san_pham, nguoi_dung):
    """AC-6.8 — Chiều ngược lại: số điện thoại mới thì không báo gì"""
    _len_don(nguoi_dung["staff_sale_1"], san_pham, phone="0912345678")
    assert order_service.customer_notice("0999999999") == {}


def test_danh_sach_den_chi_canh_bao_khong_chan(bang_van_don, san_pham, nguoi_dung):
    """Q25 — Khách trong danh sách đen thì cảnh báo, nhưng vẫn lên đơn được"""
    khach = Customer.objects.create(
        phone="0900000000", name="Khách khó",
        is_blacklisted=True, blacklist_reason="Từ chối nhận hàng 2 lần",
    )
    nhac = order_service.customer_notice("0900000000")
    assert nhac["danh_sach_den"] is True
    assert "Từ chối nhận hàng" in nhac["ly_do"]

    don = _len_don(nguoi_dung["staff_sale_1"], san_pham, phone="0900000000")
    assert don.pk is not None                      # không chặn
    assert don.record.data["black_list"] == "Từ chối nhận hàng 2 lần"


def test_khach_cu_khong_bi_tao_trung(bang_van_don, san_pham, nguoi_dung):
    """FR-6.7 — Cùng số điện thoại thì dùng lại khách cũ, không tạo bản ghi trùng"""
    _len_don(nguoi_dung["staff_sale_1"], san_pham, phone="0912345678")
    _len_don(nguoi_dung["staff_sale_1"], san_pham, phone="0912345678")

    assert Customer.objects.filter(phone="0912345678").count() == 1
    assert Customer.objects.get(phone="0912345678").order_count() == 2


# ══ Phạm vi quyền — FR-6.5 ═════════════════════════════════════════

def test_staff_chi_thay_don_cua_minh(bang_van_don, san_pham, nguoi_dung):
    """AC-6.6 — Người tạo đơn xem lại được đơn cũ của mình, và chỉ của mình"""
    _len_don(nguoi_dung["staff_sale_1"], san_pham, phone="0911111111")
    _len_don(nguoi_dung["staff_sale_2"], san_pham, phone="0922222222")

    thay = order_service.orders_of(nguoi_dung["staff_sale_1"])
    assert thay.count() == 1
    assert thay.first().created_by == nguoi_dung["staff_sale_1"]


def test_leader_thay_don_ca_team(bang_van_don, san_pham, teams, nguoi_dung):
    """AC-3.2 — Leader thấy đơn của người trong team mình"""
    _len_don(nguoi_dung["staff_sale_1"], san_pham)
    thay = order_service.orders_of(nguoi_dung["leader_sale_1"])
    assert thay.filter(created_by=nguoi_dung["staff_sale_1"]).exists()


def test_manager_khong_thay_don_bo_phan_khac(bang_van_don, san_pham, nguoi_dung):
    """AC-3.5 — Manager không thấy đơn của bộ phận khác"""
    _len_don(nguoi_dung["staff_sale_1"], san_pham)
    assert not order_service.orders_of(nguoi_dung["manager_mkt"]).exists()


def test_goi_thang_don_ngoai_pham_vi_bi_chan(client, bang_van_don, san_pham, nguoi_dung):
    """AC-3.7 — Gọi thẳng đường dẫn đơn ngoài phạm vi vẫn bị chặn"""
    don = _len_don(nguoi_dung["staff_sale_1"], san_pham)
    client.force_login(nguoi_dung["staff_mkt"])
    assert client.get(f"/don-hang/{don.code}/").status_code == 404


def test_chi_nguoi_len_don_moi_bo_duoc(client, bang_van_don, san_pham, nguoi_dung):
    """BR-3 — Người khác không bỏ được đơn của mình, kể cả Manager"""
    don = _len_don(nguoi_dung["staff_sale_1"], san_pham)
    client.force_login(nguoi_dung["manager_sale"])

    client.post(f"/don-hang/{don.code}/bo/")
    assert Order.objects.filter(pk=don.pk).exists()


# ══ Nhật ký và hiệu năng ═══════════════════════════════════════════

def test_len_don_sinh_dong_nhat_ky(bang_van_don, san_pham, nguoi_dung):
    """AC-9.2 — Lên đơn sinh dòng nhật ký, ghi rõ khách và tổng tiền"""
    truoc = AuditLog.objects.filter(action=AuditAction.CREATE).count()
    don = _len_don(nguoi_dung["staff_sale_1"], san_pham)

    ds = AuditLog.objects.filter(action=AuditAction.CREATE)
    assert ds.count() == truoc + 2                 # một cho dòng bảng, một cho đơn
    chi_tiet = ds.latest("created_at").detail
    assert don.code in chi_tiet
    assert "0912345678" in chi_tiet


def test_man_hinh_don_hang_khong_qua_muoi_lenh_truy_van(
        client, bang_van_don, san_pham, nguoi_dung, django_assert_max_num_queries):
    """AC-10.2 — Màn hình danh sách đơn chạy không quá 10 lệnh truy vấn"""
    for i in range(5):
        _len_don(nguoi_dung["staff_sale_1"], san_pham, phone=f"09000000{i:02d}")

    client.force_login(nguoi_dung["manager_sale"])
    client.get("/don-hang/")                       # lượt đầu ghi mốc phiên
    with django_assert_max_num_queries(10):
        assert client.get("/don-hang/").status_code == 200


def test_ma_don_khong_trung_trong_cung_ngay(bang_van_don, san_pham, nguoi_dung):
    """Mã đơn sinh tự động không trùng nhau trong cùng một ngày"""
    ma = {_len_don(nguoi_dung["staff_sale_1"], san_pham,
                   phone=f"09111111{i:02d}").code for i in range(5)}
    assert len(ma) == 5
