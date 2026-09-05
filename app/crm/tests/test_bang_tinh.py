"""Bảng tính vận đơn — `docs/04` mục 11, ADR-009.

Chạy qua HTTP với cả hai cấu hình: dịch vụ chính (chỉ xem) và dịch vụ
`bangtinh` (sửa được — dựng lại bằng `GRID_ONLY_TABLES` rỗng). Mỗi bài phân
quyền kiểm cả hai chiều.
"""
from datetime import date
from pathlib import Path
from urllib.parse import quote

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from core.constants import AuditAction, JobStatus
from core.models import AuditLog
from forms_builder.services import import_service, record_service
from orders.constants import PaymentStatus, ShippingStatus
from orders.models import Product, ProductGroup
from orders.services import dispatch_service

pytestmark = pytest.mark.django_db

SUA_DUOC = override_settings(GRID_ONLY_TABLES=set())    # đúng cấu hình dịch vụ bangtinh


@pytest.fixture
def san_pham(db):
    nhom = ProductGroup.objects.create(name="Mỹ phẩm")
    return {
        "cream": Product.objects.create(name="Retinol Cream", code="retinol-cream", group=nhom),
        "serum": Product.objects.create(name="Retinol Serum", code="retinol-serum", group=nhom),
    }


@pytest.fixture
def bang_vd(departments, nguoi_dung, san_pham):
    return dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])


def _dong(bang, nguoi, **gia_tri):
    mac_dinh = {
        "ma_don": f"DH-{gia_tri.get('so_dien_thoai', '0')}-{gia_tri.get('ten_khach', 'x')}",
        "ngay": "2026-08-01", "trang_thai_vc": ShippingStatus.DA_LEN_DON.label,
    }
    return record_service.create_record(bang, {**mac_dinh, **gia_tri}, actor=nguoi)


@pytest.fixture
def du_lieu(bang_vd, nguoi_dung):
    """Bốn vận đơn: hai cùng số điện thoại, một đơn huỷ, một có ghi chú."""
    vd = nguoi_dung["staff_vd"]
    return {
        "an1": _dong(bang_vd, vd, ten_khach="Nguyễn An", so_dien_thoai="0911", ngay="2026-08-01",
                     trang_thai_vc="Đang giao", sl_retinol_cream=2, ghi_chu="Giao buổi tối"),
        "an2": _dong(bang_vd, vd, ten_khach="Nguyễn An", so_dien_thoai="0911", ngay="2026-08-05",
                     trang_thai_vc="Đã nhận hàng", sl_retinol_cream=1),
        "binh": _dong(bang_vd, vd, ten_khach="Trần Bình", so_dien_thoai="0922", ngay="2026-08-10",
                      trang_thai_vc="Hủy trước giao", sl_retinol_cream=5),
        "chi": _dong(bang_vd, vd, ten_khach="Lê Chi", so_dien_thoai="0933", ngay="2026-08-20",
                     trang_thai_vc="Hoàn đơn", ghi_chu="Khách đổi ý"),
    }


def _so_dong(client, qs=""):
    kq = client.get("/bang-tinh/" + qs)
    assert kq.status_code == 200
    return kq.context["page_obj"].paginator.count


# ══ Phân quyền — AC-11.4 ═══════════════════════════════════════════

def test_ngoai_bo_phan_van_don_bi_tu_choi_moi_duong_dan(client, du_lieu, nguoi_dung):
    """AC-11.4 — Sale các cấp và Marketing bị từ chối (404, như Bảng dữ liệu) ở mọi đường dẫn Bảng tính của bảng vận đơn, kể cả POST; Vận đơn và Admin vào được"""
    pk = du_lieu["an1"].pk
    cac_duong = [
        "/bang-tinh/van_don/", "/bang-tinh/van_don/loc/trang_thai_vc/",
        f"/bang-tinh/van_don/o/{pk}/ghi_chu/", "/bang-tinh/van_don/xuat/",
    ]
    for ma in ("staff_sale_1", "leader_sale_1", "manager_sale", "staff_mkt", "manager_mkt"):
        client.force_login(nguoi_dung[ma])
        for duong in cac_duong:
            assert client.get(duong).status_code == 404, f"{ma} vào được {duong}"
        assert client.post(f"/bang-tinh/van_don/o/{pk}/ghi_chu/", {"gia_tri": "x"}).status_code == 404
        assert client.post("/bang-tinh/van_don/dong-moi/", {"ma_don": "DH-x"}).status_code == 404
        # Bảng vận đơn không hiện trong danh sách bảng ở thanh bên của họ
        kq = client.get("/bang-tinh/")
        assert kq.status_code == 404 or "van_don" not in [b.code for b in kq.context["cac_bang"]]

    for ma in ("staff_vd", "admin"):
        client.force_login(nguoi_dung[ma])
        assert client.get("/bang-tinh/").context["bang"].code == "van_don", ma
        assert client.get("/bang-tinh/van_don/").status_code == 200
        assert client.get("/bang-tinh/van_don/loc/trang_thai_vc/").status_code == 200
        assert client.get("/bang-tinh/van_don/xuat/").status_code == 200

    client.logout()
    kq = client.get("/bang-tinh/van_don/")
    assert kq.status_code == 302 and "/dang-nhap/" in kq["Location"]


# ══ Lọc theo cột — AC-11.2 ═════════════════════════════════════════

def test_loc_tung_cot_va_cong_don(client, du_lieu, nguoi_dung):
    """AC-11.2 — Lọc danh sách giá trị, chứa chữ, khoảng ngày và số, ô trống; nhiều cột cộng dồn đúng số dòng"""
    client.force_login(nguoi_dung["staff_vd"])
    assert _so_dong(client) == 4
    # danh sách giá trị (nhiều tham số cùng tên)
    dg, hd = quote("Đang giao"), quote("Hoàn đơn")
    assert _so_dong(client, f"?f_trang_thai_vc__trong={dg}&f_trang_thai_vc__trong={hd}") == 2
    # cộng dồn với chứa chữ
    assert _so_dong(client, f"?f_trang_thai_vc__trong={dg}&f_trang_thai_vc__trong={hd}&f_ten_khach__chua=An") == 1
    # khoảng ngày trên cột tách
    assert _so_dong(client, "?f_ngay__lon_bang=2026-08-05&f_ngay__nho_bang=2026-08-10") == 2
    # khoảng số trên cột JSON số nguyên (số lượng sản phẩm)
    assert _so_dong(client, "?f_sl_retinol_cream__lon_bang=2") == 2
    assert _so_dong(client, "?f_sl_retinol_cream__trong=5") == 1
    # ô trống và ô có giá trị
    assert _so_dong(client, "?f_ghi_chu__rong=1") == 2
    assert _so_dong(client, "?f_ghi_chu__co=1") == 2
    # cột lạ và phép lạ bị bỏ qua, không nổ
    assert _so_dong(client, "?f_khong_co__trong=a&f_ngay__bay=1") == 4

    # chip "đang lọc" và liên kết bỏ đúng một bộ lọc
    kq = client.get(f"/bang-tinh/?f_trang_thai_vc__trong={dg}&f_ten_khach__chua=An")
    chips = dict(kq.context["chips"])
    assert any("Trạng thái vận chuyển" in nhan for nhan in chips)
    bo_ten = next(url for nhan, url in chips.items() if "Tên khách" in nhan)
    assert "f_ten_khach" not in bo_ten and "f_trang_thai_vc__trong" in bo_ten


def test_hop_loc_cot_liet_ke_gia_tri_kem_so_dem(client, du_lieu, nguoi_dung):
    """AC-11.2 — Hộp lọc của một cột liệt kê giá trị khác nhau kèm số dòng, thu hẹp được bằng ô tìm"""
    client.force_login(nguoi_dung["staff_vd"])
    kq = client.get("/bang-tinh/van_don/loc/trang_thai_vc/")
    tuy_chon = dict(kq.context["tuy_chon"])
    assert tuy_chon == {"Đang giao": 1, "Đã nhận hàng": 1, "Hủy trước giao": 1, "Hoàn đơn": 1}
    kq = client.get("/bang-tinh/van_don/loc/trang_thai_vc/?q=hủy")
    assert dict(kq.context["tuy_chon"]) == {"Hủy trước giao": 1}
    assert kq.context["loai"] == "danh_sach"
    assert client.get("/bang-tinh/van_don/loc/ngay/").context["loai"] == "khoang"
    assert client.get("/bang-tinh/van_don/loc/ghi_chu/").context["loai"] == "chua"
    assert client.get("/bang-tinh/van_don/loc/khong_co/").status_code == 404


# ══ Sửa ô — AC-11.3, AC-11.7 ═══════════════════════════════════════

def test_sua_o_dung_kieu_va_tu_choi_gia_tri_ngoai_danh_sach(client, du_lieu, nguoi_dung):
    """AC-11.3 — Ô danh sách chỉ nhận giá trị trong danh sách (không phân biệt hoa thường), giá trị lạ → 400 kèm lý do; mỗi lần sửa một dòng nhật ký"""
    dong = du_lieu["an1"]
    client.force_login(nguoi_dung["staff_vd"])
    duong = f"/bang-tinh/van_don/o/{dong.pk}/trang_thai_vc/"
    with SUA_DUOC:
        # trình sửa là ô chọn với đủ tám trạng thái
        html = client.get(duong).content.decode()
        assert "<select" in html and html.count("<option") == 1 + len(ShippingStatus)

        truoc = AuditLog.objects.filter(action=AuditAction.UPDATE).count()
        kq = client.post(duong, {"gia_tri": "Đã nhận hàng"})
        assert kq.status_code == 200 and "Đã nhận hàng" in kq.content.decode()
        dong.refresh_from_db()
        assert dong.data["trang_thai_vc"] == "Đã nhận hàng" and dong.val_status == "Đã nhận hàng"
        assert AuditLog.objects.filter(action=AuditAction.UPDATE).count() == truoc + 1

        kq = client.post(duong, {"gia_tri": "Bay lên trời"})
        assert kq.status_code == 400 and "không có trong danh sách" in kq.content.decode()
        dong.refresh_from_db()
        assert dong.data["trang_thai_vc"] == "Đã nhận hàng"

        # thanh toán: viết hoa kiểu tệp thật vẫn về đúng nhãn
        kq = client.post(f"/bang-tinh/van_don/o/{dong.pk}/trang_thai_tt/", {"gia_tri": "đã THANH toán"})
        assert kq.status_code == 200
        dong.refresh_from_db()
        assert dong.data["trang_thai_tt"] == PaymentStatus.PAID.label

        # nhân viên vận đơn là danh sách gợi ý: mã người lạ vẫn nhận
        html = client.get(f"/bang-tinh/van_don/o/{dong.pk}/nv_van_don/").content.decode()
        assert "<datalist" in html and "staff_vd" in html
        assert client.post(f"/bang-tinh/van_don/o/{dong.pk}/nv_van_don/", {"gia_tri": "PHUONGVH"}).status_code == 200

        # số lượng sản phẩm: ô số, "abc" bị từ chối
        assert "type=\"number\"" in client.get(f"/bang-tinh/van_don/o/{dong.pk}/sl_retinol_cream/").content.decode()
        assert client.post(f"/bang-tinh/van_don/o/{dong.pk}/sl_retinol_cream/", {"gia_tri": "abc"}).status_code == 400
        # ghi chú nhiều dòng
        assert "<textarea" in client.get(f"/bang-tinh/van_don/o/{dong.pk}/ghi_chu/").content.decode()
        # huỷ sửa trả về ô hiển thị
        assert 'class="o-sua' in client.get(duong + "?hien=1").content.decode()
        assert client.get(f"/bang-tinh/van_don/o/{dong.pk}/khong_co/").status_code == 404


def test_bang_du_lieu_chi_xem_bang_tinh_sua_duoc(client, du_lieu, nguoi_dung):
    """AC-11.7 — Ở dịch vụ chính ô không sửa được (403, lưới báo chỉ xem); cùng đường dẫn ở dịch vụ Bảng tính thì 200"""
    dong = du_lieu["an1"]
    client.force_login(nguoi_dung["staff_vd"])
    duong = f"/bang-tinh/van_don/o/{dong.pk}/ghi_chu/"
    kq = client.get("/bang-tinh/")
    assert kq.context["chi_xem"] is True
    assert 'class="o-xem' in kq.content.decode() and 'class="o-sua' not in kq.content.decode()
    assert client.get(duong).status_code == 403
    assert client.post(duong, {"gia_tri": "sửa ở chỗ sai"}).status_code == 403
    assert client.post(f"/bang/van_don/o/{dong.pk}/ghi_chu/", {"gia_tri": "sửa ở chỗ sai"}).status_code == 403
    dong.refresh_from_db()
    assert dong.data.get("ghi_chu") == "Giao buổi tối"

    with SUA_DUOC:
        kq = client.get("/bang-tinh/")
        assert kq.context["chi_xem"] is False and 'class="o-sua' in kq.content.decode()
        assert client.post(duong, {"gia_tri": "Đúng chỗ"}).status_code == 200
    dong.refresh_from_db()
    assert dong.data["ghi_chu"] == "Đúng chỗ"


# ══ Lọc trùng, màu dòng — AC-11.5, AC-11.6 ═════════════════════════

def test_loc_trung_dem_dung_va_to_mau(client, du_lieu, nguoi_dung):
    """AC-11.5 — Cột Lọc trùng đếm đúng số dòng cùng số điện thoại, tô màu khi > 1, lọc được chỉ số trùng"""
    client.force_login(nguoi_dung["staff_vd"])
    kq = client.get("/bang-tinh/")
    trung = {d["ban_ghi"].pk: d["so_trung"] for d in kq.context["cac_dong"]}
    assert trung[du_lieu["an1"].pk] == 2 and trung[du_lieu["an2"].pk] == 2
    assert trung[du_lieu["binh"].pk] == 1 and trung[du_lieu["chi"].pk] == 1
    assert kq.content.decode().count("o-trung\"") == 2
    assert _so_dong(client, "?trung=1") == 2
    # Số trống không tính là trùng với nhau
    _dong(du_lieu["an1"].table, nguoi_dung["staff_vd"], ten_khach="Không số 1", so_dien_thoai="")
    _dong(du_lieu["an1"].table, nguoi_dung["staff_vd"], ten_khach="Không số 2", so_dien_thoai="")
    assert _so_dong(client, "?trung=1") == 2


def test_dong_huy_va_hoan_duoc_to_mau(client, du_lieu, nguoi_dung):
    """AC-11.6 — Dòng Hủy trước giao, Hủy sau giao, Hoàn đơn mang lớp màu xấu; dòng khác thì không"""
    client.force_login(nguoi_dung["staff_vd"])
    lop = {d["ban_ghi"].pk: d["lop"] for d in client.get("/bang-tinh/").context["cac_dong"]}
    assert lop[du_lieu["binh"].pk] == "dong-xau" and lop[du_lieu["chi"].pk] == "dong-xau"
    assert lop[du_lieu["an1"].pk] == "" and lop[du_lieu["an2"].pk] == "dong-tot"
    html = client.get("/bang-tinh/").content.decode()
    assert html.count('<tr class="dong-xau"') == 2


# ══ Cột sản phẩm — AC-11.8 ═════════════════════════════════════════

def test_moi_san_pham_mot_cot_va_len_don_dien_tu_dong(bang_vd, san_pham, nguoi_dung):
    """AC-11.8 — Mỗi sản phẩm đang bán có cột số lượng; thêm sản phẩm → thêm cột; lên đơn điền số lượng, địa chỉ, lần mua"""
    from core.constants import Currency
    from orders.constants import Market, PaymentMethod
    from orders.services import order_service

    ma_cot = set(bang_vd.columns.values_list("code", flat=True))
    assert {"sl_retinol_cream", "sl_retinol_serum", "dia_chi", "nv_van_don", "mua_lai", "doi_soat"} <= ma_cot
    ten = dict(bang_vd.columns.values_list("code", "name"))
    assert ten["sl_retinol_cream"] == "Retinol Cream"

    moi = Product.objects.create(name="Sữa Rửa Mặt", code="sua-rua-mat", group=san_pham["cream"].group)
    assert dispatch_service.sync_product_columns(bang_vd) == 1
    assert "sl_sua_rua_mat" in set(bang_vd.columns.values_list("code", flat=True))
    assert dispatch_service.sync_product_columns(bang_vd) == 0, "chạy lại không thêm cột nữa"

    def len_don():
        return order_service.create_order(
            phone="0999", customer_name="Khách Canada", address_line="812 Yonge St",
            market=Market.CA, state="AB", city="Calgary", zipcode="T1Y1J1",
            payment_method=PaymentMethod.TRANSFER, currency=Currency.CAD,
            lines=[{"product": san_pham["cream"], "quantity": 3, "unit_price": "50.00"},
                   {"product": moi, "quantity": 1, "unit_price": "20.00"},
                   {"product": san_pham["cream"], "quantity": 2, "unit_price": "50.00"}],
            actor=nguoi_dung["staff_sale_1"],
        )

    don = len_don()
    d = don.record.data
    assert d["sl_retinol_cream"] == 5 and d["sl_sua_rua_mat"] == 1
    assert "sl_retinol_serum" not in d or d["sl_retinol_serum"] in (None, 0)
    assert d["dia_chi"] == "812 Yonge St" and d["mua_lai"] == 1
    assert d["loai_tien"] == "CAD" and d["quoc_gia"] == "Canada"
    assert d["trang_thai_vc"] == "Đã lên đơn" and d["trang_thai_tt"] == "Chưa thanh toán"
    don2 = len_don()
    assert don2.record.data["mua_lai"] == 2


# ══ Tệp thật — AC-11.9 ═════════════════════════════════════════════

def test_nhap_tep_van_don_that_khong_chinh_sua(departments, nguoi_dung):
    """AC-11.9 — Tệp vận đơn thật (ẩn danh) nhập trọn: 221 dòng vào, 0 lỗi, trạng thái và thanh toán khớp danh sách, điện thoại là chuỗi, số lượng là số"""
    from core.management.commands.du_lieu_mau import SAN_PHAM

    nhom = ProductGroup.objects.create(name="Mỹ phẩm")
    for ten, ma in SAN_PHAM:
        Product.objects.create(name=ten, code=ma, group=nhom)
    bang = dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])

    duong_dan = Path(__file__).resolve().parents[3] / "docs" / "tham-khao" / "vandon-mau.xlsx"
    with open(duong_dan, "rb") as f:
        tep = SimpleUploadedFile("vandon-mau.xlsx", f.read())
    job = import_service.prepare(bang, tep, actor=nguoi_dung["admin"])
    khop = {m["code"] for m in job.summary["mapping"]}
    assert {"sl_retinol_cream", "sl_retinol_serum", "sl_vitamin_c_cream", "sl_kem_chong_nang",
            "sl_retinol_eye_serum", "trang_thai_vc", "nv_van_don", "trang_thai_tt", "ngay_tt",
            "nguoi_chuyen_tien", "bill", "doi_soat", "mua_lai", "dia_chi"} <= khop
    bo_qua = {i["cot_tep"] for i in job.summary["ignored"]}
    assert "Lọc trùng" in bo_qua and "Định dạng Ngày" in bo_qua

    import_service.confirm(job, actor=nguoi_dung["admin"])
    job.refresh_from_db()
    assert job.status == JobStatus.DONE, job.error
    assert job.summary["created"] == 221 and job.summary["error_count"] == 0, job.summary["errors"][:5]

    from forms_builder.models import DataRecord

    dong = list(DataRecord.objects.filter(table=bang))
    assert len(dong) == 221
    nhan_vc = {d.data.get("trang_thai_vc") for d in dong} - {None}
    assert nhan_vc <= {c.label for c in ShippingStatus} and "Đã nhận hàng" in nhan_vc
    nhan_tt = {d.data.get("trang_thai_tt") for d in dong} - {None}
    assert nhan_tt == {"Đã thanh toán", "Chưa thanh toán", "Thanh toán 1 phần"}
    assert {d.data.get("doi_soat") for d in dong} - {None} == {"Đã về TK"}
    assert "PHUONGVH" in {d.data.get("nv_van_don") for d in dong}
    sdt = [d.data["so_dien_thoai"] for d in dong if d.data.get("so_dien_thoai")]
    assert sdt and all(isinstance(s, str) and not s.endswith(".0") for s in sdt)
    assert all(isinstance(d.data.get("sl_retinol_cream"), int) for d in dong if d.data.get("sl_retinol_cream") is not None)
    assert any(d.data.get("sl_kem_chong_nang") for d in dong), "cột gõ sai tên trong tệp vẫn vào đúng cột"
    assert any(d.val_date == date(2023, 10, 14) for d in dong), "chuỗi '0:58 14/10/2023' phải thành ngày"
    assert sum(1 for d in dong if d.data.get("ngay_tt")) > 50
