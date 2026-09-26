"""Bố cục Báo cáo tổng hợp bằng Chromium thật: ba trạng thái bộ lọc, ngăn kéo, toàn màn hình, cột định danh ghim.

Chạy trong container `web` khi đã `playwright install chromium`; thiếu thì tự bỏ qua.
"""
import pytest

from reports.models import ReportSource
from reports.tests.test_aggregations import bang_mkt, dong_mau  # noqa: F401 — fixture
from reports.tests.test_mkt_excel import marketing_scope  # noqa: F401 — fixture
from tests.e2e.conftest import LY_DO, MAT_KHAU, chup, sync_playwright

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]

ST = "()=>document.getElementById('report-workspace').dataset.filters"
FOCUS = "()=>document.documentElement.classList.contains('sp-report-focus')"
KHONG_FOCUS = "()=>!document.documentElement.classList.contains('sp-report-focus')"


@pytest.fixture
def trinh_duyet_moi():
    if sync_playwright is None:
        pytest.skip(LY_DO)
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Exception as loi:
            pytest.skip(f"{LY_DO} — {str(loi).splitlines()[0][:160]}")
        yield browser
        browser.close()


def _mo(browser, live_server, user, width, height, url):
    ctx = browser.new_context(viewport={"width": width, "height": height}, locale="vi-VN")
    page = ctx.new_page()
    page.set_default_timeout(15_000)
    page.goto(live_server.url + "/dang-nhap/")
    page.fill("input[name=username]", user.username)
    page.fill("input[name=password]", MAT_KHAU)
    page.click("button[type=submit]")
    page.wait_for_load_state("networkidle")
    page.goto(live_server.url + url, wait_until="networkidle")
    return ctx, page


@pytest.fixture
def nguon(marketing_scope):
    return ReportSource.objects.create(table=marketing_scope.table, kind="sale",
                                       columns={"mess": "so_mess", "orders": "so_don", "sales": "doanh_so", "market": "thi_truong"})


def test_bo_loc_ba_trang_thai_va_toan_man_hinh(live_server, trinh_duyet_moi, nguon, nguoi_dung):
    """AC-22.13 — Màn rộng: bộ lọc mở 260px, thu gọn thành thanh dọc 48px có huy hiệu, nhớ trong phiên; Toàn màn
    hình tự chuyển sang thanh dọc, Escape thoát; màn hẹp: ngăn kéo mặc định đóng, mở phủ backdrop, Escape đóng trước
    rồi mới thoát toàn màn hình; cuộn ngang bảng thì cột định danh đứng yên"""
    url = f"/bao-cao/tong-hop/?nguon={nguon.table.code}&tu=2026-08-01&den=2026-08-31&team={nguoi_dung['staff_sale_1'].profile.team_id}"
    ctx, page = _mo(trinh_duyet_moi, live_server, nguoi_dung["manager_sale"], 1440, 900, url)
    try:
        assert page.evaluate(ST) == "open"
        assert page.evaluate("()=>Math.round(document.getElementById('report-filter-panel').getBoundingClientRect().width)") == 260
        page.click("#report-toggle-filters")
        page.wait_for_function(f"{ST}==='rail'")
        # Lưới chuyển cột có hiệu ứng 0,2 s — chờ tới bề rộng đích thay vì đo ngay.
        page.wait_for_function("()=>Math.round(document.getElementById('report-filter-panel').getBoundingClientRect().width)===48")
        assert page.locator(".panel-rail .huy-hieu").inner_text() == "2"   # Kỳ tự chọn + Team
        assert page.evaluate("()=>JSON.parse(sessionStorage.getItem('knjsc-report-layout'))") == {"filters": "rail", "focus": False}
        page.reload(wait_until="networkidle")
        assert page.evaluate(ST) == "rail", "nhớ trạng thái trong phiên"
        page.click("#report-panel-expand")
        page.wait_for_function(f"{ST}==='open'")
        page.click("#report-toggle-focus")
        page.wait_for_function(FOCUS)
        assert page.evaluate(ST) == "rail", "toàn màn hình nhường chỗ cho bảng"
        chup(page, "bao-cao-toan-man-hinh-1440")
        # Toàn màn hình với viewport thấp hơn bảng: khung cuộn co lại trong viewport, thanh kéo ngang và
        # phân trang vẫn thấy — không tràn ra ngoài (yêu cầu 18.09 tối)
        page.set_viewport_size({"width": 1440, "height": 240})
        khung = page.evaluate("""()=>{const s=document.querySelector('.report-table-scroll'),p=document.querySelector('.report-results>.phan-trang');
            const r=s.getBoundingClientRect();return {day:Math.round(r.bottom),cao:innerHeight,cuon_doc:s.scrollHeight>s.clientHeight,
            phan_trang:p?Math.round(p.getBoundingClientRect().bottom):null}}""")
        assert khung["day"] <= khung["cao"] and khung["cuon_doc"], khung
        assert khung["phan_trang"] is None or khung["phan_trang"] <= khung["cao"], khung
        chup(page, "bao-cao-toan-man-hinh-thap")
        page.set_viewport_size({"width": 1440, "height": 900})
        page.keyboard.press("Escape")
        page.wait_for_function(KHONG_FOCUS)
        assert page.evaluate(ST) == "rail"
        # Khoá cũ {hidden:true} vẫn đọc được thành thanh dọc
        page.evaluate("()=>sessionStorage.setItem('knjsc-report-layout', JSON.stringify({hidden:true, focus:false}))")
        page.reload(wait_until="networkidle")
        assert page.evaluate(ST) == "rail"
    finally:
        ctx.close()
    ctx, page = _mo(trinh_duyet_moi, live_server, nguoi_dung["manager_sale"], 390, 844, url)
    try:
        assert page.evaluate(ST) == "closed", "màn hẹp: ngăn kéo mặc định đóng"
        assert not page.evaluate("()=>document.documentElement.scrollWidth>document.documentElement.clientWidth")
        page.click("#report-toggle-filters")
        page.wait_for_function(f"{ST}==='open'")
        assert page.evaluate("()=>getComputedStyle(document.getElementById('report-backdrop')).display") == "block"
        page.wait_for_function("()=>Math.round(document.getElementById('report-filter-panel').getBoundingClientRect().x)===0")   # ngăn kéo trượt 0,2 s
        chup(page, "bao-cao-ngan-keo-390")
        page.keyboard.press("Escape")
        page.wait_for_function(f"{ST}==='closed'")
        ghim = page.evaluate("""()=>{const s=document.querySelector('.report-table-scroll');const id=s.querySelector('tbody tr:not(.report-total):not(.report-subtotal) .report-identity');
            const th=s.querySelector('thead th:not(.report-identity)');const a=id.getBoundingClientRect().left,b=th.getBoundingClientRect().left;s.scrollLeft=300;
            return new Promise(r=>requestAnimationFrame(()=>r({cuon:s.scrollLeft,id_dx:Math.round(id.getBoundingClientRect().left-a),th_dx:Math.round(th.getBoundingClientRect().left-b)})))}""")
        assert ghim["cuon"] > 0 and ghim["id_dx"] == 0 and ghim["th_dx"] < 0, ghim
        page.click("#report-toggle-focus")
        page.wait_for_function(FOCUS)
        page.click("#report-toggle-filters")
        page.wait_for_function(f"{ST}==='open'")
        page.keyboard.press("Escape")
        page.wait_for_function(f"{ST}==='closed'")
        assert page.evaluate(FOCUS), "Escape đóng ngăn kéo trước, chưa thoát toàn màn hình"
        page.keyboard.press("Escape")
        page.wait_for_function(KHONG_FOCUS)
    finally:
        ctx.close()


def test_the_tong_quan_moi_chi_tieu_mot_hang(live_server, trinh_duyet_moi, nguon, nguoi_dung):
    """AC-22.17 — Thẻ Báo cáo tổng hợp trên Tổng quan: mỗi chỉ tiêu một hàng nhãn–số, số tiền
    dài (cỡ nghìn tỉ ₫) không bị bẻ giữa chữ số ở màn rộng, 390 px không tràn ngang"""
    from forms_builder.models import DataRecord
    dong = DataRecord.objects.filter(table=nguon.table).order_by("pk").first()
    dong.data["doanh_so"] = "4419192172500"
    dong.val_revenue = 4419192172500
    dong.save(update_fields=["data", "val_revenue"])
    url = f"/?sale_nguon={nguon.table.code}&tu=2026-08-01&den=2026-08-31"
    do = """() => {
        const the = [...document.querySelectorAll('.dashboard-activity-card')]
            .find(t => t.querySelector('.dashboard-metric'));
        if (!the) return {loi: 'không thấy thẻ có chỉ tiêu'};
        const hang = [...the.querySelectorAll('.dashboard-metric')].map(m => {
            const dt = m.querySelector('dt').getBoundingClientRect(), dd = m.querySelector('dd');
            const b = dd.getBoundingClientRect(), dong = parseFloat(getComputedStyle(dd).lineHeight);
            return {nhan: m.querySelector('dt').textContent.trim(), so: dd.textContent.trim(),
                    trai: Math.round(m.getBoundingClientRect().left), cung_hang: Math.abs(b.top - dt.top) < 4,
                    so_dong: Math.round(b.height / dong)};
        });
        return {hang, tran: document.documentElement.scrollWidth - innerWidth};
    }"""
    for rong, cao in ((1440, 900), (390, 844)):
        ctx, page = _mo(trinh_duyet_moi, live_server, nguoi_dung["manager_sale"], rong, cao, url)
        kq = page.evaluate(do)
        chup(page, f"tong-quan-the-bao-cao-{rong}")
        ctx.close()
        assert "loi" not in kq, kq
        assert kq["tran"] <= 0, f"{rong}px tràn ngang {kq['tran']}px"
        assert len({h["trai"] for h in kq["hang"]}) == 1, f"{rong}px: chỉ tiêu không xếp mỗi cái một hàng: {kq['hang']}"
        assert all(h["cung_hang"] for h in kq["hang"]), kq["hang"]
        if rong == 1440:
            dai = [h for h in kq["hang"] if len(h["so"]) >= 15]
            assert dai, f"dữ liệu thử phải có một số tiền dài: {kq['hang']}"
            assert all(h["so_dong"] == 1 for h in kq["hang"]), f"số bị bẻ dòng ở 1440px: {kq['hang']}"
