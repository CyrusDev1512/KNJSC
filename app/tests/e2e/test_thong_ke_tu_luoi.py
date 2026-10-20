"""Đi từ lưới Vận đơn sang Thống kê mà không rơi bộ lọc — TL-109, TL-110 (rà sau khi gộp đợt P0, 14.10.2026).

TL-109: `navigate()` của lưới thay trọn phần truy vấn của mọi link `[data-query-link]`, nên sau Tôi/Tìm nút Thống kê
mất `nguon=van_don` và mở Bàn điều hành tổng hợp. TL-110: Áp dụng ở Thống kê chỉ gửi nguồn, kỳ, cách nhóm nên bộ lọc
lưới rơi mất. Phải kiểm bằng trình duyệt thật: link do JS dựng lại, ô ngày do JS đổi định dạng.
"""
from datetime import date, timedelta
from urllib.parse import parse_qs, urlsplit

import pytest

from crm.tests.test_waybill_feedback import assign_rows, delivery_leader, feedback  # noqa: F401  (fixture dùng lại)

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]


@pytest.fixture
def kn_crm(settings):
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.BANGTINH_URL = ""
    return settings


def _tham_so(trang, chon):
    return parse_qs(urlsplit(trang.locator(chon).get_attribute("href")).query)


def test_link_thong_ke_giu_nguon_sau_toi_va_tim(live_server, trang, dang_nhap, kn_crm, feedback, nguoi_dung,
                                                delivery_leader):  # noqa: F811
    """AC-33.4 — Trên lưới Vận đơn, sau khi bấm Tôi, sau khi Tìm, và khi mở lại lưới với lựa chọn Tôi đã nhớ, nút
    Thống kê vẫn trỏ `nguon=van_don` kèm bộ lọc đang áp; bấm vào thì mở thống kê Vận đơn, không phải Bàn điều hành
    tổng hợp (TL-109)"""
    bang, _, rows = feedback
    nhan_vien = nguoi_dung["staff_vd"]
    assign_rows(delivery_leader, [rows[0]], delivery=nhan_vien.pk)
    loi_js = []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(trang, nhan_vien)
    trang.goto(f"{live_server.url}/bang-tinh/{bang.code}/")
    trang.wait_for_selector(".mg-cell[data-code='ma_don']")
    link = ".mg-toolbar a[href*='/thong-ke/']"
    assert _tham_so(trang, link)["nguon"] == ["van_don"]

    trang.click("[data-pham-vi='toi']")
    trang.wait_for_url(lambda u: "cua_toi=1" in u)
    q = _tham_so(trang, link)
    assert q.get("nguon") == ["van_don"], f"Tôi xoá mất nguon của link Thống kê: {q}"
    assert q.get("cua_toi") == ["1"]

    trang.fill("#mg-search input[name=tim]", "Khách 0")
    trang.press("#mg-search input[name=tim]", "Enter")
    trang.wait_for_url(lambda u: "tim=" in u)
    q = _tham_so(trang, link)
    assert q.get("nguon") == ["van_don"] and q.get("tim") == ["Khách 0"], q

    # Mở lại lưới không tham số: lưới tự bật Tôi theo lựa chọn đã nhớ (navigate lúc mở trang)
    trang.goto(f"{live_server.url}/bang-tinh/{bang.code}/")
    trang.wait_for_url(lambda u: "cua_toi=1" in u)
    trang.wait_for_selector(".mg-cell[data-code='ma_don']")
    q = _tham_so(trang, link)
    assert q.get("nguon") == ["van_don"] and q.get("cua_toi") == ["1"], f"mở lại với Tôi đã nhớ: {q}"

    trang.click(link)
    trang.wait_for_url(lambda u: "/thong-ke/" in u)
    q = parse_qs(urlsplit(trang.url).query)
    assert q.get("nguon") == ["van_don"] and q.get("cua_toi") == ["1"], trang.url
    assert trang.locator("#exec-nguon").input_value() == "van_don"
    assert not loi_js, loi_js


def test_ap_dung_o_thong_ke_giu_bo_loc_va_doi_nguon_thi_bo(live_server, trang, dang_nhap, kn_crm, feedback,
                                                           nguoi_dung, delivery_leader):  # noqa: F811
    """AC-22.8 — Thống kê mở từ lưới với Tôi: đổi Từ ngày rồi Áp dụng vẫn lọc Tôi (địa chỉ giữ cua_toi=1, không lộ
    loc_nguon), trang ghi "Đang lọc theo lưới: Của tôi"; chọn nguồn Tổng hợp rồi Áp dụng thì bỏ bộ lọc lưới (TL-110)"""
    _, _, rows = feedback
    nhan_vien = nguoi_dung["staff_vd"]
    assign_rows(delivery_leader, [rows[0]], delivery=nhan_vien.pk)
    loi_js = []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(trang, nhan_vien)
    trang.goto(f"{live_server.url}/thong-ke/?nguon=van_don&cua_toi=1")
    dau_thang_truoc = (date.today().replace(day=1) - timedelta(days=1)).replace(day=1)
    tu_iso = dau_thang_truoc.isoformat()
    # Ô ngày là ô chữ DD/MM/YYYY (date-inputs.js, ADR-032); giá trị gửi đi vẫn là ISO
    trang.fill("#exec-tu", dau_thang_truoc.strftime("%d/%m/%Y"))
    trang.get_by_role("button", name="Áp dụng", exact=True).click()
    trang.wait_for_url(lambda u: f"tu={tu_iso}" in u)
    q = parse_qs(urlsplit(trang.url).query)
    assert q.get("cua_toi") == ["1"], f"Áp dụng bỏ rơi Tôi: {trang.url}"
    assert "loc_nguon" not in q and q.get("nguon") == ["van_don"], trang.url
    bao = trang.locator("#exec-loc-luoi")
    assert bao.count() == 1 and "Của tôi" in bao.inner_text()

    trang.select_option("#exec-nguon", value="")
    trang.get_by_role("button", name="Áp dụng", exact=True).click()
    trang.wait_for_url(lambda u: "nguon=van_don" not in u)
    q = parse_qs(urlsplit(trang.url).query)
    assert "cua_toi" not in q and "loc_nguon" not in q, trang.url
    assert trang.locator("#exec-loc-luoi").count() == 0
    assert not loi_js, loi_js
