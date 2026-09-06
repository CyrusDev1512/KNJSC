"""Khung KN CRM có sidebar — ADR-013, AC-11.31 và AC-11.32.

Trang chủ `/` là tổng quan theo phạm vi; mục Bảng tính trên sidebar mở trang
thư mục `/thu-muc/`; bấm bảng mới mở lưới toàn màn hình; ← của lưới về trang
thư mục, không bao giờ về KN ERP. Phạm vi kiểm cả hai chiều: Sale không thấy
nhánh Vận đơn trên sidebar và ngược lại.
"""
import pytest

from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, TableDef
from forms_builder.services import record_service
from orders.services import dispatch_service

pytestmark = pytest.mark.django_db


@pytest.fixture
def du_lieu(departments, nguoi_dung):
    vd = dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    sale = TableDef.objects.create(
        name="Đơn hàng Sale", code="don_sale",
        department=departments["sale"], created_by=nguoi_dung["manager_sale"],
    )
    ColumnDef.objects.create(table=sale, name="Ngày", code="ngay", field_type=FieldType.DATE, meaning=Meaning.DATE, order=0)
    ColumnDef.objects.create(table=sale, name="Khách", code="khach", field_type=FieldType.TEXT, order=1)
    for i in range(3):
        record_service.create_record(vd, {"ma_don": f"DH-{i}", "ngay": "2026-09-01", "ten_khach": f"K{i}", "so_dien_thoai": f"09{i}"}, actor=nguoi_dung["staff_vd"])
    record_service.create_record(sale, {"ngay": "2026-09-03", "khach": "A"}, actor=nguoi_dung["staff_sale_1"])
    record_service.create_record(sale, {"ngay": "2026-09-04", "khach": "B"}, actor=nguoi_dung["staff_sale_2"])
    return {"vd": vd, "sale": sale}


def _sidebar(html):
    return html.split('id="thanh-ben"')[1].split('<div class="chinh">')[0]


def test_trang_chu_tong_quan_co_sidebar_theo_pham_vi(client, du_lieu, nguoi_dung, django_assert_max_num_queries):
    """AC-11.31 — Trang chủ KN CRM là tổng quan theo phạm vi (Staff chỉ đếm dòng của mình), có sidebar avatar + Trang chủ + Bảng tính với mục con là bộ phận trong phạm vi, không có nút ←; Leader thấy Tạo bảng; người không có bảng vẫn vào được; chưa đăng nhập chuyển về đăng nhập; trong ngân sách truy vấn"""
    kq = client.get("/")
    assert kq.status_code == 302 and "/dang-nhap/" in kq["Location"]

    client.force_login(nguoi_dung["staff_vd"])
    with django_assert_max_num_queries(14):
        kq = client.get("/")
    assert kq.status_code == 200
    html = kq.content.decode()
    assert 'id="thanh-ben"' in html and 'class="bt-ve"' not in html
    ben = _sidebar(html)
    assert "Trang chủ" in ben and "Bảng tính" in ben and "Vận đơn" in ben and "Sale" not in ben
    assert 'href="/thu-muc/"' in ben and 'href="/thu-muc/?bp=van-don"' in ben
    assert "KN ERP" in ben and "Tác vụ nền" in ben
    sl = kq.context["so_lieu"]["data"]
    assert sl["so_bang"] == 1 and sl["so_dong"] == 3 and sl["dong_thang"] == 3 and sl["dong_hom_nay"] == 3
    assert [b.code for b in kq.context["bang"]["data"]] == ["van_don"]
    assert kq.context["duoc_tao_bang"] is False and "+ Tạo bảng" not in html
    assert kq.context["hoat_dong"]["ok"]

    # Sale Staff: chỉ dòng của mình, sidebar không có Vận đơn
    client.force_login(nguoi_dung["staff_sale_1"])
    kq = client.get("/")
    sl = kq.context["so_lieu"]["data"]
    assert sl["so_dong"] == 1 and sl["so_bang"] == 1
    ben = _sidebar(kq.content.decode())
    assert "Sale" in ben and "Vận đơn" not in ben
    # Leader Sale: cả team, thấy nút Tạo bảng
    client.force_login(nguoi_dung["leader_sale_1"])
    kq = client.get("/")
    assert kq.context["duoc_tao_bang"] is True and "+ Tạo bảng" in kq.content.decode()
    assert kq.context["so_lieu"]["data"]["so_dong"] == 1        # staff_sale_2 ở team khác
    # Admin: mọi bộ phận có bảng
    client.force_login(nguoi_dung["admin"])
    ben = _sidebar(client.get("/").content.decode())
    assert "Sale" in ben and "Vận đơn" in ben
    # Marketing chưa có bảng nào: trang chủ vẫn 200, số bảng 0 (không phải 404 như trang thư mục)
    client.force_login(nguoi_dung["staff_mkt"])
    kq = client.get("/")
    assert kq.status_code == 200 and kq.context["so_lieu"]["data"]["so_bang"] == 0
    assert client.get("/thu-muc/").status_code == 404


def test_bang_tinh_thu_muc_roi_luoi_va_quay_ve(client, du_lieu, nguoi_dung):
    """AC-11.32 — Mục Bảng tính mở trang thư mục có sidebar và mục con bộ phận đang chọn; lưới toàn màn hình không sidebar; ← của lưới về đúng trang thư mục và nhánh, không về KN ERP"""
    client.force_login(nguoi_dung["staff_vd"])
    kq = client.get("/thu-muc/")
    assert kq.status_code == 200 and kq.context["bp"].code == "van-don"
    html = kq.content.decode()
    assert 'id="thanh-ben"' in html and 'class="bt-ve"' not in html
    assert 'class="nav-muc crm-con crm-dang" href="/thu-muc/?bp=van-don" aria-current="page"' in html
    assert "Đơn hàng Sale" not in html

    luoi = client.get("/bang-tinh/van_don/")
    assert luoi.status_code == 200
    html = luoi.content.decode()
    assert 'id="thanh-ben"' not in html
    assert 'class="bt-ve" href="/thu-muc/?bp=van-don&amp;tat-ca=1"' in html
    assert "Về Bảng tính" in html
    luoi = client.get("/bang-tinh/van_don/", {"f_ngay__lon_bang": "2026-09-01", "f_ngay__nho_bang": "2026-09-30"})
    assert 'class="bt-ve" href="/thu-muc/?bp=van-don&amp;thang=2026-09"' in luoi.content.decode()
    # Sale không mở được nhánh Vận đơn, kể cả gõ thẳng
    client.force_login(nguoi_dung["staff_sale_1"])
    assert client.get("/thu-muc/", {"bp": "van-don"}).status_code == 404
