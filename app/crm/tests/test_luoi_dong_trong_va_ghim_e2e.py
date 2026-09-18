"""Lưới KN CRM bằng Chromium thật: 1.000 dòng trống sẵn và cột ghim đứng đầu thứ tự nhìn thấy.

Chạy trong container `web` khi đã `playwright install chromium`; thiếu thì tự bỏ qua
(fixture `trinh_duyet` của `tests/e2e/conftest.py`). Góp ý chủ dự án 17.09.2026 sau ADR-033.
"""
import re

import pytest

from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, DataRecord, TableDef
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
JS_TOTAL = "()=>KNJSC_MASTER.diagnostics().total"


def _frames(page):
    page.evaluate("()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")


def _so_dong_that(page):
    return int(re.search(r"([\d.]+) dòng khớp", page.evaluate(JS_COUNT)).group(1).replace(".", ""))


@pytest.fixture
def bang_thuong(departments, nguoi_dung):
    """Bảng thường của bộ phận Vận đơn: Admin được thêm dòng, không cột bắt buộc."""
    bang = TableDef.objects.create(name="Sổ tay kiểm", code="so_tay_kiem",
                                   department=departments["vd"], created_by=nguoi_dung["admin"])
    for i, (ten, ma, kieu, nhan) in enumerate([
        ("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
        ("Mã đơn", "ma_don", FieldType.TEXT, ""),
        ("Tên khách", "ten_khach", FieldType.TEXT, Meaning.CUSTOMER),
        ("Ghi chú", "ghi_chu", FieldType.TEXT, ""),
    ]):
        ColumnDef.objects.create(table=bang, name=ten, code=ma, field_type=kieu, meaning=nhan, order=i)
    return bang


def test_mot_nghin_dong_trong_san_va_tao_dong_khong_tai_lai(live_server, trang, dang_nhap, bang_thuong, nguoi_dung):
    """AC-11.37 — Mở bảng có quyền thêm thì có sẵn 1.000 dòng trống; gõ một dòng thành bản ghi mà không tải lại lưới,
    tổng dòng không đổi (dòng trống chỉ bù theo đợt); tới dòng trống áp chót thì thêm 1.000 dòng nữa"""
    dang_nhap(trang, nguoi_dung["admin"])
    yeu_cau = []
    trang.on("request", lambda r: yeu_cau.append(r.url) if "/du-lieu/" in r.url else None)
    trang.goto(live_server.url + f"/bang-tinh/{bang_thuong.code}/")
    trang.locator(".mg-cell[data-id]").first.wait_for()
    _frames(trang)
    assert trang.evaluate(JS_COUNT) == "0 dòng khớp bộ lọc · 1.000 dòng trống để nhập"
    assert trang.evaluate(JS_TOTAL) == 1000

    # Gõ vào dòng trống đầu tiên: F2 mở ô nhập, Tab rời ô là tự lưu
    o = trang.locator('.mg-cell[data-r="0"][data-code="ten_khach"]')
    o.click()
    trang.keyboard.press("F2")
    trang.locator("#mg-editor .o-nhap").fill("Khách kiểm 1000 dòng")
    truoc = len(yeu_cau)
    trang.keyboard.press("Tab")
    try:
        trang.wait_for_function("()=>document.getElementById('bt-trang-thai')?.textContent==='Đã lưu'", timeout=40000)
    except Exception as loi:
        raise AssertionError("chưa lưu: " + trang.evaluate(
            "()=>[document.getElementById('bt-trang-thai')?.textContent, document.getElementById('mg-message')?.textContent].join(' | ')")) from loi
    trang.wait_for_timeout(600)
    assert DataRecord.objects.filter(table=bang_thuong).count() == 1
    assert len(yeu_cau) == truoc, "tạo dòng không được tải lại khối JSON"
    assert trang.evaluate(JS_COUNT) == "1 dòng khớp bộ lọc · 999 dòng trống để nhập"
    assert trang.evaluate(JS_TOTAL) == 1000, "nháp thành bản ghi thì tổng dòng giữ nguyên, không sinh hàng"
    assert trang.evaluate("()=>+document.querySelector('.mg-cell[data-r=\"0\"]').dataset.id") > 0
    chup(trang, "luoi-1000-dong-trong-sau-tao")

    # Tới dòng trống áp chót (Ctrl+End) thì thêm một đợt 1.000 nữa
    trang.locator('.mg-cell[data-r="0"][data-code="ma_don"]').click()
    trang.wait_for_function("()=>!document.getElementById('mg-editor').hidden")   # bấm ô là mở ô nhập ngay (ADR-033)
    trang.keyboard.press("Escape")                                                # Esc trả phím về lưới
    trang.wait_for_function("()=>document.getElementById('mg-editor').hidden&&document.activeElement.id==='mg-viewport'")
    trang.keyboard.press("Control+End")
    _frames(trang)
    try:
        trang.wait_for_function("()=>KNJSC_MASTER.diagnostics().total===2000")
    except Exception as loi:
        raise AssertionError("chưa thêm đợt 1.000: " + str(trang.evaluate(
            "()=>({total:KNJSC_MASTER.diagnostics().total, active:document.activeElement.id||document.activeElement.className, editor:document.getElementById('mg-editor').hidden, chon:document.getElementById('mg-selection').textContent, msg:document.getElementById('mg-message')?.textContent})"))) from loi
    assert trang.evaluate(JS_COUNT) == "1 dòng khớp bộ lọc · 1.999 dòng trống để nhập"
    trang.reload()
    trang.locator(".mg-cell[data-id]").first.wait_for()
    assert _so_dong_that(trang) == 1


def test_cot_ghim_dung_dau_va_boi_den_theo_thu_tu_nhin_thay(live_server, trang, dang_nhap, feedback, nguoi_dung):
    """AC-11.38 — Cột ghim không ở đầu thứ tự cột vẫn được xếp lên đầu khi vẽ: không ô trống ở vị trí gốc,
    không che cột khác; kéo chọn từ cột ghim sang cột thường bôi đúng dải liền nhau và địa chỉ A1:E2"""
    table = feedback[0]
    dang_nhap(trang, nguoi_dung["admin"])
    trang.goto(live_server.url + f"/bang-tinh/{table.code}/")
    trang.locator(".mg-cell[data-id]").first.wait_for()
    cau_hinh = trang.evaluate("()=>JSON.parse(document.getElementById('mg-config').textContent)")
    khoa = f"kn-master:{cau_hinh['user']}:{cau_hinh['table']}"
    ma = [c.code for c in table.columns.order_by("order")]
    ghim = ["ma_don", "ten_khach", "so_dien_thoai"]
    thu_tu = [c for c in ma if c not in ghim][:4] + ghim + [c for c in ma if c not in ghim][4:]
    trang.evaluate("([k,o])=>localStorage.setItem(k,JSON.stringify({order:o}))", [khoa, thu_tu])
    trang.reload()
    trang.locator(".mg-cell[data-id]").first.wait_for()
    _frames(trang)
    dau = trang.evaluate(JS_HEADERS)
    assert [h["code"] for h in dau[:3]] == ghim and all(h["pin"] for h in dau[:3]) and not dau[3]["pin"]
    assert dau[3]["code"] == thu_tu[0], "cột thường đầu tiên đứng ngay sau cột ghim, không bị che"
    assert max(abs(dau[i + 1]["x"] - dau[i]["x"] - dau[i]["w"]) for i in range(len(dau) - 1)) == 0, "không ô trống giữa các cột"

    trang.locator(f'.mg-cell[data-r="0"][data-code="{dau[0]["code"]}"]').click()
    trang.locator(f'.mg-cell[data-r="1"][data-code="{dau[4]["code"]}"]').click(modifiers=["Shift"])
    _frames(trang)
    boi = set(trang.evaluate("()=>[...document.querySelectorAll('.mg-cell.mg-selected')].map(c=>c.dataset.code)"))
    assert boi == {h["code"] for h in dau[:5]}
    assert trang.evaluate("()=>document.getElementById('mg-selection').textContent").startswith("A1:E2")
    chup(trang, "luoi-cot-ghim-dung-dau-boi-den")
    trang.evaluate("k=>localStorage.removeItem(k)", khoa)


TRACER = ("()=>{window.__t0=performance.now();window.__log=[];"
          "const ed=document.getElementById('mg-editor'),vp=document.getElementById('mg-viewport');"
          "const tick=()=>{const r=ed.getBoundingClientRect(),vr=vp.getBoundingClientRect();"
          "const dots=[...document.querySelectorAll('.mg-cell')].filter(c=>c.textContent==='…'&&c.getBoundingClientRect().top<vr.bottom).length;"
          "window.__log.push({ed:ed.hidden?null:Math.round(r.top),dots,total:KNJSC_MASTER.diagnostics().total,h:document.getElementById('mg-canvas').offsetHeight,win:Math.round(scrollY),vpTop:Math.round(vr.top),vpH:vp.clientHeight,vpScroll:vp.scrollTop,css:document.styleSheets.length});"
          "requestAnimationFrame(tick)};requestAnimationFrame(tick);}")


def _go_va_enter(trang, r0, code, n):
    trang.locator(f'.mg-cell[data-r="{r0}"][data-code="{code}"]').click()
    for i in range(n):
        # Ô nhập mở xong mới gõ (như người dùng); gõ khi ô chưa mở thì dấu cách cuộn viewport.
        trang.wait_for_function(f"()=>!document.getElementById('mg-editor').hidden&&document.querySelector('.mg-current')?.dataset.r==='{r0 + i}'")
        trang.keyboard.type(f"Kiểm Enter {i}")
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


def test_go_lien_tiep_roi_enter_khong_giat(live_server, trang, dang_nhap, bang_thuong, nguoi_dung):
    """AC-11.40 — Gõ liên tiếp nhiều dòng rồi Enter (dòng trống lẫn dòng có sẵn) không giật: ô nhập không nhảy
    ngược lên, tổng dòng và chiều cao lưới không đổi từng dòng, không ô `…` kể cả khi tới kỳ hỏi mốc 8 giây
    (mốc vừa đổi là do chính mình lưu), mọi giá trị đã vào cơ sở dữ liệu"""
    dang_nhap(trang, nguoi_dung["admin"])
    trang.goto(live_server.url + f"/bang-tinh/{bang_thuong.code}/")
    trang.locator(".mg-cell[data-id]").first.wait_for()
    _frames(trang)
    trang.evaluate(TRACER)
    # 5 dòng trống liên tiếp
    _go_va_enter(trang, 0, "ghi_chu", 5)
    trang.wait_for_timeout(9000)      # qua một kỳ hỏi mốc `moi-nhat/`
    bc = _bao_cao(trang)
    print("TOPS-1", bc)
    assert bc["nhay_len"] == 0, bc
    assert bc["tong"] == {1000} and len(bc["cao"]) == 1, bc
    assert bc["dots"] == 0, "ô không được hoá `…` khi mốc đổi do chính mình lưu"
    assert DataRecord.objects.filter(table=bang_thuong).count() == 5
    assert trang.evaluate(JS_COUNT) == "5 dòng khớp bộ lọc · 995 dòng trống để nhập"
    # rồi sửa lại 3 dòng có sẵn
    trang.evaluate(TRACER)
    _go_va_enter(trang, 0, "ten_khach", 3)
    trang.wait_for_timeout(9000)
    bc = _bao_cao(trang)
    assert bc["nhay_len"] == 0 and bc["dots"] == 0 and bc["tong"] == {1000}, bc
    values = sorted(v for v in DataRecord.objects.filter(table=bang_thuong).values_list("data__ten_khach", flat=True) if v)
    assert values == ["Kiểm Enter 0", "Kiểm Enter 1", "Kiểm Enter 2"]
    chup(trang, "luoi-go-enter-khong-giat")
