"""Lịch sử từng ô ngay trên lưới Vận đơn — AC-21.13 (chủ dự án 28.09.2026).

Ô bị người khác sửa trong 24 giờ có dấu góc; chuột phải vào ô thì khung lịch sử hiện ngay cạnh ô
(ai sửa, lúc nào, từ gì thành gì), Esc hay bấm ra ngoài thì đóng. Phải kiểm bằng trình duyệt thật:
dấu góc và vị trí khung là chuyện hiển thị.
"""
import pytest
from django.test import Client

from core.constants import Rank
from crm.tests.test_master_grid import write
from crm.tests.test_waybill_feedback import feedback  # noqa: F401  (fixture dùng lại)

from .conftest import chup

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]


@pytest.fixture
def kn_crm(settings):
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.BANGTINH_URL = ""
    return settings


def test_chuot_phai_o_xem_lich_su_va_dau_o_vua_sua(live_server, trang, dang_nhap, kn_crm, feedback,
                                                   nguoi_dung, make_user, departments):  # noqa: F811
    """AC-21.13 — Ô Tên khách vừa bị người khác sửa mang dấu góc; ô chưa ai sửa thì không; chuột phải
    ô đó mở khung lịch sử cạnh ô, có mã người sửa và giá trị trước → sau; Esc đóng"""
    bang, _, dong = feedback
    khac = make_user("vd_khac", Rank.STAFF, departments["vd"])
    c = Client()
    c.force_login(khac)
    assert write(c, dong[0], column="ten_khach", old=dong[0].data["ten_khach"], value="Khách Đã Sửa").status_code == 200

    loi_js = []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(trang, nguoi_dung["staff_vd"])
    trang.goto(f"{live_server.url}/bang-tinh/{bang.code}/")
    o = f".mg-cell[data-code='ten_khach'][data-id='{dong[0].pk}']"
    trang.wait_for_selector(o)
    trang.wait_for_function(f"() => document.querySelector(\"{o}\").textContent.includes('Khách Đã Sửa')")

    assert trang.evaluate(f"() => document.querySelector(\"{o}\").classList.contains('mg-moi-sua')"), \
        "ô vừa bị người khác sửa phải có dấu góc"
    assert not trang.evaluate(
        f"() => document.querySelector(\".mg-cell[data-code='ten_khach'][data-id='{dong[1].pk}']\").classList.contains('mg-moi-sua')")

    trang.click(o, button="right")
    trang.wait_for_selector("#mg-cell-history:not([hidden])", timeout=5_000)
    trang.wait_for_function("() => document.querySelector('#mg-cell-history .mg-history-item')", timeout=5_000)
    khung = trang.text_content("#mg-cell-history")
    assert "Khách Đã Sửa" in khung and dong[0].data["ten_khach"] in khung, khung
    assert "Tên khách" in khung
    vi_tri = trang.evaluate(f"""() => {{ const o = document.querySelector("{o}").getBoundingClientRect();
        const k = document.getElementById('mg-cell-history').getBoundingClientRect();
        return {{gan: Math.abs(k.top - o.bottom) < 40 || Math.abs(k.bottom - o.top) < 40}}; }}""")
    assert vi_tri["gan"], "khung lịch sử phải nằm ngay cạnh ô"
    chup(trang, "lich-su-o-tren-luoi")
    trang.keyboard.press("Escape")
    trang.wait_for_function("() => document.getElementById('mg-cell-history').hidden", timeout=3_000)
    assert not loi_js, loi_js


def test_chuot_phai_len_hop_doc_van_mo_lich_su_o(live_server, trang, dang_nhap, kn_crm, feedback,
                                                 nguoi_dung, make_user, departments):  # noqa: F811
    """AC-21.13 — Bấm ô Ghi chú dài thì hộp đọc hiện đè gần ô; chuột phải lên chính hộp đó (hay lên ô
    khi hộp đang mở) vẫn mở lịch sử của ô Ghi chú, không ra menu của trình duyệt (chủ dự án 28.09)"""
    bang, _, dong = feedback
    khac = make_user("vd_khac", Rank.STAFF, departments["vd"])
    c = Client()
    c.force_login(khac)
    dai = "Ghi chú rất dài " * 30
    assert write(c, dong[0], column="ghi_chu", old=dong[0].data.get("ghi_chu"), value=dai).status_code == 200

    dang_nhap(trang, nguoi_dung["staff_vd"])
    trang.goto(f"{live_server.url}/bang-tinh/{bang.code}/")
    o = f".mg-cell[data-code='ghi_chu'][data-id='{dong[0].pk}']"
    trang.wait_for_selector(".mg-cell[data-code='ten_khach']")
    trang.wait_for_function(f"""() => {{ const v = document.getElementById('mg-viewport');
        if (document.querySelector("{o}")) return true; v.scrollLeft += 300; return false; }}""", timeout=10_000)
    trang.locator(o).scroll_into_view_if_needed()
    trang.click(o)
    trang.wait_for_selector("#mg-reader:not([hidden])", timeout=5_000)

    chan = trang.evaluate("""() => { const e = new MouseEvent('contextmenu', {bubbles: true, cancelable: true,
        clientX: 1, clientY: 1}); return !document.querySelector('#mg-reader div').dispatchEvent(e); }""")
    assert chan, "chuột phải lên hộp đọc phải chặn menu trình duyệt"
    trang.wait_for_selector("#mg-cell-history:not([hidden])", timeout=5_000)
    trang.wait_for_function("() => document.querySelector('#mg-cell-history .mg-history-item')", timeout=5_000)
    assert "Ghi chú" in trang.text_content("#mg-cell-history strong")
    assert trang.evaluate("() => document.getElementById('mg-reader').hidden"), "hộp đọc phải nhường chỗ cho lịch sử"
