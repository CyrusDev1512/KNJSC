"""Lưới KN CRM bằng Chromium thật: cột ghim đứng đầu thứ tự nhìn thấy, gõ liên tiếp rồi Enter không giật.

Chạy trong container `web` khi đã `playwright install chromium`; thiếu thì tự bỏ qua
(fixture `trinh_duyet` của `tests/e2e/conftest.py`). Góp ý chủ dự án 17.09.2026 sau ADR-033.

Cả hai bài chạy trên **bảng vận đơn**: từ ADR-040 (24.09.2026) KN CRM trả 404 cho mọi bảng
không phải vận đơn, nên bài kiểm lưới không dùng bảng thường được nữa.
"""
import re

import pytest

from forms_builder.models import DataRecord
from orders.services import order_service
from tests.e2e.conftest import LY_DO, MAT_KHAU, chup, sync_playwright

from .test_waybill_feedback import feedback  # noqa: F401 — fixture


# Trình duyệt theo từng bài (không dùng fixture phiên của tests/e2e): mở Chromium trong cùng
# luồng với bài, nên chạy chung với tests/e2e không dính lỗi "Sync API inside the asyncio loop".
@pytest.fixture
def trang():
    if sync_playwright is None:
        pytest.skip(LY_DO)
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Exception as loi:
            pytest.skip(f"{LY_DO} — {str(loi).splitlines()[0][:160]}")
        ctx = browser.new_context(viewport={"width": 1366, "height": 800}, locale="vi-VN")
        page = ctx.new_page()
        page.set_default_timeout(15_000)
        yield page
        ctx.close()
        browser.close()


@pytest.fixture
def dang_nhap(live_server):
    def _dang_nhap(page, user, mat_khau=MAT_KHAU):
        page.goto(live_server.url + "/dang-nhap/")
        page.fill("input[name=username]", user.username)
        page.fill("input[name=password]", mat_khau)
        page.click("button[type=submit]")
        page.wait_for_load_state("networkidle")
        assert "/dang-nhap/" not in page.url, "đăng nhập không thành"
        return page
    return _dang_nhap

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]

JS_HEADERS = ("()=>[...document.querySelectorAll('.mg-heading')].filter(h=>h.dataset.code)"
              ".map(h=>{const r=h.getBoundingClientRect();return {code:h.dataset.code,i:+h.dataset.column,"
              "x:Math.round(r.x),w:Math.round(r.width),pin:h.classList.contains('mg-pinned')}})"
              ".sort((a,b)=>a.i-b.i)")
JS_COUNT = "()=>document.getElementById('mg-count').textContent"


def _frames(page):
    page.evaluate("()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")


def _so_dong_that(page):
    return int(re.search(r"([\d.]+) dòng khớp", page.evaluate(JS_COUNT)).group(1).replace(".", ""))


def test_cot_ghim_dung_dau_va_boi_den_theo_thu_tu_nhin_thay(live_server, trang, dang_nhap, feedback, nguoi_dung):
    """AC-11.38 — Cột ghim không ở đầu thứ tự cột vẫn được xếp lên đầu khi vẽ: không ô trống ở vị trí gốc,
    không che cột khác; kéo chọn từ cột ghim sang cột thường bôi đúng dải liền nhau và đúng địa chỉ ô"""
    table = feedback[0]
    dang_nhap(trang, nguoi_dung["admin"])
    trang.goto(live_server.url + f"/bang-tinh/{table.code}/")
    trang.locator(".mg-cell[data-id]").first.wait_for()
    cau_hinh = trang.evaluate("()=>JSON.parse(document.getElementById('mg-config').textContent)")
    khoa = f"kn-master:{cau_hinh['user']}:{cau_hinh['table']}"
    ma = [c.code for c in table.columns.order_by("order")]
    ghim = ["ngay", "ma_don", "ten_khach", "so_dien_thoai"]
    thu_tu = [c for c in ma if c not in ghim][:4] + ghim + [c for c in ma if c not in ghim][4:]
    trang.evaluate("([k,o])=>localStorage.setItem(k,JSON.stringify({order:o}))", [khoa, thu_tu])
    trang.reload()
    trang.locator(".mg-cell[data-id]").first.wait_for()
    _frames(trang)
    dau = trang.evaluate(JS_HEADERS)
    # Không chốt cứng số cột ghim: bảng vận đơn còn cột ảo Trùng cũng ghim (ADR-036), và
    # sau này thêm/bớt cột ghim nữa thì bài vẫn phải kiểm đúng điều cần kiểm — mọi cột ghim
    # xếp lên đầu, cột thường nối ngay sau, không ô trống.
    pin = [h for h in dau if h["pin"]]
    thuong = [h for h in dau if not h["pin"]]
    assert dau == pin + thuong, "mọi cột ghim phải đứng trước cột thường khi vẽ"
    assert set(ghim) <= {h["code"] for h in pin}, f"bốn cột ghim của bảng vận đơn phải nằm trong nhóm ghim: {pin}"
    assert thuong[0]["code"] == thu_tu[0], "cột thường đầu tiên đứng ngay sau nhóm ghim, không bị che"
    assert max(abs(dau[i + 1]["x"] - dau[i]["x"] - dau[i]["w"]) for i in range(len(dau) - 1)) == 0, "không ô trống giữa các cột"

    trang.locator(f'.mg-cell[data-r="0"][data-code="{pin[0]["code"]}"]').click()
    trang.locator(f'.mg-cell[data-r="1"][data-code="{thuong[0]["code"]}"]').click(modifiers=["Shift"])
    _frames(trang)
    boi = set(trang.evaluate("()=>[...document.querySelectorAll('.mg-cell.mg-selected')].map(c=>c.dataset.code)"))
    assert boi == {h["code"] for h in pin + thuong[:1]}
    cot_cuoi = chr(ord("A") + len(pin))          # kéo từ cột ghim đầu sang cột thường đầu tiên
    assert trang.evaluate("()=>document.getElementById('mg-selection').textContent").startswith(f"A1:{cot_cuoi}2")
    chup(trang, "luoi-cot-ghim-dung-dau-boi-den")
    trang.evaluate("k=>localStorage.removeItem(k)", khoa)


TRACER = ("()=>{window.__t0=performance.now();window.__log=[];"
          "const ed=document.getElementById('mg-editor'),vp=document.getElementById('mg-viewport');"
          "const tick=()=>{const r=ed.getBoundingClientRect(),vr=vp.getBoundingClientRect();"
          "const dots=[...document.querySelectorAll('.mg-cell')].filter(c=>c.textContent==='…'&&c.getBoundingClientRect().top<vr.bottom).length;"
          "window.__log.push({ed:ed.hidden?null:Math.round(r.top),dots,total:KNJSC_MASTER.diagnostics().total,h:document.getElementById('mg-canvas').offsetHeight,win:Math.round(scrollY),vpTop:Math.round(vr.top),vpH:vp.clientHeight,vpScroll:vp.scrollTop,css:document.styleSheets.length});"
          "requestAnimationFrame(tick)};requestAnimationFrame(tick);}")


def _go_va_enter(trang, r0, code, n, nhan="Kiểm Enter"):
    """Gõ liên tiếp `n` dòng rồi Enter, đúng thao tác người dùng của ADR-033:
    bấm một lần chỉ chọn ô, gõ ký tự đầu mới mở ô nhập, Enter chỉ chuyển ô."""
    trang.locator(f'.mg-cell[data-r="{r0}"][data-code="{code}"]').click()
    for i in range(n):
        trang.wait_for_function(
            f"()=>document.getElementById('mg-editor').hidden"
            f"&&document.querySelector('.mg-current')?.dataset.r==='{r0 + i}'")
        trang.keyboard.type(nhan[0])
        trang.wait_for_function("()=>!document.getElementById('mg-editor').hidden")
        trang.keyboard.type(f"{nhan[1:]} {i}")
        trang.keyboard.press("Enter")
        trang.wait_for_timeout(700)
    trang.keyboard.press("Escape")
    trang.wait_for_function("()=>document.getElementById('bt-trang-thai')?.textContent==='Đã lưu'", timeout=40000)


def _bao_cao(trang):
    log = trang.evaluate("()=>window.__log")
    tops = [e["ed"] for e in log if e["ed"] is not None]
    doi = [t for i, t in enumerate(tops) if i == 0 or t != tops[i - 1]]
    moi = [(e["win"], e["vpTop"], e["vpH"], e["vpScroll"], e["css"]) for e in log]
    return {"nhay_len": sum(1 for a, b in zip(tops, tops[1:]) if b < a - 2), "tops": doi, "moi": sorted(set(moi))[:8],
            "tong": {e["total"] for e in log}, "cao": {e["h"] for e in log}, "dots": max(e["dots"] for e in log)}


@pytest.fixture
def van_don_sau_dong(feedback, nguoi_dung):
    """Bảng vận đơn với sáu dòng thật — đủ để gõ liên tiếp nhiều dòng rồi Enter.

    Bảng vận đơn cấm thêm dòng (`waybill_service.protect_table`) và KN CRM chỉ phục vụ
    bảng vận đơn (ADR-040), nên dòng phải có sẵn, không gõ vào dòng trống được nữa."""
    table, products, rows = feedback
    for i in range(len(rows), 6):
        order = order_service.create_order(
            phone=f"09000000{i:02d}", customer_name=f"Khách {i}",
            lines=[{"product": products[0].code, "quantity": 1, "unit_price": "10.00"}],
            actor=nguoi_dung["staff_sale_1"])
        rows.append(order.record)
    return table, rows


def test_go_lien_tiep_roi_enter_khong_giat(live_server, trang, dang_nhap, van_don_sau_dong, nguoi_dung):
    """AC-11.40 — Gõ liên tiếp nhiều dòng rồi Enter không giật: ô nhập không nhảy ngược lên, tổng dòng
    và chiều cao lưới không đổi từng dòng, không ô `…` kể cả khi tới kỳ hỏi mốc 8 giây (mốc vừa đổi là
    do chính mình lưu), mọi giá trị đã vào cơ sở dữ liệu"""
    table, rows = van_don_sau_dong
    tong = len(rows)
    dang_nhap(trang, nguoi_dung["admin"])
    trang.goto(live_server.url + f"/bang-tinh/{table.code}/")
    trang.locator(".mg-cell[data-id]").first.wait_for()
    _frames(trang)
    trang.evaluate(TRACER)
    # Năm dòng liên tiếp, cột chữ ngắn
    _go_va_enter(trang, 0, "ten_khach", 5)
    trang.wait_for_timeout(9000)      # qua một kỳ hỏi mốc `moi-nhat/`
    bc = _bao_cao(trang)
    print("TOPS-1", bc)
    assert bc["nhay_len"] == 0, bc
    assert bc["tong"] == {tong} and len(bc["cao"]) == 1, bc
    assert bc["dots"] == 0, "ô không được hoá `…` khi mốc đổi do chính mình lưu"
    assert _so_dong_that(trang) == tong, "gõ vào dòng có sẵn không được làm đổi tổng dòng"
    ten = [v for v in DataRecord.objects.filter(table=table).values_list("data__ten_khach", flat=True) if v]
    assert {f"Kiểm Enter {i}" for i in range(5)} <= set(ten), ten
    assert len(ten) == tong, "dòng không gõ tới phải giữ nguyên tên khách"
    # Lượt thứ hai trên cột khác, ngay sau lượt đầu
    trang.evaluate(TRACER)
    _go_va_enter(trang, 0, "thanh_pho", 3, nhan="Thành phố")
    trang.wait_for_timeout(9000)
    bc = _bao_cao(trang)
    assert bc["nhay_len"] == 0 and bc["dots"] == 0 and bc["tong"] == {tong}, bc
    tp = sorted(v for v in DataRecord.objects.filter(table=table).values_list("data__thanh_pho", flat=True) if v)
    assert tp == [f"Thành phố {i}" for i in range(3)], tp
    chup(trang, "luoi-go-enter-khong-giat")
