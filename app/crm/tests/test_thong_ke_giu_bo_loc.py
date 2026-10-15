"""Áp dụng ở Thống kê giữ bộ lọc lưới; đổi nguồn thì bỏ — TL-110 (rà sau khi gộp đợt P0, 14.10.2026).

Từ lưới sang Thống kê (Tôi, Tìm, lọc cột) rồi đổi kỳ, bấm Áp dụng: form `exec-controls` chỉ có nguồn, kỳ, cách nhóm nên
bộ lọc lưới rơi mất, số nhảy sang toàn bảng mà trang không báo.
"""
from datetime import timedelta
from html.parser import HTMLParser

import pytest
from django.http import QueryDict
from django.utils import timezone

from forms_builder.meaning import FieldType
from crm.services import grid_service

from .test_executive_statistics import col, make_table
from .test_waybill_feedback import assign_rows, delivery_leader, feedback  # noqa: F401

pytestmark = pytest.mark.django_db


class _FormApDung(HTMLParser):
    """Các cặp tên–giá trị mà trình duyệt gửi khi bấm Áp dụng ở form `exec-controls`."""

    def __init__(self, chi_o_an=False):
        super().__init__()
        self.chi_o_an, self.trong_form, self.select, self.chon, self.cap = chi_o_an, False, None, None, []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "form":
            self.trong_form = "exec-controls" in (a.get("class") or "").split()
        elif not self.trong_form:
            return
        elif tag == "input" and a.get("name"):
            if not self.chi_o_an or a.get("type") == "hidden":
                self.cap.append((a["name"], a.get("value") or ""))
        elif tag == "select" and not self.chi_o_an:
            self.select, self.chon = a.get("name"), None
        elif tag == "option" and self.select:
            if self.chon is None or "selected" in a:
                self.chon = (a.get("value") or "", "selected" in a)

    def handle_endtag(self, tag):
        if tag == "form":
            self.trong_form = False
        elif tag == "select" and self.select:
            if self.chon is not None:
                self.cap.append((self.select, self.chon[0]))
            self.select = None

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)


def _cap_form(trang, chi_o_an=False):
    p = _FormApDung(chi_o_an)
    p.feed(trang.content.decode())
    return p.cap


def _ap_dung(client, trang, **doi):
    """Bấm Áp dụng: gửi đúng các ô của form, thay ô nào có trong `doi`; theo chuyển hướng."""
    q = QueryDict("", mutable=True)
    for ten, gia_tri in _cap_form(trang):
        if ten not in doi:
            q.appendlist(ten, gia_tri)
    for ten, gia_tri in doi.items():
        q[ten] = gia_tri
    return client.get("/thong-ke/?" + q.urlencode(), follow=True)


def _dau_thang_truoc():
    return (timezone.localdate().replace(day=1) - timedelta(days=1)).replace(day=1).isoformat()


@pytest.mark.parametrize("khoa", ["cua_toi", "tim", "f_ma_don__trong"])
def test_ap_dung_giu_bo_loc_luoi(client, feedback, nguoi_dung, delivery_leader, khoa):  # noqa: F811
    """AC-22.8 — Từ lưới sang Thống kê rồi đổi kỳ, bấm Áp dụng: số liệu vẫn theo bộ lọc lưới (Tôi, Tìm, lọc cột); form
    mang bộ lọc bằng ô ẩn; địa chỉ cuối giữ bộ lọc và không còn `loc_nguon` (TL-110)"""
    _, _, rows = feedback
    nhan_vien = nguoi_dung["staff_vd"]
    assign_rows(delivery_leader, [rows[0]], delivery=nhan_vien.pk)
    gia_tri = {"cua_toi": "1", "tim": "Khách 0", "f_ma_don__trong": rows[0].data["ma_don"]}[khoa]
    client.force_login(nhan_vien)
    dau = client.get("/thong-ke/", {"nguon": "van_don", khoa: gia_tri})
    assert dau.context["summary"]["orders"] == 1
    tu = _dau_thang_truoc()
    sau = _ap_dung(client, dau, tu=tu)
    assert sau.status_code == 200
    assert sau.context["summary"]["orders"] == 1, "Áp dụng bỏ rơi bộ lọc lưới — số nhảy sang toàn bảng"
    g = sau.wsgi_request.GET
    assert g["tu"] == tu and g["nguon"] == "van_don" and "loc_nguon" not in g
    assert g.getlist(khoa) == [gia_tri]


def test_o_an_chi_mang_trang_thai_luoi(client, feedback, nguoi_dung):  # noqa: F811
    """AC-22.8 — Form Áp dụng của Thống kê mang đúng trạng thái lưới bằng ô ẩn trong `.exec-controls` (bộ lọc cột, Tìm,
    Tôi, sắp xếp) cùng `loc_nguon`; không mang số trang, trang biểu đồ, Làm mới; Bàn điều hành tổng hợp không có ô
    ẩn nào (TL-110)"""
    client.force_login(nguoi_dung["staff_vd"])
    trang = client.get("/thong-ke/", {"nguon": "van_don", "cua_toi": "1", "sap": "ma_don", "chieu": "giam",
                                      "f_ma_don__co": "1", "chart_1": "1", "trang": "2", "moi_trang": "25",
                                      "lam_moi": "1"})
    o_an = _cap_form(trang, chi_o_an=True)
    assert {k for k, _ in o_an} == {"loc_nguon", "cua_toi", "sap", "chieu", "f_ma_don__co"}, o_an
    assert ("loc_nguon", "van_don") in o_an
    assert _cap_form(client.get("/thong-ke/?cua_toi=1"), chi_o_an=True) == []


def test_thong_ke_bao_dang_loc_theo_luoi_va_bo_duoc(client, feedback, nguoi_dung, delivery_leader):  # noqa: F811
    """AC-22.8 — Thống kê mở với bộ lọc lưới ghi rõ "Đang lọc theo lưới" và từng bộ lọc (Của tôi, Tìm, cột), mỗi nhãn
    bỏ riêng được; "Bỏ lọc lưới" về số toàn phạm vi, giữ nguồn và kỳ (TL-110)"""
    _, _, rows = feedback
    nhan_vien = nguoi_dung["staff_vd"]
    assign_rows(delivery_leader, [rows[0]], delivery=nhan_vien.pk)
    client.force_login(nhan_vien)
    tu, den = _dau_thang_truoc(), timezone.localdate().isoformat()
    trang = client.get("/thong-ke/", {"nguon": "van_don", "cua_toi": "1", "tim": "Khách", "tu": tu, "den": den})
    html = trang.content.decode()
    assert 'id="exec-loc-luoi"' in html, "Trang không báo đang lọc theo lưới"
    nhan = {label: url for label, url, _ in trang.context["chips"]}
    assert "Của tôi" in nhan and "Tìm “Khách”" in nhan, nhan
    bo_toi = QueryDict(nhan["Của tôi"].lstrip("?"))
    assert "cua_toi" not in bo_toi and bo_toi.get("tim") == "Khách"
    assert QueryDict(trang.context["bo_loc_luoi"]).dict() == {"nguon": "van_don", "tu": tu, "den": den}
    het = client.get("/thong-ke/?" + trang.context["bo_loc_luoi"])
    assert het.context["summary"]["orders"] == 2
    assert 'id="exec-loc-luoi"' not in het.content.decode()


def test_doi_nguon_bo_bo_loc_luoi_cua_nguon_cu(client, feedback, nguoi_dung, departments):  # noqa: F811
    """AC-22.1 — `nguon` phân tích đúng một bảng: Thống kê Vận đơn đang mang bộ lọc lưới, giữ nguồn rồi Áp dụng thì giữ
    bộ lọc; chọn nguồn khác hay Tổng hợp rồi Áp dụng thì bộ lọc của bảng cũ bị bỏ, bảng mới không bị lọc mà không ai
    biết (TL-110)"""
    admin = nguoi_dung["admin"]
    make_table(departments["sale"], admin, "sale_tl110", "Sale TL-110", [col("Nội dung", "noi_dung", FieldType.TEXT)])
    client.force_login(admin)
    dau = client.get("/thong-ke/", {"nguon": "van_don", "tim": "Khách 0", "cua_toi": "1", "f_ma_don__co": "1"})
    giu = _ap_dung(client, dau)
    assert giu.wsgi_request.GET.get("tim") == "Khách 0"

    sang = _ap_dung(client, dau, nguon="sale_tl110")
    assert sang.status_code == 200 and sang.context["source_table"].code == "sale_tl110"
    assert sang.context["luoi"].search == "" and not sang.context["luoi"].my_scope
    g = sang.wsgi_request.GET
    assert not [k for k in g if k.startswith("f_") or k in {"tim", "cua_toi", "loc_nguon"}], g
    assert [ma for _, ma in sang.redirect_chain] == [302]

    tong = _ap_dung(client, dau, nguon="")
    assert tong.context["dashboard"]["profile"] == "overview"
    assert "tim" not in tong.wsgi_request.GET


def test_moi_khoa_trang_thai_luoi_doi_duoc_ket_qua_build_grid(feedback, nguoi_dung):  # noqa: F811
    """TL-110 · `GRID_STATE_PARAMS` khai một chỗ những khoá lưới mà Thống kê mang qua Áp dụng; mỗi khoá trong đó phải
    thật sự đổi được truy vấn của `build_grid` (Tìm, Tôi, sản phẩm, trùng, sắp xếp, chiều), để hằng không lệch khỏi bộ
    đọc của lưới"""
    bang, products, _ = feedback
    nguoi = nguoi_dung["staff_vd"]
    goc = str(grid_service.build_grid(nguoi, QueryDict(""), table=bang).queryset.query)
    mau = {"tim": "Khách 0", grid_service.MY_SCOPE_PARAM: "1", grid_service.PRODUCT_PARAM: products[0].code,
           "trung": "1", "sap": "ma_don", "chieu": "giam"}
    assert set(mau) == set(grid_service.GRID_STATE_PARAMS)
    for khoa, gia_tri in mau.items():
        q = QueryDict(f"{khoa}={gia_tri}" + ("&sap=ma_don" if khoa == "chieu" else ""), mutable=True)
        so_voi = goc if khoa != "chieu" else str(grid_service.build_grid(
            nguoi, QueryDict("sap=ma_don"), table=bang).queryset.query)
        assert str(grid_service.build_grid(nguoi, q, table=bang).queryset.query) != so_voi, khoa
    assert grid_service.is_grid_param("f_ma_don__co") and not grid_service.is_grid_param("nguon")
