"""Trang thư mục KN CRM (mục Bảng tính, `/thu-muc/`) — Bộ phận ▸ thư mục ▸ bảng, `docs/04` mục 11, ADR-012, ADR-015.

Từ ADR-040 (24.09.2026) không còn cấp Quý ▸ Tháng và KN CRM chỉ phục vụ bảng
vận đơn — bài viết lại theo trang phẳng. Chạy ở app KN CRM (`conftest.py` đặt
URLconf 8021). Mỗi bài phân quyền kiểm cả hai chiều: nhánh được xem có mặt,
nhánh ngoài phạm vi không có; `bp` ngoài phạm vi trả 404 chứ không phải trang
rỗng (quy tắc 8).
"""
from datetime import date

import pytest
from django.test import override_settings

from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, GrantAction, TableDef
from forms_builder.services import grant_service, record_service
from orders.services import dispatch_service

from crm.services import tree_service

pytestmark = pytest.mark.django_db

HOM_NAY = date(2026, 9, 6)
SUA_DUOC = override_settings(GRID_ONLY_TABLES=set())


@pytest.fixture
def bang_vd(departments, nguoi_dung):
    return dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])


@pytest.fixture
def bang_sale(departments, nguoi_dung):
    # KN CRM chỉ phục vụ bảng vận đơn (ADR-040) — bảng đạo cụ mang workflow
    bang = TableDef.objects.create(
        name="Đơn hàng Sale", code="don_sale", workflow="waybill",
        department=departments["sale"], created_by=nguoi_dung["manager_sale"],
    )
    for i, (ten, ma, kieu, nhan) in enumerate([
        ("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
        ("Khách hàng", "khach", FieldType.TEXT, Meaning.CUSTOMER),
    ]):
        ColumnDef.objects.create(table=bang, name=ten, code=ma, field_type=kieu, meaning=nhan, order=i)
    return bang


@pytest.fixture
def bang_thuong(departments, nguoi_dung):
    """Bảng thường của Sale — theo ADR-040 KHÔNG hiện ở thư mục KN CRM."""
    bang = TableDef.objects.create(
        name="Danh mục Sale", code="danh_muc_sale",
        department=departments["sale"], created_by=nguoi_dung["manager_sale"],
    )
    ColumnDef.objects.create(table=bang, name="Tên", code="ten", field_type=FieldType.TEXT, order=0)
    return bang


def _dong(bang, nguoi, **gia_tri):
    return record_service.create_record(bang, gia_tri, actor=nguoi)


@pytest.fixture
def du_lieu(bang_vd, bang_sale, bang_thuong, nguoi_dung):
    vd = nguoi_dung["staff_vd"]
    for i, ngay in enumerate(["2026-09-01", "2026-09-15", "2026-08-30", "2026-04-02"]):
        _dong(bang_vd, vd, ma_don=f"DH-{i}", ngay=ngay, ten_khach=f"K{i}", so_dien_thoai=f"09{i}")
    _dong(bang_sale, nguoi_dung["staff_sale_1"], ngay="2026-09-03", khach="A")
    _dong(bang_sale, nguoi_dung["staff_sale_2"], ngay="2026-09-04", khach="B")      # team khác
    _dong(bang_thuong, nguoi_dung["staff_sale_1"], ten="X")
    return {"vd": bang_vd, "sale": bang_sale, "thuong": bang_thuong}


def _trang(client, **tham_so):
    kq = client.get("/thu-muc/", tham_so)
    return kq, (kq.content.decode() if kq.status_code == 200 else "")


# ══ Trang phẳng theo phạm vi — AC-11.28 (viết lại theo ADR-040) ═════

def test_trang_chu_theo_pham_vi_quyen(client, du_lieu, nguoi_dung, departments, django_assert_max_num_queries):
    """AC-11.28 — Trang thư mục KN CRM phẳng (Bộ phận ▸ thư mục ▸ bảng, không còn
    Quý/Tháng — ADR-040) chỉ dựng từ bảng vận đơn trong phạm vi: Vận đơn không thấy
    nhánh Sale và ngược lại, Admin thấy mọi bộ phận có bảng vận đơn, bảng được cấp
    quyền Xem hiện với nhãn Xem; bảng thường không có mặt; `bp` ngoài phạm vi 404"""
    client.force_login(nguoi_dung["staff_vd"])
    with django_assert_max_num_queries(14):          # cùng ngân sách với lưới — backlog K24
        kq, html = _trang(client)
    assert kq.status_code == 200 and kq.context["bp"].code == "van-don"
    cay = html.split("crm-cay")[1].split("crm-noi-dung")[0]
    assert "Vận đơn" in cay and "bp=sale" not in cay
    assert "Quý" not in html and "Vận đơn mới" in html
    assert kq.context["tieu_de"] == "Vận đơn"
    # Nhánh Sale không có với Vận đơn, kể cả gõ thẳng bp → 404, không phải trang rỗng
    assert client.get("/thu-muc/", {"bp": "sale"}).status_code == 404
    assert client.get("/thu-muc/", {"bp": "khong-co"}).status_code == 404

    # Sale staff: thấy nhánh Sale (bảng workflow vận đơn), không thấy Vận đơn;
    # bảng thường "Danh mục Sale" không có mặt (ADR-040)
    client.force_login(nguoi_dung["staff_sale_1"])
    kq, html = _trang(client)
    assert kq.context["bp"].code == "sale"
    assert "Đơn hàng Sale" in html and "Danh mục Sale" not in html
    assert "bp=van-don" not in html.split("crm-cay")[1].split("crm-noi-dung")[0]
    # Manager Sale: có quản lý thư mục và Cấp quyền
    client.force_login(nguoi_dung["manager_sale"])
    kq, html = _trang(client)
    assert "Cấp quyền" in html and 'id="crm-form-thu-muc"' in html
    assert "+ Tạo bảng" not in html                    # nút đã ẩn (ADR-040)

    # Admin: mọi bộ phận có bảng vận đơn; Marketing không có bảng nào
    client.force_login(nguoi_dung["admin"])
    kq, html = _trang(client)
    cay = html.split("crm-cay")[1].split("crm-noi-dung")[0]
    assert "bp=van-don" in cay and "bp=sale" in cay and "Marketing" not in cay

    # Marketing được cấp quyền XEM bảng Sale: thấy nhánh Sale với nhãn Xem
    mkt = nguoi_dung["staff_mkt"]
    assert client.force_login(mkt) is None and client.get("/thu-muc/").status_code == 404   # chưa có bảng nào
    grant_service.grant(table=du_lieu["sale"], user=mkt, action=GrantAction.VIEW, actor=nguoi_dung["manager_sale"])
    grant_service.clear_cache(mkt)
    kq, html = _trang(client, bp="sale")
    assert kq.status_code == 200 and "Đơn hàng Sale" in html
    assert '<span class="chip">Xem</span>' in html
    assert "bp=van-don" not in html.split("crm-cay")[1].split("crm-noi-dung")[0]
    assert "Danh mục Sale" not in html                                    # bảng thường + không được cấp

    client.logout()
    kq = client.get("/thu-muc/")
    assert kq.status_code == 302 and "/dang-nhap/" in kq["Location"]


# ══ Lọc thời gian là việc của lưới — AC-11.29 (viết lại theo ADR-040) ═══

def test_mo_bang_khong_mang_bo_loc_va_nhan_thang_tren_luoi(client, du_lieu, nguoi_dung):
    """AC-11.29 — Nút Mở trên thư mục dẫn thẳng tới lưới không mang bộ lọc (cấp
    Quý/Tháng đã bỏ); gõ URL bộ lọc trọn một tháng thì lưới vẫn ghi nhãn tháng,
    nút ← về đúng bộ phận không mang tham số; tham số `thang`/`quy`/`tat-ca` cũ
    trên URL bị bỏ qua, không nổ"""
    client.force_login(nguoi_dung["manager_sale"])
    kq, html = _trang(client)
    assert 'href="/bang-tinh/don_sale/"' in html, "nút Mở dẫn thẳng, không bộ lọc"
    assert "f_ngay__lon_bang" not in html

    luoi = client.get("/bang-tinh/don_sale/", {"f_ngay__lon_bang": "2026-09-01", "f_ngay__nho_bang": "2026-09-30"})
    assert luoi.status_code == 200
    assert client.get("/bang-tinh/don_sale/du-lieu/", {"f_ngay__lon_bang": "2026-09-01", "f_ngay__nho_bang": "2026-09-30"}).json()["total"] == 2
    assert luoi.context["thang_dang_xem"].label == "Tháng 9/2026"
    html_luoi = luoi.content.decode()
    assert "Tháng 9/2026" in html_luoi
    assert 'class="bt-ve" href="/thu-muc/?bp=sale"' in html_luoi, "← về đúng bộ phận"
    # Tháng 2 năm nhuận: ngày cuối đúng
    assert tree_service.Month(2028, 2).last == date(2028, 2, 29)
    # Lọc không trọn tháng thì không có nhãn
    luoi = client.get("/bang-tinh/don_sale/", {"f_ngay__lon_bang": "2026-09-02", "f_ngay__nho_bang": "2026-09-30"})
    assert luoi.context["thang_dang_xem"] is None

    # URL cũ còn tham số quý/tháng/tat-ca: bỏ qua, trang vẫn mở
    for cu in ({"thang": "2026-09"}, {"quy": "2025-4"}, {"tat-ca": "1"}, {"thang": "abc"}):
        assert client.get("/thu-muc/", cu).status_code == 200

    # Bỏ nhãn Sửa; bảng chỉ xem vẫn có nhãn Xem để phân biệt quyền.
    client.force_login(nguoi_dung["staff_vd"])
    with SUA_DUOC:
        assert '<span class="chip chip-nhan">Sửa</span>' not in _trang(client)[1]
    assert '<span class="chip">Xem</span>' in _trang(client)[1]


def test_tree_service_dung_mot_truy_van_moi_bang_dem(du_lieu, nguoi_dung, django_assert_max_num_queries):
    """AC-11.28 — `tree_service.table_stats` một truy vấn cho cả bộ phận;
    `month_of_params` chỉ nhận bộ lọc trọn tháng; bảng thường không vào
    `all_tables` (ADR-040)"""
    vd = nguoi_dung["staff_vd"]
    with django_assert_max_num_queries(2):
        tk = tree_service.table_stats(vd, du_lieu["vd"].department)
    assert tk[du_lieu["vd"].pk][0] == 4
    sale = nguoi_dung["manager_sale"]
    ma = [b.code for b in tree_service.all_tables(sale)]
    assert "don_sale" in ma and "danh_muc_sale" not in ma
    from django.http import QueryDict
    cot = list(du_lieu["sale"].columns.all())
    thang = tree_service.month_of_params(QueryDict("f_ngay__lon_bang=2026-09-01&f_ngay__nho_bang=2026-09-30"), cot)
    assert (thang.year, thang.month) == (2026, 9)
    assert tree_service.month_of_params(QueryDict("f_ngay__lon_bang=2026-09-02&f_ngay__nho_bang=2026-09-30"), cot) is None
