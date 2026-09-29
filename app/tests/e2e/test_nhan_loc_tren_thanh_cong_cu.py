"""Nhãn bộ lọc đang bật nằm trên thanh công cụ, giữa "Cột" và "Định dạng" — AC-21.14.

Chủ dự án 28.09.2026: hàng nhãn lọc riêng dưới thanh công cụ đẩy trang tính xuống mỗi khi bật/tắt
một bộ lọc. Phải kiểm bằng trình duyệt thật: vị trí và chiều cao là chuyện hiển thị.
"""
import pytest

from crm.tests.test_waybill_feedback import feedback  # noqa: F401  (fixture dùng lại)

from .conftest import chup

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]


@pytest.fixture
def kn_crm(settings):
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.BANGTINH_URL = ""
    return settings


DO = """() => { const r = id => document.getElementById(id)?.getBoundingClientRect();
  const chips = [...document.querySelectorAll('#mg-chips a')].map(a => a.getBoundingClientRect());
  return {luoi: r('mg-viewport').top, cot: r('mg-columns-button'), dinh_dang: r('mg-format-button'),
          thanh: document.querySelector('.mg-toolbar').getBoundingClientRect(),
          trong_thanh: !!document.querySelector('.mg-toolbar #mg-chips'), chips, khung: r('mg-chips'),
          tran_ngang: document.documentElement.scrollWidth > innerWidth}; }"""


@pytest.mark.parametrize("rong", [1440, 1280])
def test_nhan_loc_nam_giua_cot_va_dinh_dang_khong_day_luoi(live_server, trang, dang_nhap, kn_crm, feedback,
                                                           nguoi_dung, rong):  # noqa: F811
    """AC-21.14 — Bật bộ lọc thì nhãn lọc hiện trên thanh công cụ, giữa nút Cột và Định dạng, cùng hàng;
    trang tính không bị đẩy xuống (đỉnh lưới giữ nguyên); nhiều nhãn thì cuộn ngang trong chỗ của nó"""
    bang, products, _ = feedback
    trang.set_viewport_size({"width": rong, "height": 800})
    dang_nhap(trang, nguoi_dung["staff_vd"])
    trang.goto(f"{live_server.url}/bang-tinh/{bang.code}/")
    trang.wait_for_selector(".mg-cell[data-code='ten_khach']")
    truoc = trang.evaluate(DO)

    trang.goto(f"{live_server.url}/bang-tinh/{bang.code}/?sp={products[0].code}"
               "&f_ten_khach=Kh%C3%A1ch%200&f_quoc_gia__rong=1&f_ma_don__co=1")
    trang.wait_for_selector("#mg-chips a")
    sau = trang.evaluate(DO)

    assert sau["trong_thanh"], "nhãn lọc phải nằm trong thanh công cụ"
    assert len(sau["chips"]) >= 2
    assert sau["luoi"] == truoc["luoi"], f"lưới bị đẩy xuống: {truoc['luoi']} → {sau['luoi']}"
    khung = sau["khung"]
    assert khung["left"] >= sau["cot"]["right"] - 1, "nhãn lọc phải nằm sau nút Cột"
    assert khung["right"] <= sau["dinh_dang"]["left"] + 1, "nhãn lọc không được đè lên nút Định dạng"
    assert khung["top"] >= sau["thanh"]["top"] and khung["bottom"] <= sau["thanh"]["bottom"]
    dau = sau["chips"][0]
    assert dau["left"] >= khung["left"] - 1 and dau["right"] <= khung["right"] + 1, "nhãn đầu phải thấy trọn"
    assert not sau["tran_ngang"]
    chup(trang, f"nhan-loc-tren-thanh-cong-cu-{rong}")
