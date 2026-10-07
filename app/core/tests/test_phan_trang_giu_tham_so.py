"""Thanh phân trang dùng chung giữ mọi tham số đang có trên URL — AC-10.18 (07.10.2026).

Trước đây liên kết trang chỉ gồm `?trang=…&moi_trang=…` cộng chuỗi lọc màn hình tự truyền (`qs_loc`). Màn hình quên
truyền thì chuyển trang là mất bộ lọc: Nhân sự lọc "Trưởng nhóm" rồi bấm trang 2 ra trang 2 của toàn bộ nhân sự (Nhân sự
và Nhật ký đều quên). Trang có hai bảng phân trang (Bộ phận và team) thì chuyển trang bảng này làm bảng kia về trang 1.
Nay liên kết lấy đúng URL đang mở, chỉ thay số trang (đổi cỡ trang thì về trang 1).
"""
import re
from html import unescape
from urllib.parse import parse_qs, urlsplit

import pytest
from django.template import Context, Template
from django.test import RequestFactory

from core.constants import Rank
from org.models import Department, Team

pytestmark = pytest.mark.django_db


def _lien_ket(html):
    """Các liên kết và lựa chọn cỡ trang trong thanh phân trang, đã đọc thành dict tham số."""
    khoi = re.search(r'<div class="phan-trang".*?</div>\s*</div>', html, re.S).group(0)
    hrefs = [unescape(h) for h in re.findall(r'(?<!data-)href="([^"]+)"', khoi)]
    co = [unescape(h) for h in re.findall(r'data-href="([^"]+)"', khoi)]
    doc = lambda u: {k: v[0] for k, v in parse_qs(urlsplit(u).query).items()}
    return [doc(h) for h in hrefs], [doc(h) for h in co]


def _ve(duong, **ngu_canh):
    tpl = Template('{% include "components/phan_trang.html" %}')
    request = RequestFactory().get(duong)
    return tpl.render(Context({"request": request, **ngu_canh}))


def test_lien_ket_giu_tham_so_chi_doi_so_trang():
    """AC-10.18 — Liên kết trang giữ mọi tham số của URL (kể cả chữ có "&", "#"), chỉ thay số trang; đổi cỡ trang thì
    về trang 1; chuỗi lọc `qs_loc` màn hình truyền vẫn được tôn trọng"""
    from django.core.paginator import Paginator
    trang = Paginator(list(range(100)), 25).page(2)
    html = _ve("/x/?tim=Sale+%26+MKT+%231&cap_bac=leader&trang=2&moi_trang=25",
               page_obj=trang, moi_trang=25, cac_co_trang=[25, 50, 100], qs_loc="&nhom=ngay")
    trang_lk, co_lk = _lien_ket(html)
    assert {d["trang"] for d in trang_lk} >= {"1", "3", "4"}
    for d in trang_lk:
        assert d["tim"] == "Sale & MKT #1" and d["cap_bac"] == "leader" and d["moi_trang"] == "25"
        assert d["nhom"] == "ngay"
    assert {d["moi_trang"] for d in co_lk} == {"25", "50", "100"}
    assert all("trang" not in d and d["cap_bac"] == "leader" for d in co_lk)


def test_nhan_su_sang_trang_2_giu_bo_loc(client, nguoi_dung, departments, make_user):
    """AC-10.18 — Nhân sự lọc theo cấp bậc: liên kết sang trang 2 vẫn mang bộ lọc đó, trang 2 chỉ có người đúng cấp bậc"""
    for i in range(30):
        make_user(f"nv_loc_{i:02d}", Rank.STAFF, departments["sale"])
    client.force_login(nguoi_dung["admin"])
    html = client.get("/nhan-su/?cap_bac=staff").content.decode()
    trang_lk, _ = _lien_ket(html)
    sang_2 = next(d for d in trang_lk if d.get("trang") == "2")
    assert sang_2["cap_bac"] == "staff"
    html2 = client.get("/nhan-su/?" + "&".join(f"{k}={v}" for k, v in sang_2.items())).content.decode()
    assert "quan_tri" not in html2 and "manager_sale" not in html2


def test_hai_bang_phan_trang_khong_giam_nhau(client, nguoi_dung, departments):
    """AC-10.18 — Trang Bộ phận và team: đang ở trang 2 của bảng Bộ phận thì liên kết trang của bảng Team vẫn giữ
    `trang_bp=2`"""
    for i in range(30):
        Department.objects.create(name=f"Bộ phận thử {i:02d}", code=f"bp-thu-{i:02d}")
    Team.objects.create(name="Team thử", department=departments["sale"])
    client.force_login(nguoi_dung["admin"])
    html = client.get("/bo-phan/?trang_bp=2").content.decode()
    khoi = re.findall(r'<div class="phan-trang".*?</div>\s*</div>', html, re.S)
    assert len(khoi) == 2
    team_hrefs = [unescape(h) for h in re.findall(r'(?:data-)?href="([^"]+)"', khoi[1])]
    assert team_hrefs and all("trang_bp=2" in h for h in team_hrefs)
