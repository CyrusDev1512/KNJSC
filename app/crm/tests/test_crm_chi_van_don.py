"""KN CRM chỉ còn một bảng Vận đơn — ADR-040, chủ dự án chốt 24.09.2026.

Bảng Sale và Marketing nhập – xuất đều bên KN ERP; KN CRM chỉ phục vụ bảng vận
đơn và bỏ cấp Quý ▸ Tháng. **Dữ liệu không đổi một dòng nào** — bảng thường chỉ
không hiện và không mở được ở dịch vụ 8021; ERP và Thống kê đọc như cũ.
"""
import pytest
from django.test import override_settings

from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, DataRecord, TableDef
from forms_builder.services import record_service
from orders.services import dispatch_service

pytestmark = pytest.mark.django_db

ERP = override_settings(ROOT_URLCONF="knjsc.urls")


@pytest.fixture
def hai_bang(departments, nguoi_dung, settings):
    settings.GRID_ONLY_TABLES = set()
    vd = dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    mkt = TableDef.objects.create(name="Báo cáo Marketing", code="bao_cao_mkt_thu",
                                  department=departments["mkt"], created_by=nguoi_dung["manager_mkt"])
    for i, (ten, ma, kieu, nhan) in enumerate([
        ("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
        ("Marketer", "marketer", FieldType.TEXT, ""),
    ]):
        ColumnDef.objects.create(table=mkt, name=ten, code=ma, field_type=kieu, meaning=nhan, order=i)
    dong_vd = record_service.create_record(vd, {"ma_don": "AD40-1", "ten_khach": "A", "so_dien_thoai": "0900",
                                                "ngay": "2026-09-24", "loai_tien": "USD"}, actor=nguoi_dung["staff_vd"])
    dong_mkt = record_service.create_record(mkt, {"ngay": "2026-09-24", "marketer": "ANHPM"},
                                            actor=nguoi_dung["staff_mkt"])
    return vd, mkt, dong_vd, dong_mkt


def test_crm_tu_choi_moi_cua_cua_bang_thuong(client, hai_bang, nguoi_dung):
    """AC-40.2 — KN CRM từ chối bảng thường ở mọi cửa (404/403 như ngoài phạm vi,
    kể cả Admin): lưới, JSON đọc/ghi/lịch sử, xuất, hộp lọc, cột, nhập tệp, cấp
    quyền, mẫu nhập; bảng vận đơn vẫn phục vụ bình thường — kiểm cả hai chiều"""
    vd, mkt, dong_vd, dong_mkt = hai_bang
    client.force_login(nguoi_dung["admin"])
    ma = mkt.code
    assert client.get(f"/bang-tinh/{ma}/").status_code == 404
    for duong in ("du-lieu/", "lich-su/", "moi-nhat/", "xuat/", "loc/ngay/"):
        assert client.get(f"/bang-tinh/{ma}/{duong}").status_code in (403, 404), duong
    assert client.post(f"/bang-tinh/{ma}/luu-json/", {}, content_type="application/json").status_code in (403, 404)
    for duong in ("cot/", "nhap/", "cap-quyen/", "mau-nhap.xlsx"):
        assert client.get(f"/bang/{ma}/{duong}").status_code == 404, duong
    # Chiều được phép: bảng vận đơn vẫn nguyên
    assert client.get(f"/bang-tinh/{vd.code}/").status_code == 200
    assert client.get(f"/bang-tinh/{vd.code}/du-lieu/").json()["total"] == 1


def test_trang_chu_va_thu_muc_chi_nhac_van_don(client, hai_bang, nguoi_dung):
    """AC-40.1 — Trang chủ KN CRM (ô số, Bảng gần đây, Hoạt động gần đây) và trang
    thư mục chỉ nhắc tới bảng vận đơn; bảng thường không xuất hiện dù người xem là
    Admin hay chính bộ phận sở hữu"""
    vd, mkt, dong_vd, dong_mkt = hai_bang
    client.force_login(nguoi_dung["admin"])
    kq = client.get("/")
    sl = kq.context["so_lieu"]["data"]
    assert sl["so_bang"] == 1 and sl["so_dong"] == 1                  # chỉ đếm vận đơn
    assert [b.code for b in kq.context["bang"]["data"]] == [vd.code]
    hoat_dong = " ".join(h.detail for h in kq.context["hoat_dong"]["data"])
    assert mkt.code not in hoat_dong and str(dong_mkt.pk) not in [
        h.target_id for h in kq.context["hoat_dong"]["data"] if h.target_type == "DataRecord"]
    html = client.get("/thu-muc/").content.decode()
    assert "Vận đơn mới" in html and mkt.name not in html and "Quý" not in html


def test_du_lieu_khong_doi_va_erp_nguyen_ven(client, hai_bang, nguoi_dung):
    """AC-40.3 — Dữ liệu bảng thường không đổi một dòng nào: KN ERP vẫn xem Bảng
    dữ liệu, cột, quản lý như cũ; dòng và cột của bảng thường còn nguyên trong DB"""
    vd, mkt, dong_vd, dong_mkt = hai_bang
    with ERP:
        client.force_login(nguoi_dung["admin"])
        kq = client.get(f"/bang/{mkt.code}/")
        assert kq.status_code == 200
        assert [d.pk for d, _ in kq.context["cac_dong"]] == [dong_mkt.pk]
        assert client.get(f"/bang/{mkt.code}/cot/").status_code == 200
    dong_mkt.refresh_from_db()
    assert dong_mkt.data == {"ngay": "2026-09-24", "marketer": "ANHPM"}
    assert DataRecord.objects.filter(table=mkt).count() == 1
    assert mkt.columns.count() == 2
