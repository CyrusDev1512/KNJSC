"""Luồng làm việc xuyên suốt ba bộ phận — một ngày của công ty.

`docs/04` mục 13 điều 6 đòi *"ba vai trò đã chạy trọn quy trình trên dữ liệu
thật"*. Bài này chạy trọn quy trình đó bằng mã, đi qua HTTP như người dùng
thật, không gọi tắt tầng dịch vụ.

    Quản lý Marketing dựng bảng và biểu mẫu
        ↓
    Nhân viên Marketing nộp báo cáo ngày        → cột tính sẵn tự tính
        ↓
    Nhân viên Sale lên đơn                      → sinh dòng bảng vận đơn
        ↓
    Nhân viên Vận đơn cập nhật trạng thái       → sửa ô ngay trên bảng
        ↓
    Quản lý mở nhật ký                          → thấy đủ dấu vết

Khác các tệp kiểm thử khác ở chỗ: chúng kiểm từng mảnh, bài này kiểm **các
mảnh nối được với nhau**. Nhiều lỗi chỉ lộ ra ở chỗ nối — như lỗi bộ phận Vận
đơn không thấy dòng nào, đã xảy ra thật ở Giai đoạn 5.
"""
from datetime import date
from decimal import Decimal

import pytest
from django.test import override_settings

from core.constants import AuditAction
from core.models import AuditLog
from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, ComputeOp, DataRecord, FieldDef, TableDef
from forms_builder.services import form_service
from orders.models import Order, Product, ProductGroup
from orders.services import dispatch_service
from reports.models import DailyReport

pytestmark = pytest.mark.django_db

NGAY = date(2026, 8, 28)


def _lay_the(client, duong_dan):
    """Lấy thẻ chống giả mạo trên một trang, như trình duyệt vẫn làm."""
    kq = client.get(duong_dan)
    assert kq.status_code == 200, f"{duong_dan} trả {kq.status_code}"
    return kq.cookies["csrftoken"].value


def test_mot_ngay_cua_cong_ty(client, departments, teams, nguoi_dung):
    """docs/04 mục 13 điều 6 — Ba vai trò chạy trọn quy trình của mình

    Đây là bài dài nhất trong bộ kiểm thử, và cố ý như vậy: nó kiểm chỗ nối
    giữa ba module, không kiểm từng module.
    """
    mkt_ql, mkt_nv = nguoi_dung["manager_mkt"], nguoi_dung["staff_mkt"]
    sale_nv, vd_nv = nguoi_dung["staff_sale_1"], nguoi_dung["staff_vd"]

    # ── 1. Quản lý Marketing dựng bảng và biểu mẫu ──
    bang = TableDef.objects.create(
        name="Báo cáo Marketing", code="bc_mkt",
        department=departments["mkt"], created_by=mkt_ql,
    )
    for i, (ten, ma, kieu, nhan) in enumerate([
        ("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
        ("Số Mess", "so_mess", FieldType.INTEGER, ""),
        ("Số đơn", "so_don", FieldType.INTEGER, ""),
        ("Doanh số", "doanh_so", FieldType.MONEY, Meaning.REVENUE),
    ]):
        ColumnDef.objects.create(
            table=bang, name=ten, code=ma, field_type=kieu, meaning=nhan, order=i)
    ColumnDef.objects.create(
        table=bang, name="Tỉ lệ chốt", code="ti_le_chot", field_type=FieldType.DECIMAL,
        order=4, is_computed=True, compute_op=ComputeOp.PERCENT,
        compute_left="so_don", compute_right="so_mess", compute_decimals=2,
    )

    bm = form_service.create_form(
        name="Báo cáo Marketing ngày", code="bc_mkt_ngay",
        department=departments["mkt"], table=bang, actor=mkt_ql,
    )
    for ten, ma, kieu, nhan in [
        ("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
        ("Số Mess", "so_mess", FieldType.INTEGER, ""),
        ("Số đơn", "so_don", FieldType.INTEGER, ""),
        ("Doanh số", "doanh_so", FieldType.MONEY, Meaning.REVENUE),
    ]:
        truong = FieldDef.objects.create(
            name=ten, code=ma, field_type=kieu, meaning=nhan,
            department=departments["mkt"],
        )
        form_service.add_field(
            bm, truong, column=bang.columns.get(code=ma),
            required=(ma == "ngay"), actor=mkt_ql,
        )

    # ── 2. Nhân viên Marketing nộp báo cáo ngày, qua giao diện ──
    client.force_login(mkt_nv)
    kq = client.post("/bao-cao/", {
        "bieu_mau": "bc_mkt_ngay", "ngay_bao_cao": NGAY.isoformat(),
        "ngay": NGAY.isoformat(), "so_mess": "4303", "so_don": "291",
        "doanh_so": "1.425.942.850",          # gõ theo tập quán Việt Nam
    })
    assert kq.status_code == 302, "Nộp báo cáo không thành công"

    bao_cao = DailyReport.objects.get()
    assert bao_cao.record.data["ti_le_chot"] == "6.76"      # cột tính sẵn
    assert bao_cao.record.val_revenue == Decimal("1425942850.00")
    assert bao_cao.submitted_at is not None

    # Nộp đè lần hai thì bị chặn — BR-2
    lan_hai = client.post("/bao-cao/", {
        "bieu_mau": "bc_mkt_ngay", "ngay_bao_cao": NGAY.isoformat(),
        "ngay": NGAY.isoformat(), "so_mess": "1", "so_don": "1",
    })
    assert "đã nộp" in lan_hai.content.decode()
    assert DailyReport.objects.count() == 1

    # ── 3. Nhân viên Sale lên đơn, qua giao diện ──
    dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    nhom = ProductGroup.objects.create(name="Đồ gia dụng")
    Product.objects.create(name="Máy massage HM-200", code="hm200", group=nhom)

    client.force_login(sale_nv)
    the = _lay_the(client, "/len-don/")
    kq = client.post("/len-don/", {
        "csrfmiddlewaretoken": the,
        "phone": "0912345678", "customer_name": "Nguyễn Văn An",
        "email": "an@vidu.com", "market": "us", "state": "California",
        "city": "San Jose", "zipcode": "95112",
        "payment_method": "card", "currency": "USD",
        "sp_0": "hm200", "sl_0": "2", "gia_0": "150,00",   # phẩy thập phân
    })
    assert kq.status_code == 302, "Lên đơn không thành công"

    don = Order.objects.get()
    assert don.total == Decimal("300.00"), "Đọc sai số tiền người dùng gõ"
    assert don.record is not None, "Đơn chưa chảy sang bảng vận đơn"

    # ── 4. Nhân viên Vận đơn cập nhật trạng thái, ngay trên bảng ──
    client.force_login(vd_nv)
    bang_vd = dispatch_service.waybill_table()

    thay = DataRecord.objects.in_scope(vd_nv)
    assert thay.filter(pk=don.record_id).exists(), (
        "Vận đơn không thấy dòng do Sale lên — cả tính năng vô dụng"
    )

    # Ở Bảng dữ liệu chỉ xem (ADR-009); cập nhật là việc của Bảng tính — dịch
    # vụ `bangtinh` chạy cùng mã với `GRID_ONLY_TABLES` rỗng
    duong_dan = f"/bang/{bang_vd.code}/o/{don.record_id}/trang_thai_vc/"
    assert client.post(duong_dan, {"gia_tri": "Đang giao"}).status_code == 403
    with override_settings(GRID_ONLY_TABLES=set()):
        kq = client.post(duong_dan, {"gia_tri": "Đang giao"})
    assert kq.status_code == 200
    don.record.refresh_from_db()
    assert don.record.data["trang_thai_vc"] == "Đang giao"

    # Đơn gốc vẫn khoá — BR-3
    don.refresh_from_db()
    assert don.total == Decimal("300.00")

    # ── 5. Quản lý mở nhật ký, thấy đủ dấu vết ──
    client.force_login(nguoi_dung["admin"])
    assert client.get("/nhat-ky/").status_code == 200

    dau_vet = list(AuditLog.objects.order_by("created_at").values_list("detail", flat=True))
    assert any("Nộp báo cáo" in d for d in dau_vet), "Thiếu dấu vết nộp báo cáo"
    assert any("Lên đơn" in d for d in dau_vet), "Thiếu dấu vết lên đơn"
    assert any("Sửa ô" in d and "trang_thai_vc" in d for d in dau_vet), (
        "Thiếu dấu vết cập nhật trạng thái vận chuyển"
    )
    assert AuditLog.objects.filter(action=AuditAction.CREATE).count() >= 4


def test_moi_bo_phan_chi_thay_phan_cua_minh(client, departments, teams, nguoi_dung):
    """AC-3.5 — Ba bộ phận cùng làm việc nhưng không thấy dữ liệu của nhau

    Chạy sau bài trên: cùng một hệ thống, ba người mở ba màn hình, không ai
    thấy nhầm dữ liệu của ai.
    """
    dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])

    client.force_login(nguoi_dung["staff_mkt"])
    assert client.get("/len-don/").status_code == 403      # Marketing không lên đơn
    assert client.get("/bang/van_don/").status_code == 404  # không thấy bảng vận đơn

    client.force_login(nguoi_dung["staff_vd"])
    assert client.get("/len-don/").status_code == 403      # Vận đơn không lên đơn
    assert client.get("/bang/van_don/").status_code == 200  # nhưng thấy bảng của mình

    client.force_login(nguoi_dung["staff_sale_1"])
    assert client.get("/len-don/").status_code == 200      # Sale lên đơn được
    assert client.get("/bang/van_don/").status_code == 404  # không thấy bảng vận đơn
