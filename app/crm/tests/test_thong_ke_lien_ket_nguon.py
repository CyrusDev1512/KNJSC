"""Nút "Mở dữ liệu", "Mở bảng nguồn" ở Thống kê KN CRM không dẫn tới trang 404 — AC-40.9 (TL-89, 12.10.2026).

Từ ADR-040 KN CRM chỉ phục vụ bảng vận đơn, nhưng Thống kê vẫn đọc nguồn Sale/MKT (AC-40.3) và trỏ nút sang lưới
`/bang-tinh/bao_cao_*/` — trang đó luôn 404. Chủ dự án chốt 12.10.2026: nguồn Sale/MKT mở Báo cáo tổng hợp KN ERP của
đúng nguồn đó, cùng khoảng ngày (mọi vai thấy nguồn trong Thống kê đều mở được); Vận đơn giữ lưới KN CRM; bảng khác
không có nút. Liên kết sang ERP giữ đúng host đang mở như mọi liên kết giữa hai dịch vụ (AC-1.10).
"""
import html as html_lib
import re
from datetime import date
from io import StringIO
from urllib.parse import parse_qs, urlsplit

import pytest
from django.core.management import call_command

from core.constants import Rank
from crm.services import statistics_profiles, statistics_service
from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import FormDef, TableDef
from orders.constants import ACTIVE_WAYBILL_TABLE_CODE
from orders.services import dispatch_service

from .test_executive_statistics import add_row, col, make_table

pytestmark = pytest.mark.django_db

TU, DEN = "2026-09-01", "2026-09-30"
KY = {"tu": TU, "den": DEN}
BAO_CAO = ("bao_cao_sale", "bao_cao_mkt")


@pytest.fixture
def he_thong(departments, nguoi_dung, make_user):
    """Như máy thật sau launcher: bảng vận đơn, Báo cáo Marketing, rồi `configure_erp_reports` tạo Báo cáo Sale và
    nguồn báo cáo ERP cho cả ba; thêm một bảng chung không có nguồn báo cáo. Mỗi báo cáo một dòng trong kỳ."""
    dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    mkt = make_table(departments["mkt"], nguoi_dung["manager_mkt"], "bao_cao_mkt", "Báo cáo Marketing", [
        col("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
        col("Marketer", "marketer", FieldType.TEXT, Meaning.SELLER),
        col("Sản phẩm", "san_pham", FieldType.TEXT, Meaning.PRODUCT),
        col("Số Mess", "so_mess"), col("CPQC", "cpqc", FieldType.MONEY),
        col("Số đơn", "so_don"),
        col("Doanh số", "doanh_so", FieldType.MONEY, Meaning.REVENUE),
    ])
    FormDef.objects.create(table=mkt, department=mkt.department, code="bc_mkt_ngay", name="Báo cáo Marketing ngày")
    call_command("configure_erp_reports", stdout=StringIO())
    sale = TableDef.objects.get(code="bao_cao_sale")
    make_table(departments["sale"], nguoi_dung["admin"], "ghi_chu_chung", "Ghi chú chung",
               [col("Ngày", "ngay", FieldType.DATE, Meaning.DATE)])
    add_row(mkt, nguoi_dung["staff_mkt"], date(2026, 9, 10),
            {"marketer": "A", "so_mess": 10, "cpqc": "100", "so_don": 1, "doanh_so": "1000", "loai_tien": "VND"},
            revenue=1000, seller="A")
    add_row(sale, nguoi_dung["staff_sale_1"], date(2026, 9, 10),
            {"sale": "Lan", "so_mess": 5, "so_don": 2, "doanh_so": "200", "loai_tien": "USD"},
            revenue=200, seller="Lan")
    return {**nguoi_dung, "leader_mkt": make_user("leader_mkt", Rank.LEADER, departments["mkt"])}


def _nut(html, nhan):
    """href của mọi nút mang nhãn `nhan` trong trang, đã bỏ mã `&amp;`."""
    mau = r'<a\b[^>]*\bhref="([^"]*)"[^>]*>\s*' + re.escape(nhan) + r"\s*</a>"
    return [html_lib.unescape(h) for h in re.findall(mau, html)]


def _luoi_crm(html):
    """Mọi liên kết tới lưới KN CRM trong trang."""
    return [html_lib.unescape(h) for h in re.findall(r'href="(/bang-tinh/[^"]*)"', html)]


def _bao_cao_erp(href, ma, goc="http://localhost:8020"):
    """`href` là Báo cáo tổng hợp KN ERP của đúng nguồn `ma`, đúng kỳ đang xem."""
    phan = urlsplit(href)
    return (f"{phan.scheme}://{phan.netloc}" == goc and phan.path == "/bao-cao/tong-hop/"
            and parse_qs(phan.query) == {"nguon": [ma], "tu": [TU], "den": [DEN]})


def _mo_o_erp(client, settings, href):
    """Mở liên kết bằng URLconf KN ERP (cổng 8020), rồi trả lại URLconf KN CRM cho phần còn lại của bài."""
    phan = urlsplit(href)
    settings.ROOT_URLCONF = "knjsc.urls"
    try:
        return client.get(f"{phan.path}?{phan.query}")
    finally:
        settings.ROOT_URLCONF = "knjsc.urls_bangtinh"


def _nguon_bao_cao_thay_duoc(user):
    return sorted(t.code for t in statistics_service.source_tables(user) if t.code in BAO_CAO)


@pytest.mark.parametrize("ai", ["staff_sale_1", "leader_sale_1", "manager_sale",
                                "staff_mkt", "leader_mkt", "manager_mkt", "admin"])
def test_nguon_sale_mkt_mo_bao_cao_tong_hop_erp_cung_ky(client, settings, he_thong, ai):
    """AC-40.9 — Thống kê KN CRM của nguồn Sale/MKT: nút "Mở dữ liệu" mở Báo cáo tổng hợp KN ERP của đúng nguồn đó, cùng khoảng ngày, và vai nào thấy nguồn trong Thống kê thì mở được (200, đúng nguồn, đúng kỳ); trang không còn liên kết nào tới lưới `/bang-tinh/` của bảng báo cáo (404 từ ADR-040)"""
    client.force_login(he_thong[ai])
    nguon = _nguon_bao_cao_thay_duoc(he_thong[ai])
    assert nguon, f"{ai} không thấy nguồn Sale/MKT nào — bài kiểm rỗng"
    for ma in nguon:
        trang = client.get("/thong-ke/", {"nguon": ma, **KY})
        assert trang.status_code == 200
        html = trang.content.decode()
        assert not _luoi_crm(html), f"{ai} {ma}: còn liên kết lưới {_luoi_crm(html)}"
        nut = _nut(html, "Mở dữ liệu")
        assert nut and all(_bao_cao_erp(h, ma) for h in nut), (ai, ma, nut)
        erp = _mo_o_erp(client, settings, nut[0])
        assert erp.status_code == 200, (ai, ma, erp.status_code)
        assert erp.context["source"].table.code == ma
        assert (erp.context["params"]["start"], erp.context["params"]["end"]) == (date(2026, 9, 1), date(2026, 9, 30))


@pytest.mark.parametrize("ai", ["staff_vd", "manager_sale", "manager_mkt", "admin"])
def test_tong_quan_moi_nut_mo_duoc(client, settings, he_thong, ai):
    """AC-40.9 — Trang tổng quan Thống kê (không chọn nguồn): mọi nút "Mở dữ liệu" mở được — nguồn Sale/MKT sang Báo cáo tổng hợp KN ERP đúng nguồn, đúng kỳ; Vận đơn mở lưới KN CRM; không nút nào 403/404"""
    client.force_login(he_thong[ai])
    html = client.get("/thong-ke/", KY).content.decode()
    nut = _nut(html, "Mở dữ liệu")
    assert nut, f"{ai}: tổng quan không có nhận định nào"
    for href in nut:
        if href.startswith("/bang-tinh/"):
            assert href.startswith(f"/bang-tinh/{ACTIVE_WAYBILL_TABLE_CODE}/"), (ai, href)
            assert client.get(href).status_code == 200, (ai, href)
        else:
            assert any(_bao_cao_erp(href, ma) for ma in BAO_CAO), (ai, href)
            assert _mo_o_erp(client, settings, href).status_code == 200, (ai, href)


def test_van_don_giu_luoi_crm(client, he_thong):
    """AC-40.9 — Thống kê nguồn Vận đơn giữ nút "Mở dữ liệu" sang lưới KN CRM (lọc đúng kỳ) như trước, mở được"""
    client.force_login(he_thong["admin"])
    html = client.get("/thong-ke/", {"nguon": ACTIVE_WAYBILL_TABLE_CODE, **KY}).content.decode()
    nut = _nut(html, "Mở dữ liệu")
    assert nut and all(h.startswith(f"/bang-tinh/{ACTIVE_WAYBILL_TABLE_CODE}/?") and TU in h and DEN in h for h in nut)
    assert client.get(nut[0]).status_code == 200


def test_bang_khac_khong_co_nut(client, he_thong):
    """AC-40.9 — Bảng không phải Vận đơn, Sale, MKT: nhận định vẫn hiện nhưng không có nút "Mở dữ liệu", không có liên kết tới lưới KN CRM (bảng đó 404 ở KN CRM, không có Báo cáo tổng hợp riêng)"""
    client.force_login(he_thong["admin"])
    trang = client.get("/thong-ke/", {"nguon": "ghi_chu_chung", **KY})
    html = trang.content.decode()
    assert trang.status_code == 200 and trang.context["dashboard"]["insights"]
    assert "Bảng chưa có dữ liệu" in html
    assert not _nut(html, "Mở dữ liệu") and not _luoi_crm(html)


def test_so_lieu_loi_nut_mo_bang_nguon_cung_luat(client, he_thong, monkeypatch):
    """AC-40.9 — Phần số liệu tạm lỗi: nút "Mở bảng nguồn" theo cùng luật — nguồn MKT sang Báo cáo tổng hợp KN ERP đúng kỳ (ở trang riêng và ở ô Marketing của tổng quan), Vận đơn sang lưới KN CRM, bảng khác không có nút"""
    def hong(*args, **kwargs):
        raise RuntimeError("lỗi thử")
    for profile in ("marketing", "waybill", "generic"):
        monkeypatch.setitem(statistics_profiles.BUILDERS, profile, hong)
    client.force_login(he_thong["admin"])

    trang = client.get("/thong-ke/", {"nguon": "bao_cao_mkt", **KY})
    assert trang.context["dashboard"]["ok"] is False
    nut = _nut(trang.content.decode(), "Mở bảng nguồn")
    assert len(nut) == 1 and _bao_cao_erp(nut[0], "bao_cao_mkt"), nut

    tong_quan = client.get("/thong-ke/", KY).content.decode()
    nut = _nut(tong_quan, "Mở bảng nguồn")
    assert any(_bao_cao_erp(h, "bao_cao_mkt") for h in nut), nut
    assert all(_bao_cao_erp(h, "bao_cao_mkt") or h.startswith(f"/bang-tinh/{ACTIVE_WAYBILL_TABLE_CODE}/")
               for h in nut), nut

    van_don = client.get("/thong-ke/", {"nguon": ACTIVE_WAYBILL_TABLE_CODE, **KY}).content.decode()
    assert [h.split("?")[0] for h in _nut(van_don, "Mở bảng nguồn")] == [f"/bang-tinh/{ACTIVE_WAYBILL_TABLE_CODE}/"]

    chung = client.get("/thong-ke/", {"nguon": "ghi_chu_chung", **KY}).content.decode()
    assert "Phần số liệu tạm chưa khả dụng" in chung
    assert not _nut(chung, "Mở bảng nguồn") and not _luoi_crm(chung)


def test_lien_ket_erp_giu_host_dang_mo_ke_ca_so_lieu_tu_bo_nho_dem(client, he_thong, settings):
    """AC-40.9 — Liên kết sang Báo cáo tổng hợp KN ERP giữ đúng host đang mở (AC-1.10): mở KN CRM bằng 127.0.0.1 thì trỏ 127.0.0.1:8020, bằng localhost thì localhost:8020 — kể cả khi số liệu lấy lại từ bộ nhớ đệm Thống kê (khoá đệm không theo host)"""
    from django.core.cache import caches
    settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
                       "crm": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                               "LOCATION": "thong-ke-lien-ket-nguon"}}
    caches["crm"].clear()
    settings.CRM_OPT_STATS = True
    client.force_login(he_thong["admin"])
    dau = client.get("/thong-ke/", {"nguon": "bao_cao_mkt", **KY}, HTTP_HOST="localhost:8021")
    sau = client.get("/thong-ke/", {"nguon": "bao_cao_mkt", **KY}, HTTP_HOST="127.0.0.1:8021")
    assert sau.context["updated"] == dau.context["updated"]          # lần sau lấy từ bộ nhớ đệm
    nut = _nut(dau.content.decode(), "Mở dữ liệu")
    assert nut and all(_bao_cao_erp(h, "bao_cao_mkt", "http://localhost:8020") for h in nut), nut
    nut = _nut(sau.content.decode(), "Mở dữ liệu")
    assert nut and all(_bao_cao_erp(h, "bao_cao_mkt", "http://127.0.0.1:8020") for h in nut), nut
    assert "localhost:8020" not in sau.content.decode()


def test_ten_mien_that_giu_dung_cau_hinh(client, he_thong, settings):
    """AC-40.9 — Trên VPS (tên miền thật) liên kết sang Báo cáo tổng hợp đúng địa chỉ KN ERP đã cấu hình, không đổi theo host"""
    settings.MAIN_APP_URL = "https://erp.vi-du.vn/"
    settings.ALLOWED_HOSTS = ["crm.vi-du.vn"]
    client.force_login(he_thong["admin"])
    html = client.get("/thong-ke/", {"nguon": "bao_cao_sale", **KY}, HTTP_HOST="crm.vi-du.vn").content.decode()
    nut = _nut(html, "Mở dữ liệu")
    assert nut and all(_bao_cao_erp(h, "bao_cao_sale", "https://erp.vi-du.vn") for h in nut), nut
