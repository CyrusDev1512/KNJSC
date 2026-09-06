"""Trang chủ KN CRM — cây Bộ phận ▸ Quý ▸ Tháng ▸ bảng, `docs/04` mục 11, ADR-012.

Chạy ở app KN CRM (`conftest.py` đặt URLconf 8021). Mỗi bài phân quyền kiểm
cả hai chiều: nhánh được xem có mặt, nhánh ngoài phạm vi không có; `bp` ngoài
phạm vi trả 404 chứ không phải trang rỗng (quy tắc 8).
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
    bang = TableDef.objects.create(
        name="Đơn hàng Sale", code="don_sale",
        department=departments["sale"], created_by=nguoi_dung["manager_sale"],
    )
    for i, (ten, ma, kieu, nhan) in enumerate([
        ("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
        ("Khách hàng", "khach", FieldType.TEXT, Meaning.CUSTOMER),
    ]):
        ColumnDef.objects.create(table=bang, name=ten, code=ma, field_type=kieu, meaning=nhan, order=i)
    return bang


@pytest.fixture
def bang_khong_ngay(departments, nguoi_dung):
    """Bảng của Sale không có cột Ngày: chỉ nằm ở Toàn bộ, không xếp theo tháng."""
    bang = TableDef.objects.create(
        name="Danh mục Sale", code="danh_muc_sale",
        department=departments["sale"], created_by=nguoi_dung["manager_sale"],
    )
    ColumnDef.objects.create(table=bang, name="Tên", code="ten", field_type=FieldType.TEXT, order=0)
    return bang


def _dong(bang, nguoi, **gia_tri):
    return record_service.create_record(bang, gia_tri, actor=nguoi)


@pytest.fixture
def du_lieu(bang_vd, bang_sale, bang_khong_ngay, nguoi_dung):
    vd = nguoi_dung["staff_vd"]
    for i, ngay in enumerate(["2026-09-01", "2026-09-15", "2026-08-30", "2026-04-02"]):
        _dong(bang_vd, vd, ma_don=f"DH-{i}", ngay=ngay, ten_khach=f"K{i}", so_dien_thoai=f"09{i}")
    _dong(bang_sale, nguoi_dung["staff_sale_1"], ngay="2026-09-03", khach="A")
    _dong(bang_sale, nguoi_dung["staff_sale_2"], ngay="2026-09-04", khach="B")      # team khác
    _dong(bang_khong_ngay, nguoi_dung["staff_sale_1"], ten="X")
    return {"vd": bang_vd, "sale": bang_sale, "khong_ngay": bang_khong_ngay}


def _trang(client, **tham_so):
    kq = client.get("/", tham_so)
    return kq, (kq.content.decode() if kq.status_code == 200 else "")


# ══ Cây theo phạm vi — AC-11.28 ════════════════════════════════════

def test_trang_chu_theo_pham_vi_quyen(client, du_lieu, nguoi_dung, departments, django_assert_max_num_queries):
    """AC-11.28 — Trang chủ KN CRM: cây Bộ phận ▸ Quý ▸ Tháng chỉ dựng từ bảng trong phạm vi (Vận đơn không thấy nhánh Sale và ngược lại, Admin thấy mọi bộ phận, bảng được cấp quyền Xem hiện với nhãn Xem); số dòng theo tháng đúng phạm vi cấp bậc; `bp` ngoài phạm vi 404; trong ngân sách truy vấn của lưới"""
    # Vận đơn: thấy nhánh Vận đơn với quý 3 (tháng 9: 2 dòng, tháng 8: 1) và quý 2 (tháng 4: 1)
    client.force_login(nguoi_dung["staff_vd"])
    with django_assert_max_num_queries(14):          # cùng ngân sách với lưới — backlog K24
        kq, html = _trang(client, thang="2026-09")
    assert kq.status_code == 200
    assert "Vận đơn" in html and "Sale" not in html.split("crm-noi-dung")[0].split("crm-cay")[1]
    assert "Quý 3/2026" in html and "Quý 2/2026" in html and "Quý 1/2026" not in html
    assert 'aria-current="page">Tháng 9/2026 <span class="crm-so">2</span>' in html
    assert "Tháng 8/2026 <span class=\"crm-so\">1</span>" in html
    assert "Tháng 4/2026 <span class=\"crm-so\">1</span>" in html
    assert kq.context["tieu_de"] == "Vận đơn · Tháng 9/2026"
    # Nhánh Sale không có với Vận đơn, kể cả gõ thẳng bp → 404, không phải trang rỗng
    assert client.get("/", {"bp": "sale"}).status_code == 404
    assert client.get("/", {"bp": "khong-co"}).status_code == 404

    # Sale staff: chỉ dòng của mình đếm vào tháng (AC-3.1), không thấy Vận đơn
    client.force_login(nguoi_dung["staff_sale_1"])
    kq, html = _trang(client, thang="2026-09")
    assert kq.context["bp"].code == "sale"
    assert "Tháng 9/2026 <span class=\"crm-so\">1</span>" in html
    assert "Vận đơn" not in html.split("crm-cay")[1].split("crm-noi-dung")[0]
    # Manager Sale đếm cả bộ phận
    client.force_login(nguoi_dung["manager_sale"])
    kq, html = _trang(client, thang="2026-09")
    assert "Tháng 9/2026 <span class=\"crm-so\">2</span>" in html
    assert "Cấp quyền" in html and 'id="crm-form-thu-muc"' in html      # Manager quản lý thư mục

    # Admin: mọi bộ phận có bảng
    client.force_login(nguoi_dung["admin"])
    kq, html = _trang(client)
    cay = html.split("crm-cay")[1].split("crm-noi-dung")[0]
    assert "Vận đơn" in cay and "Sale" in cay and "Marketing" not in cay      # Marketing chưa có bảng

    # Marketing được cấp quyền XEM bảng Sale: thấy nhánh Sale với nhãn Xem, không thấy Vận đơn
    mkt = nguoi_dung["staff_mkt"]
    assert client.force_login(mkt) is None and client.get("/").status_code == 404   # chưa có bảng nào
    grant_service.grant(table=du_lieu["sale"], user=mkt, action=GrantAction.VIEW, actor=nguoi_dung["manager_sale"])
    grant_service.clear_cache(mkt)
    kq, html = _trang(client, bp="sale", **{"tat-ca": "1"})
    assert kq.status_code == 200 and "Đơn hàng Sale" in html
    assert '<span class="chip">Xem</span>' in html and "Vận đơn" not in html.split("crm-cay")[1].split("crm-noi-dung")[0]
    assert "Danh mục Sale" not in html                                    # bảng không được cấp

    client.logout()
    kq = client.get("/")
    assert kq.status_code == 302 and "/dang-nhap/" in kq["Location"]


# ══ Tháng là góc nhìn — AC-11.29 ═══════════════════════════════════

def test_bam_thang_mo_luoi_loc_dung_thang(client, du_lieu, nguoi_dung):
    """AC-11.29 — Nút tháng mở lưới với bộ lọc khoảng ngày đúng ngày đầu và cuối tháng, lưới trả đúng số dòng của tháng và ghi nhãn tháng trên thanh trên, nút ← về đúng nhánh; bảng không có cột Ngày chỉ nằm ở Toàn bộ bảng"""
    client.force_login(nguoi_dung["manager_sale"])
    kq, html = _trang(client, thang="2026-09")
    assert kq.status_code == 200
    url = "/bang-tinh/don_sale/?f_ngay__lon_bang=2026-09-01&amp;f_ngay__nho_bang=2026-09-30"
    assert url in html, "nút Mở phải mang bộ lọc đúng tháng"
    assert "Danh mục Sale" not in html                    # không có cột Ngày → không ở góc nhìn tháng
    assert '<span class="chip chip-nhan">Sửa</span>' in html

    luoi = client.get("/bang-tinh/don_sale/", {"f_ngay__lon_bang": "2026-09-01", "f_ngay__nho_bang": "2026-09-30"})
    assert luoi.status_code == 200
    assert luoi.context["page_obj"].paginator.count == 2
    assert luoi.context["thang_dang_xem"].label == "Tháng 9/2026"
    html_luoi = luoi.content.decode()
    assert "Tháng 9/2026" in html_luoi
    assert 'href="/?bp=sale&amp;thang=2026-09"' in html_luoi or 'href="/?bp=sale&thang=2026-09"' in html_luoi, "← phải về đúng nhánh"
    # Tháng 2 năm nhuận: ngày cuối đúng
    assert tree_service.Month(2028, 2).last == date(2028, 2, 29)
    # Lọc không trọn tháng thì không có nhãn
    luoi = client.get("/bang-tinh/don_sale/", {"f_ngay__lon_bang": "2026-09-02", "f_ngay__nho_bang": "2026-09-30"})
    assert luoi.context["thang_dang_xem"] is None

    # Toàn bộ bảng: có cả bảng không cột Ngày, nút Mở không mang bộ lọc
    kq, html = _trang(client, bp="sale", **{"tat-ca": "1"})
    assert "Danh mục Sale" in html and "không có cột Ngày" in html
    assert 'href="/bang-tinh/danh_muc_sale/"' in html
    assert kq.context["tieu_de"] == "Sale · Toàn bộ bảng"

    # Quý gõ tay chưa có dữ liệu vẫn mở với ba tháng trống, tháng sai dạng thì về mặc định
    kq, html = _trang(client, quy="2025-4")
    assert kq.status_code == 200 and "Quý 4/2025" in html and "Tháng 12/2025" in html
    assert client.get("/", {"thang": "abc"}).status_code == 200

    # Vận đơn: bảng vận đơn ở KN CRM sửa được → nhãn Sửa; tắt (bảng chỉ xem) → nhãn Xem
    client.force_login(nguoi_dung["staff_vd"])
    with SUA_DUOC:
        assert '<span class="chip chip-nhan">Sửa</span>' in _trang(client)[1]
    assert '<span class="chip">Xem</span>' in _trang(client)[1]


def test_tree_service_dung_mot_truy_van_moi_bang_dem(du_lieu, nguoi_dung, django_assert_max_num_queries):
    """AC-11.28 — `tree_service`: đếm theo tháng và thống kê bảng mỗi thứ một truy vấn cho cả bộ phận; quý mới trước, quý hiện tại luôn có; tháng trong quý mới trước"""
    vd = nguoi_dung["staff_vd"]
    # Một lệnh đếm, cộng tối đa một lệnh của phạm vi quyền (`in_scope` đọc phần cấp thêm)
    with django_assert_max_num_queries(2):
        dem = tree_service.month_counts(vd, du_lieu["vd"].department)
    assert dem[(du_lieu["vd"].pk, 2026, 9)] == 2 and dem[(du_lieu["vd"].pk, 2026, 4)] == 1
    with django_assert_max_num_queries(2):
        tk = tree_service.table_stats(vd, du_lieu["vd"].department)
    assert tk[du_lieu["vd"].pk][0] == 4
    cac_quy = tree_service.quarters(dem, hom_nay=date(2027, 1, 10))
    assert [(q.year, q.quarter) for q in cac_quy] == [(2027, 1), (2026, 3), (2026, 2)]
    assert [m.month for m in cac_quy[1].months] == [9, 8, 7]
    assert cac_quy[1].count == 3 and cac_quy[0].count == 0
    assert tree_service.parse_month("2026-13") is None and tree_service.parse_quarter("2026-5") is None
