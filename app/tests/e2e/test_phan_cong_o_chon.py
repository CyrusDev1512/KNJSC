"""Phân công ngay trong ô bằng ô chọn, như "Trạng thái vận chuyển" — AC-21.15 (chủ dự án 28.09.2026).

Trước: bấm đúp ô "Phụ trách …" mở hộp Phân công riêng giữa màn hình. Nay Leader/Manager Vận đơn và
Admin chọn người ngay trong ô; quyền và CAS vẫn qua endpoint phân công cũ.
"""
import pytest

from core.constants import Rank
from core.identity import employee_code
from crm.tests.test_waybill_feedback import feedback  # noqa: F401  (fixture dùng lại)
from orders.models import WaybillAssignment

from .conftest import chup

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]


@pytest.fixture
def kn_crm(settings):
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.BANGTINH_URL = ""
    return settings


def mo_luoi_toi_o(trang, live_server, bang, o):
    trang.goto(f"{live_server.url}/bang-tinh/{bang.code}/")
    trang.wait_for_selector(".mg-cell[data-code='ten_khach']")
    trang.wait_for_function(f"""() => {{ const v = document.getElementById('mg-viewport');
        if (document.querySelector("{o}")) return true; v.scrollLeft += 300; return false; }}""", timeout=10_000)
    trang.locator(o).scroll_into_view_if_needed()


def test_leader_chon_nguoi_ngay_trong_o_phu_trach(live_server, trang, dang_nhap, kn_crm, feedback,
                                                  nguoi_dung, make_user, departments):  # noqa: F811
    """AC-21.15 — Leader Vận đơn bấm đúp ô Phụ trách Vận đơn: ô chọn hiện ngay trong ô, có mã nhân viên
    Vận đơn; chọn là lưu (qua endpoint phân công, có CAS), ô hiện mã người vừa giao; Esc đóng không đổi"""
    bang, _, dong = feedback
    leader = make_user("vd_leader", Rank.LEADER, departments["vd"])
    nv = nguoi_dung["staff_vd"]
    loi_js = []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(trang, leader)
    o = f".mg-cell[data-code='phu_trach_vd'][data-id='{dong[0].pk}']"
    mo_luoi_toi_o(trang, live_server, bang, o)

    trang.dblclick(o)
    trang.wait_for_selector("#vd-assign-cell[data-ready]:not([hidden])", timeout=5_000)
    vi_tri = trang.evaluate(f"""() => {{ const o = document.querySelector("{o}").getBoundingClientRect();
        const s = document.querySelector('#vd-assign-cell select').getBoundingClientRect();
        return {{trong_o: Math.abs(s.top - o.top) < 6 && Math.abs(s.left - o.left) < 6}}; }}""")
    assert vi_tri["trong_o"], "ô chọn phải nằm ngay trong ô"
    nhan = trang.eval_on_selector_all("#vd-assign-cell select option", "os => os.map(o => o.textContent)")
    assert employee_code(nv) in nhan and any("Chưa gán" in n for n in nhan), nhan
    chup(trang, "phan-cong-o-chon")

    trang.keyboard.press("Escape")
    trang.wait_for_function("() => document.getElementById('vd-assign-cell').hidden", timeout=3_000)
    assert not WaybillAssignment.objects.filter(record=dong[0], delivery__isnull=False).exists()

    trang.dblclick(o)
    trang.wait_for_selector("#vd-assign-cell[data-ready]:not([hidden])", timeout=5_000)
    trang.select_option("#vd-assign-cell select", str(nv.pk))
    trang.wait_for_function(f"() => document.querySelector(\"{o}\")?.textContent.includes('{employee_code(nv)}')",
                            timeout=8_000)
    assert WaybillAssignment.objects.get(record=dong[0]).delivery_id == nv.pk
    assert trang.evaluate("() => document.getElementById('vd-assign-cell').hidden")

    # Bàn phím: Enter mở, phím di chuyển (Home/mũi tên) (chưa lưu), Enter mới lưu — bỏ giao về "Chưa gán".
    trang.click(o)
    trang.keyboard.press("Enter")
    trang.wait_for_selector("#vd-assign-cell[data-ready]:not([hidden])", timeout=5_000)
    trang.wait_for_function("() => document.activeElement === document.querySelector('#vd-assign-cell select')")
    assert trang.evaluate("() => document.querySelector('#vd-assign-cell select').value") == str(nv.pk)
    trang.keyboard.press("Home")
    trang.wait_for_timeout(300)
    assert trang.evaluate("() => document.querySelector('#vd-assign-cell select').value") == ""
    assert WaybillAssignment.objects.get(record=dong[0]).delivery_id == nv.pk, "phím di chuyển không được tự lưu"
    trang.keyboard.press("Enter")
    trang.wait_for_function("() => document.getElementById('vd-assign-cell').hidden", timeout=8_000)
    trang.wait_for_function(f"() => !document.querySelector(\"{o}\")?.textContent.includes('{employee_code(nv)}')",
                            timeout=8_000)
    assert WaybillAssignment.objects.get(record=dong[0]).delivery_id is None
    assert not loi_js, loi_js


def test_nhan_vien_thuong_khong_co_o_chon_phan_cong(live_server, trang, dang_nhap, kn_crm, feedback,
                                                    nguoi_dung):  # noqa: F811
    """AC-21.15 — Nhân viên Vận đơn thường (không được phân công) bấm đúp ô phụ trách không có ô chọn"""
    bang, _, dong = feedback
    dang_nhap(trang, nguoi_dung["staff_vd"])
    o = f".mg-cell[data-code='phu_trach_vd'][data-id='{dong[0].pk}']"
    mo_luoi_toi_o(trang, live_server, bang, o)
    trang.dblclick(o)
    trang.wait_for_timeout(800)
    assert not trang.evaluate("() => { const e = document.getElementById('vd-assign-cell'); return !!e && !e.hidden; }")
