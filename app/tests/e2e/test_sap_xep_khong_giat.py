"""Bấm tiêu đề cột để sắp xếp không làm trang giật — AC-21.12 (lưới KN CRM), AC-7.13 (Bảng dữ liệu ERP).

Chủ dự án báo 28.09.2026: bấm sắp xếp theo Quốc gia thì "cả trang bị load". Lưới xử lý đổi
thứ tự như mở bảng mới: cuộn về cột đầu, đứng hình (mũi tên tiêu đề chưa đổi) tới khi dữ liệu
về, đặt lại chiều cao dòng và tải lại cả trang HTML chỉ để lấy khung lọc. Bảng dữ liệu ERP thì
tải lại trang thật.
Phải đo bằng trình duyệt thật: cái giật là chuyện của từng khung hình.
"""
import time

import pytest

from crm.tests.test_waybill_feedback import feedback  # noqa: F401  (fixture dùng lại)

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]

#: Theo dõi từng khung hình: có ô "…" nào không, có tải lại trang HTML của lưới không
THEO_DOI = """() => {
    window.__giat = {ba_cham: 0, tai_html: 0, chay: true};
    const goc = window.fetch;
    window.fetch = (url, tuy = {}) => {
        const h = tuy.headers || {};
        if (h['X-Master-Filters'] || (h.get && h.get('X-Master-Filters'))) window.__giat.tai_html++;
        return goc(url, tuy);
    };
    (function khung() {
        if (!window.__giat.chay) return;
        if ([...document.querySelectorAll('.mg-cell')].some(o => o.textContent === '…')) window.__giat.ba_cham++;
        requestAnimationFrame(khung);
    })();
}"""


@pytest.fixture
def kn_crm(settings):
    """Lưới nằm trong dịch vụ KN CRM cổng 8021 — ADR-012."""
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.BANGTINH_URL = ""
    return settings


def _dat(dong, **gia_tri):
    """Lưu trọn bản ghi để cột chỉ mục (tên khách, quốc gia…) đồng bộ — sắp xếp đọc cột đó."""
    dong.data.update(gia_tri)
    dong.save()


def test_luoi_sap_xep_theo_quoc_gia_khong_giat(live_server, trang, dang_nhap, kn_crm,
                                               feedback, nguoi_dung):  # noqa: F811
    """AC-21.12 — Bấm tiêu đề Quốc gia trên lưới: mũi tên đổi ngay (trước khi dữ liệu về), giữ vị
    trí cuộn ngang, không tải lại trang HTML, không khung hình nào hiện ô "…"; dòng đổi đúng thứ tự"""
    bang, _, dong = feedback
    _dat(dong[0], quoc_gia="Hoa Kỳ", ten_khach="Khách Mỹ")
    _dat(dong[1], quoc_gia="Canada", ten_khach="Khách Canada")
    loi_js = []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(trang, nguoi_dung["staff_vd"])
    trang.goto(f"{live_server.url}/bang-tinh/{bang.code}/")
    trang.wait_for_function(
        "() => [...document.querySelectorAll('.mg-cell')].some(e => e.dataset.id && e.textContent !== '…')",
        timeout=30_000)
    trang.wait_for_timeout(500)

    cuon = trang.evaluate("""() => { const vp = document.getElementById('mg-viewport');
        vp.scrollLeft = 150; return vp.scrollLeft; }""")
    assert cuon > 0, "lưới phải cuộn ngang được để kiểm giữ vị trí"
    trang.wait_for_selector("[data-sort='quoc_gia']")
    trang.wait_for_timeout(300)
    trang.evaluate(THEO_DOI)
    # Giả lập độ trễ mạng thật (VPS): máy chủ cục bộ trả 2 dòng nhanh tới mức lưới chưa kịp vẽ
    # khung hình trống nào, cái nháy chỉ lộ khi dữ liệu về chậm
    def cham(route):
        time.sleep(0.4)
        route.continue_()
    trang.route("**/du-lieu/**", cham)

    trang.click("[data-sort='quoc_gia']")
    trang.wait_for_function("() => new URLSearchParams(location.search).get('sap') === 'quoc_gia'")
    # Mũi tên đổi ngay khi bấm (trong khung hình kế), không đợi dữ liệu về
    trang.wait_for_function("() => document.querySelector(\"[data-sort='quoc_gia']\").textContent.includes('↑')",
                            timeout=200)
    trang.wait_for_function(
        """() => { const o = [...document.querySelectorAll(".mg-cell[data-code='ten_khach'][data-r='0']")];
                   return o.some(e => e.textContent.trim() === 'Khách Canada'); }""", timeout=15_000)
    trang.wait_for_timeout(600)
    giat = trang.evaluate("() => { window.__giat.chay = false; return window.__giat; }")
    sau = trang.evaluate("() => document.getElementById('mg-viewport').scrollLeft")

    loi = []
    if giat["ba_cham"]:
        loi.append(f"lưới xoá trắng thành '…' trong {giat['ba_cham']} khung hình")
    if giat["tai_html"]:
        loi.append("đổi thứ tự không được tải lại trang HTML của lưới")
    if abs(sau - cuon) > 1:
        loi.append(f"cuộn ngang nhảy từ {cuon} về {sau}")
    assert not loi, loi
    assert not loi_js, loi_js


def test_bang_du_lieu_sap_xep_khong_tai_lai_trang(live_server, trang, dang_nhap,
                                                  feedback, nguoi_dung):  # noqa: F811
    """AC-7.13 — Bảng dữ liệu ERP: bấm tiêu đề cột chỉ thay phần bảng (HTMX), trang không tải
    lại; địa chỉ trang mang tham số sắp xếp mới; dòng đổi đúng thứ tự; bấm lần nữa đảo chiều"""
    bang, _, dong = feedback
    _dat(dong[0], ten_khach="Bảo")
    _dat(dong[1], ten_khach="An")
    loi_js = []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(trang, nguoi_dung["admin"])
    trang.goto(f"{live_server.url}/bang/{bang.code}/")
    trang.wait_for_selector("table.bang-luoi")
    trang.evaluate("() => { window.__khong_tai_lai = true; }")

    tieu_de = "th.sap-xep a:has-text('Tên khách')"
    trang.click(tieu_de)
    trang.wait_for_function("() => new URLSearchParams(location.search).get('sap') === 'ten_khach'")
    trang.wait_for_selector("th[aria-sort='ascending'] a:has-text('Tên khách')")
    assert trang.evaluate("() => window.__khong_tai_lai === true"), "trang đã tải lại khi sắp xếp"
    cot = trang.evaluate("""() => { const th = [...document.querySelectorAll('table.bang-luoi thead th')];
        const i = th.findIndex(t => t.textContent.includes('Tên khách'));
        return [...document.querySelectorAll('table.bang-luoi tbody tr')].map(r => r.children[i].textContent.trim()); }""")
    assert cot[:2] == ["An", "Bảo"], cot

    trang.click(tieu_de)
    trang.wait_for_selector("th[aria-sort='descending'] a:has-text('Tên khách')")
    assert "chieu=giam" in trang.url
    assert trang.evaluate("() => window.__khong_tai_lai === true"), "bấm lần hai đã tải lại trang"
    assert not loi_js, loi_js


def test_bo_chip_loc_sau_khi_sap_xep_giu_thu_tu_moi(live_server, trang, dang_nhap, kn_crm,
                                                    feedback, nguoi_dung):  # noqa: F811
    """AC-21.12 — Chip lọc dựng sẵn lúc tải trang; sắp xếp xong (không tải lại) rồi bấm × bỏ
    chip thì vẫn giữ thứ tự vừa chọn, không quay về thứ tự cũ"""
    bang, _, dong = feedback
    _dat(dong[0], quoc_gia="Hoa Kỳ")
    _dat(dong[1], quoc_gia="Canada")
    dang_nhap(trang, nguoi_dung["staff_vd"])
    trang.goto(f"{live_server.url}/bang-tinh/{bang.code}/?f_quoc_gia=Canada")
    trang.wait_for_selector("#mg-chips a")
    trang.wait_for_function(
        "() => [...document.querySelectorAll('.mg-cell')].some(e => e.dataset.id && e.textContent !== '…')",
        timeout=30_000)
    trang.click("[data-sort='ten_khach']")
    trang.wait_for_function("() => new URLSearchParams(location.search).get('sap') === 'ten_khach'")
    trang.click("#mg-chips a")
    trang.wait_for_function("() => !new URLSearchParams(location.search).has('f_quoc_gia')")
    tham_so = trang.evaluate("() => Object.fromEntries(new URLSearchParams(location.search))")
    assert tham_so.get("sap") == "ten_khach" and tham_so.get("chieu") == "tang", tham_so
