"""Bố cục Báo cáo tổng hợp bằng Chromium thật: ba trạng thái bộ lọc, ngăn kéo, toàn màn hình, cột định danh ghim.

Chạy trong container `web` khi đã `playwright install chromium`; thiếu thì tự bỏ qua.
"""
import pytest

from reports.models import ReportSource
from reports.tests.test_aggregations import bang_mkt, dong_mau  # noqa: F401 — fixture
from reports.tests.test_che_do_so_lieu import _nop
from reports.tests.test_mkt_derived_revenue import mkt_source, van_don  # noqa: F401 — fixture
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


#: Điểm giữa phần nhìn thấy của khung bảng (giao với khung cuộn của trang) — chỗ người dùng đặt chuột
DIEM_TREN_BANG = """()=>{const s=document.querySelector('.report-table-scroll').getBoundingClientRect(),
    m=document.querySelector('main.noi-dung').getBoundingClientRect();
    const tren=Math.max(s.top,m.top)+30,duoi=Math.min(s.bottom,m.bottom,innerHeight)-20;
    return [Math.round(s.left+s.width/2),Math.round((tren+duoi)/2)]}"""
#: [bảng đã cuộn, bảng cuộn tối đa, trang đã cuộn, trang cuộn tối đa]
VI_TRI = """()=>{const s=document.querySelector('.report-table-scroll'),m=document.querySelector('main.noi-dung');
    return [s.scrollTop,s.scrollHeight-s.clientHeight,m.scrollTop,m.scrollHeight-m.clientHeight]}"""


def _lan(page, nac):
    """Lăn bánh xe `nac` nấc xuống tại giữa phần nhìn thấy của khung bảng; trả VI_TRI."""
    x, y = page.evaluate(DIEM_TREN_BANG)
    assert page.evaluate(f"()=>document.querySelector('.report-table-scroll').contains(document.elementFromPoint({x},{y}))"), \
        "con trỏ phải nằm trên bảng"
    page.mouse.move(x, y)
    for _ in range(nac):
        page.mouse.wheel(0, 100)
        page.wait_for_timeout(15)
    page.wait_for_timeout(250)
    return page.evaluate(VI_TRI)


def test_lan_chuot_tren_bang_khong_ket(live_server, trinh_duyet_moi, nguon, nguoi_dung):
    """AC-22.19 — Lăn chuột với con trỏ đặt trên bảng không bị kẹt (TL-63, chủ dự án 28.09.2026): bảng ngắn
    hơn khung (không có gì để cuộn dọc) thì trang cuộn ngay; bảng dài thì bảng cuộn trước, cuộn hết bảng
    thì trang cuộn tiếp — khung bảng không chặn cuộn truyền ra trang"""
    from datetime import date, timedelta
    from forms_builder.models import DataRecord

    # Bảng ngắn: lọc một nhân sự — khối toàn kỳ và một khối ngày mỗi khối một dòng, vừa khung theo chiều dọc
    # nhưng rộng hơn khung (bảng thật nhiều cột luôn cuộn ngang): đúng lúc khung cuộn được một chiều thì nó
    # nuốt cú lăn dọc
    url = (f"/bao-cao/tong-hop/?nguon={nguon.table.code}&tu=2026-08-01&den=2026-08-31"
           f"&nhan_su={nguoi_dung['staff_sale_1'].pk}")
    # 1000×900: khung bảng vừa khít màn hình từ 03.10.2026 nên cần màn cao hơn để bảng ngắn lọt vừa khung dọc
    ctx, page = _mo(trinh_duyet_moi, live_server, nguoi_dung["manager_sale"], 1000, 900, url)
    try:
        bang, bang_max, trang, trang_max = page.evaluate(VI_TRI)
        ngang = page.evaluate("()=>{const s=document.querySelector('.report-table-scroll');return s.scrollWidth-s.clientWidth}")
        assert bang_max <= 0 < trang_max and ngang > 0, \
            f"tiền đề: bảng vừa khung dọc, tràn ngang, trang cuộn được — {[bang_max, ngang, trang_max]}"
        _, _, trang, _ = _lan(page, 10)
        assert trang > 0, "bảng ngắn: lăn chuột trên bảng mà trang không cuộn"
    finally:
        ctx.close()

    # Bảng dài: thêm 29 ngày cho bốn người — Tổng hợp không gộp là 25 khối ngày mỗi trang
    mau = list(DataRecord.objects.filter(table=nguon.table))
    DataRecord.objects.bulk_create([
        DataRecord(table=d.table, created_by=d.created_by, department=d.department, team=d.team,
                   val_date=date(2026, 8, 1) + timedelta(days=i), val_seller=d.val_seller,
                   val_product=d.val_product, val_revenue=d.val_revenue,
                   data={**d.data, "ngay": (date(2026, 8, 1) + timedelta(days=i)).isoformat()})
        for i in range(1, 30) for d in mau])
    url = f"/bao-cao/tong-hop/?nguon={nguon.table.code}&tu=2026-08-01&den=2026-08-31"
    ctx, page = _mo(trinh_duyet_moi, live_server, nguoi_dung["manager_sale"], 1440, 760, url)
    try:
        _, bang_max, _, trang_max = page.evaluate(VI_TRI)
        assert bang_max > 1000 and trang_max > 0, f"tiền đề: bảng dài hơn khung — {[bang_max, trang_max]}"
        bang, _, trang, _ = _lan(page, 5)
        assert bang > 0 and trang == 0, f"bảng dài: bảng phải cuộn trước — {[bang, trang]}"
        bang, bang_max, trang, _ = _lan(page, bang_max // 100 + 10)
        assert bang >= bang_max - 1, f"bảng chưa cuộn hết — {[bang, bang_max]}"
        assert trang > 0, "bảng dài: cuộn hết bảng rồi mà trang không cuộn tiếp"
    finally:
        ctx.close()


@pytest.fixture
def mkt_ba_loai_tien(bang_mkt, mkt_source, van_don):
    """Sáu ngày, hai marketer, ba loại tiền: mỗi khối có ba dòng TỔNG CỘNG dính chồng (ADR-046) và bảng đủ
    dài để cuộn, như video 30.09 (TL-69)."""
    from datetime import date, timedelta

    A, B = van_don["A"], van_don["B"]
    for i in range(6):
        ngay = date(2026, 8, 1) + timedelta(days=i)
        _nop(bang_mkt, A, 9, 0, cpqc="8000", ngay=ngay)
        _nop(bang_mkt, A, 10, 0, cpqc="500", thi_truong="Hoa Kỳ", tien="USD", ngay=ngay)
        _nop(bang_mkt, B, 11, 0, cpqc="3000", thi_truong="Philippines", tien="PHP", ngay=ngay)
    return bang_mkt


#: Mỗi bảng báo cáo: chiều cao thật của hàng tiêu đề và dòng TỔNG CỘNG, so với --head-h/--total-h mà dòng tổng
#: dính theo
DO_BANG = """()=>[...document.querySelectorAll('.report-table')].map(t=>{const cs=getComputedStyle(t),
    tong=t.querySelector('.report-total');return {tieu_de:t.tHead.getBoundingClientRect().height,
    head_h:parseFloat(cs.getPropertyValue('--head-h')),dong_tong:tong?tong.getBoundingClientRect().height:null,
    total_h:parseFloat(cs.getPropertyValue('--total-h'))}})"""
#: Màu tính ra của ô → [r, g, b, a] trong 0–1; Chrome trả rgb()/rgba(), hoặc color(srgb …) cho color-mix
MAU = r"""const mau=c=>{let m=/^rgba?\(([^)]+)\)$/.exec(c);if(m){const p=m[1].split(',').map(parseFloat);
    return [p[0]/255,p[1]/255,p[2]/255,p.length>3?p[3]:1]}m=/^color\(srgb ([^)]+)\)$/.exec(c);if(m){
    const [rgb,a]=m[1].split('/');return [...rgb.trim().split(/\s+/).map(parseFloat),a===undefined?1:parseFloat(a)]}
    throw new Error('màu lạ: '+c)};"""
#: Ô nào của dòng TỔNG CỘNG có nền trong suốt (chữ dòng đang cuộn bên dưới lộ ra), và ô chỉ số ở dòng tổng lệch
#: bao nhiêu phần 255 so với màu cũ lúc đứng yên: 45 % --accent-soft phủ trên nền bảng --surface
NEN_DONG_TONG = "()=>{" + MAU + r"""
    const o=[...document.querySelectorAll('.report-total>*')];
    const trong=o.filter(c=>mau(getComputedStyle(c).backgroundColor)[3]<1).map(c=>c.className||c.tagName);
    const thu=v=>{const d=document.createElement('div');d.style.background=`var(${v})`;document.body.append(d);
        const c=mau(getComputedStyle(d).backgroundColor);d.remove();return c};
    const a=thu('--accent-soft'),s=thu('--surface');
    const chi_so=document.querySelector('.report-total>td.o-chi-so:not(.o-tot):not(.o-canh-bao):not(.o-xau)');
    const c=chi_so&&mau(getComputedStyle(chi_so).backgroundColor);
    return {so_o:o.length,trong:[...new Set(trong)],co_o_chi_so:!!chi_so,
            lech_mau:c?Math.max(...[0,1,2].map(i=>Math.abs(c[i]-(0.45*a[i]+0.55*s[i]))))*255:null}}"""
#: Cuộn khung bảng vào giữa khối đầu (hàng tiêu đề đã dính trên cùng); trả khoảng hở (px) giữa đáy tiêu đề và
#: dòng TỔNG CỘNG đầu, giữa các dòng tổng liền nhau
VI_TRI_DINH = """()=>new Promise(r=>{const s=document.querySelector('.report-table-scroll'),t=s.querySelector('.report-table');
    const muon=t.offsetTop+60;s.scrollTop=muon;requestAnimationFrame(()=>requestAnimationFrame(()=>{
    const k=s.getBoundingClientRect().top,th=t.querySelector('thead th:not(.report-identity)').getBoundingClientRect();
    const tong=[...t.querySelectorAll('.report-total')].map(tr=>tr.querySelector('td:not(.report-identity)').getBoundingClientRect());
    r({da_cuon:s.scrollTop>=muon-1,tieu_de_dinh:Math.round(th.top-k),ho_dau:Math.round(tong[0].top-th.bottom),
       ho_giua:tong.slice(1).map((b,i)=>Math.round(b.top-tong[i].bottom))})}))})"""

#: Cuộn trang tới khung bảng (màn thường: bảng nằm dưới bộ lọc) để ảnh chụp thấy chỗ dòng tổng dính
TOI_KHUNG_BANG = "()=>document.querySelector('.report-table-scroll').scrollIntoView({block:'start'})"


def _lech(bangs):
    """Bảng có dòng tổng dính sai chỗ: --head-h khác chiều cao tiêu đề thật, hay --total-h khác dòng tổng, quá 1 px."""
    return [(i, b) for i, b in enumerate(bangs) if abs(b["head_h"] - b["tieu_de"]) > 1
            or (b["dong_tong"] is not None and abs(b["total_h"] - b["dong_tong"]) > 1)]


def _kiem_nen(nen, noi):
    assert nen["so_o"] and nen["co_o_chi_so"], f"{noi}: tiền đề — cần dòng TỔNG CỘNG có ô chỉ số: {nen}"
    assert not nen["trong"], f"{noi}: ô dòng TỔNG CỘNG nền trong suốt, chữ dòng cuộn bên dưới lộ ra: {nen['trong']}"
    assert nen["lech_mau"] <= 1.5, f"{noi}: màu ô chỉ số ở dòng tổng khác trước {nen['lech_mau']:.1f}/255"


def _kiem_dinh(vi_tri, noi):
    assert vi_tri["da_cuon"] and vi_tri["tieu_de_dinh"] in (0, 1), \
        f"{noi}: tiền đề — khung phải cuộn, tiêu đề dính: {vi_tri}"
    assert abs(vi_tri["ho_dau"]) <= 1, f"{noi}: dòng TỔNG CỘNG đầu cách đáy tiêu đề {vi_tri['ho_dau']} px"
    assert all(abs(h) <= 1 for h in vi_tri["ho_giua"]), f"{noi}: các dòng TỔNG CỘNG không liền nhau: {vi_tri['ho_giua']}"


def test_dong_tong_dinh_nen_dac_va_sat_tieu_de(live_server, trinh_duyet_moi, mkt_ba_loai_tien, nguoi_dung):
    """AC-22.21 — Dòng TỔNG CỘNG dính đọc được (TL-69, chủ dự án 30.09.2026): mọi ô của dòng TỔNG CỘNG có nền
    đặc ở chế độ sáng và tối, kể cả cột chỉ số (màu nhìn như cũ: 45 % nền chỉ số trên nền bảng), nên dòng đang
    cuộn bên dưới không lộ chữ; dòng tổng đầu dính sát dưới hàng tiêu đề của chính bảng đó và các dòng tổng
    xếp liền nhau — đúng cả khi khung bảng giãn mà cửa sổ không đổi cỡ (Toàn màn hình, thu bộ lọc: hiệu ứng
    0,2 s), ở màn hẹp và ở Bảng dữ liệu dạng báo cáo (cùng khối bảng)"""
    manager = nguoi_dung["manager_mkt"]
    ky = "tu=2026-08-01&den=2026-08-06"
    url = f"/bao-cao/tong-hop/?nguon={mkt_ba_loai_tien.code}&{ky}"
    ctx, page = _mo(trinh_duyet_moi, live_server, manager, 2400, 800, url)
    try:
        _kiem_nen(page.evaluate(NEN_DONG_TONG), "sáng")
        # Bộ lọc rộng ra làm bảng hẹp lại, tiêu đề xuống nhiều dòng; rồi bấm Toàn màn hình: bộ lọc thu về thanh
        # dọc trong 0,2 s, bảng giãn ra mà cửa sổ không đổi cỡ — như video 30.09
        page.evaluate("()=>document.getElementById('report-view').style.setProperty('--w-panel','1100px')")
        page.wait_for_function("()=>Math.round(document.getElementById('report-filter-panel').getBoundingClientRect().width)===1100")
        cao_hep = page.evaluate(DO_BANG)[0]["tieu_de"]
        page.click("#report-toggle-focus")
        page.wait_for_function(FOCUS)
        page.wait_for_function("()=>Math.round(document.getElementById('report-filter-panel').getBoundingClientRect().width)===48")
        page.wait_for_timeout(150)   # vài khung hình để trình duyệt báo bảng đã đổi cỡ
        bangs = page.evaluate(DO_BANG)
        assert cao_hep - bangs[0]["tieu_de"] >= 5, \
            f"tiền đề: bảng giãn thì tiêu đề phải thấp đi — {cao_hep:.0f} → {bangs[0]['tieu_de']:.0f} px"
        assert len(bangs) == 7 and not _lech(bangs), f"dòng TỔNG CỘNG dính theo số đo cũ: {_lech(bangs)}"
        _kiem_dinh(page.evaluate(VI_TRI_DINH), "toàn màn hình")
        chup(page, "bao-cao-dong-tong-dinh-2400")
        page.evaluate("()=>{document.documentElement.dataset.theme='dark'}")
        _kiem_nen(page.evaluate(NEN_DONG_TONG), "tối")
        chup(page, "bao-cao-dong-tong-dinh-toi")
    finally:
        ctx.close()
    ctx, page = _mo(trinh_duyet_moi, live_server, manager, 390, 844, url)
    try:
        assert not page.evaluate("()=>document.documentElement.scrollWidth>document.documentElement.clientWidth")
        _kiem_nen(page.evaluate(NEN_DONG_TONG), "390 px")
        lech = _lech(page.evaluate(DO_BANG))
        assert not lech, f"390 px: dòng TỔNG CỘNG dính sai chỗ: {lech}"
        page.evaluate(TOI_KHUNG_BANG)
        _kiem_dinh(page.evaluate(VI_TRI_DINH), "390 px")
        chup(page, "bao-cao-dong-tong-dinh-390")
    finally:
        ctx.close()
    ctx, page = _mo(trinh_duyet_moi, live_server, manager, 1440, 900, f"/bang/{mkt_ba_loai_tien.code}/?{ky}")
    try:
        assert page.locator(".report-table").count() > 1, "tiền đề: Bảng dữ liệu hiện dạng báo cáo"
        _kiem_nen(page.evaluate(NEN_DONG_TONG), "Bảng dữ liệu")
        lech = _lech(page.evaluate(DO_BANG))
        assert not lech, f"Bảng dữ liệu: dòng TỔNG CỘNG dính sai chỗ: {lech}"
        page.evaluate(TOI_KHUNG_BANG)
        _kiem_dinh(page.evaluate(VI_TRI_DINH), "Bảng dữ liệu")
        chup(page, "bang-du-lieu-dong-tong-dinh")
    finally:
        ctx.close()


def test_chon_nhanh_ngay_dau_thang_chi_sang_mot_nut(live_server, trinh_duyet_moi, nguon, nguoi_dung, monkeypatch):
    """AC-22.22 — Ngày 01.10 bấm "Tháng này" (cùng khoảng 01/10 – 01/10 với "Hôm nay"): trang tải lại chỉ "Tháng
    này" sáng, URL mang `ky=thang-nay`; bấm "Hôm nay" thì chỉ "Hôm nay" sáng; sửa tay ô ngày thì ô ẩn `ky` trống;
    bộ lọc không còn ô Cách xem, Chế độ"""
    from datetime import date
    from django.utils import timezone

    localdate = timezone.localdate
    monkeypatch.setattr(timezone, "localdate",
                        lambda value=None, timezone=None: date(2026, 10, 1) if value is None else localdate(value, timezone))
    ctx, page = _mo(trinh_duyet_moi, live_server, nguoi_dung["manager_sale"], 1440, 900,
                    f"/bao-cao/tong-hop/?nguon={nguon.table.code}")
    sang = "()=>[...document.querySelectorAll('.report-preset.is-active')].map(b=>b.dataset.key)"
    try:
        assert page.locator("#nhom").count() == 0 and page.locator("#report-che-do").count() == 0
        with page.expect_navigation():
            page.click(".report-preset[data-key=thang-nay]")
        page.wait_for_load_state("networkidle")
        assert "ky=thang-nay" in page.url and page.evaluate(sang) == ["thang-nay"]
        with page.expect_navigation():
            page.click(".report-preset[data-key=hom-nay]")
        page.wait_for_load_state("networkidle")
        assert page.evaluate(sang) == ["hom-nay"]
        page.fill("#tu", "2026-09-15")
        assert page.input_value("#ky") == ""
    finally:
        ctx.close()


# ── Ba chỗ sửa Báo cáo tổng hợp (chủ dự án duyệt mockup 02.10.2026) ─────────────────────────────────────────────

#: Phần khung bảng lộ ra lúc mở trang: đáy phần nhìn thấy (cửa sổ, khung cuộn của trang, thanh menu dưới), đáy dòng
#: TỔNG CỘNG cuối của khối đầu, và số dòng số liệu của khối đầu nằm trọn trong phần nhìn thấy
LO_RA = """()=>{const k=document.querySelector('.report-table-scroll'),m=document.querySelector('main.noi-dung');
    const t=k.querySelector('.report-table'),dock=document.querySelector('.sp-dock');
    const day=Math.min(innerHeight,m.getBoundingClientRect().bottom,dock?dock.getBoundingClientRect().top:innerHeight);
    const tong=[...t.querySelectorAll('.report-total')];const cuoi=tong.length?tong[tong.length-1]:t.tHead;
    return {khung:Math.round(k.getBoundingClientRect().top),day:Math.round(day),so_tong:tong.length,
            tieu_de:Math.round(t.tHead.getBoundingClientRect().bottom),can:Math.round(cuoi.getBoundingClientRect().bottom),
            thay_tong:tong.filter(r=>r.getBoundingClientRect().bottom<=day).length,
            dong_so:[...t.querySelectorAll('tbody tr:not(.report-total)')].filter(r=>r.getBoundingClientRect().bottom<=day).length}}"""

#: Vùng đứng yên của khối đang xem — khối nằm ở giữa phần khung bảng đang thấy, cùng cách chọn với phần nhích cột
#: (mỗi khối là một bảng riêng nên cột lệch nhau) — và các ô tiêu đề số bị vắt qua mép của nó
VUNG_GHIM = """()=>{const k=document.querySelector('.report-table-scroll'),kb=k.getBoundingClientRect();
    const mb=document.querySelector('main.noi-dung').getBoundingClientRect();
    const giua=(Math.max(kb.top,mb.top,0)+Math.min(kb.bottom,mb.bottom,innerHeight))/2;
    const khois=[...k.querySelectorAll('.report-block')];
    const khoi=khois.find(b=>{const r=b.getBoundingClientRect();return r.top<=giua&&r.bottom>=giua})||khois[0];
    const ths=[...khoi.querySelector('.report-table').tHead.rows[0].cells];
    const yen=ths.filter(th=>th.classList.contains('report-identity')&&!th.classList.contains('report-troi'));
    const mep=Math.max(...yen.map(th=>th.getBoundingClientRect().right));
    const vat=ths.filter(th=>!th.classList.contains('report-identity')).filter(th=>{const r=th.getBoundingClientRect();
        return r.left<mep-1&&r.right>mep+1}).map(th=>th.textContent.trim());
    const vi_tri=Object.fromEntries(yen.map(th=>[th.textContent.trim(),Math.round(th.getBoundingClientRect().left-kb.left)]));
    const team=ths.find(th=>th.textContent.trim()==='Team');
    return {rong:Math.round(mep-kb.left),vat,vi_tri,cuon:k.scrollLeft,
            team_khuat:!team||team.getBoundingClientRect().right<=mep+1}}"""


def _cho_yen(page, ham="()=>document.querySelector('.report-table-scroll').scrollLeft"):
    """Chờ khung bảng cuộn xong, kể cả lần nhích mượt bắt đầu sau `scrollend`: giá trị `ham` đứng yên qua bốn lần
    đo liền nhau cách 150 ms (0,6 s), tối đa khoảng 9 s."""
    truoc, yen = None, 0
    for _ in range(60):
        page.wait_for_timeout(150)
        gia_tri = page.evaluate(ham)
        yen = yen + 1 if gia_tri == truoc else 0
        if yen >= 3:
            return gia_tri
        truoc = gia_tri
    return truoc


def test_mo_trang_da_thay_so(live_server, trinh_duyet_moi, mkt_ba_loai_tien, van_don, nguoi_dung):
    """AC-22.24 — Vừa mở Báo cáo tổng hợp đã thấy số (chủ dự án duyệt mockup 02.10.2026): ở laptop 1366×768, bộ lọc
    mở như mặc định, có cảnh báo dòng chưa có loại tiền, khung bảng lộ đủ tiêu đề khối, hàng tiêu đề cột và mọi
    dòng TỔNG CỘNG của khối đầu mà không phải cuộn; cảnh báo cao một dòng; nút Giải thích số liệu mở và đóng panel,
    Escape đóng panel và trả focus về nút; Toàn màn hình vẫn có hai nút; 390 px không tràn ngang"""
    from datetime import date

    _nop(mkt_ba_loai_tien, van_don["B"], 12, 0, cpqc="100", thi_truong="", tien="", ngay=date(2026, 8, 6))
    url = f"/bao-cao/tong-hop/?nguon={mkt_ba_loai_tien.code}&tu=2026-08-01&den=2026-08-06"
    ctx, page = _mo(trinh_duyet_moi, live_server, nguoi_dung["manager_mkt"], 1366, 768, url)
    try:
        assert page.evaluate(ST) == "open"
        lo = page.evaluate(LO_RA)
        chup(page, "bao-cao-mo-trang-1366")
        assert lo["so_tong"] == 4, f"tiền đề: bốn dòng TỔNG CỘNG (CAD, USD, PHP, Chưa rõ) — {lo}"
        # Trước khi sửa: khung bảng bắt đầu ở 583 px, chưa thấy trọn hàng tiêu đề cột. Sau: thấy hàng tiêu đề và các
        # dòng TỔNG CỘNG (số) ngay khi mở — đo tại máy 4/4 dòng; đặt mức ≥ 3 để phông chữ khác máy không làm đỏ oan
        assert lo["tieu_de"] <= lo["day"] and lo["thay_tong"] >= 3, f"mở trang chưa thấy số — {lo}"
        canh = page.evaluate("""()=>{const s=document.querySelector('.report-canh-gon>span');
            return {cao:s.getBoundingClientRect().height,dong:parseFloat(getComputedStyle(s).lineHeight)}}""")
        assert canh["cao"] <= canh["dong"] * 1.5, f"cảnh báo loại tiền dài hơn một dòng — {canh}"
        nut = page.locator("button[aria-controls=report-giai-thich]")
        panel = page.locator("#report-giai-thich")
        assert panel.is_hidden() and nut.get_attribute("aria-expanded") == "false"
        nut.click()
        assert panel.is_visible() and nut.get_attribute("aria-expanded") == "true"
        assert "(TT) = đối soát từ vận đơn" in panel.inner_text()
        chup(page, "bao-cao-giai-thich-mo")
        page.keyboard.press("Escape")
        assert panel.is_hidden() and nut.get_attribute("aria-expanded") == "false"
        assert page.evaluate("()=>document.activeElement.getAttribute('aria-controls')") == "report-giai-thich"
        nut.click()
        nut.click()
        assert panel.is_hidden(), "bấm lại nút thì đóng panel"
        page.click("#report-toggle-focus")
        page.wait_for_function(FOCUS)
        assert nut.is_visible() and page.locator("button[aria-controls=report-nguong]").is_visible(), \
            "Toàn màn hình vẫn có nút Giải thích số liệu và Ngưỡng màu"
        page.keyboard.press("Escape")
        page.wait_for_function(KHONG_FOCUS)
    finally:
        ctx.close()
    ctx, page = _mo(trinh_duyet_moi, live_server, nguoi_dung["manager_mkt"], 390, 844, url)
    try:
        assert not page.evaluate("()=>document.documentElement.scrollWidth>document.documentElement.clientWidth")
        chup(page, "bao-cao-mo-trang-390")
    finally:
        ctx.close()


def test_keo_ngang_khong_con_cot_bi_che(live_server, trinh_duyet_moi, mkt_ba_loai_tien, nguoi_dung, du_cot_dinh_danh):
    """AC-22.25 — Kéo ngang không còn cột số bị che (chủ dự án duyệt mockup 02.10.2026): ở 1366×768 vùng đứng yên chỉ
    STT · Nhân sự · Loại tiền (≤ 262 px); kéo ngang rồi dừng thì ba cột đó nằm đúng chỗ, Team đã trôi khuất và không
    ô tiêu đề số nào vắt qua mép vùng đứng yên (bảng tự nhích); bấm mũi tên phải trên bàn phím thì vẫn tiến tiếp; cuộn
    dọc thì mọi ô dòng TỔNG CỘNG, kể cả ô Team, vẫn dính dưới tiêu đề; Bảng dữ liệu dạng báo cáo cùng cách"""
    ky = "tu=2026-08-01&den=2026-08-06"
    for url, noi in ((f"/bao-cao/tong-hop/?nguon={mkt_ba_loai_tien.code}&{ky}", "Báo cáo tổng hợp"),
                     (f"/bang/{mkt_ba_loai_tien.code}/?{ky}", "Bảng dữ liệu")):
        ctx, page = _mo(trinh_duyet_moi, live_server, nguoi_dung["manager_mkt"], 1366, 768, url)
        try:
            page.evaluate(TOI_KHUNG_BANG)
            page.evaluate("()=>{document.querySelector('.report-table-scroll').scrollLeft=400}")
            _cho_yen(page)
            sau = page.evaluate(VUNG_GHIM)
            # STT 44 + Nhân sự 130 + Loại tiền 88 (chữ "Loại tiền" không xuống dòng) = 262 px, như mockup; trước đây 522–638
            assert sau["rong"] <= 262, f"{noi}: vùng đứng yên rộng {sau['rong']} px — {sau}"
            chup(page, f"keo-ngang-{'bang' if noi == 'Bảng dữ liệu' else 'bao-cao'}")
            assert sau["cuon"] > 0 and sau["vi_tri"] == {"STT": 0, "Nhân sự": 44, "Loại tiền": 174}, f"{noi}: {sau}"
            assert sau["team_khuat"], f"{noi}: Team còn đứng yên — {sau}"
            het = page.evaluate("()=>{const s=document.querySelector('.report-table-scroll');return s.scrollWidth-s.clientWidth}")
            assert sau["cuon"] >= het - 2 or not sau["vat"], f"{noi}: cột số bị vắt qua mép vùng đứng yên: {sau['vat']}"
            if noi == "Báo cáo tổng hợp":
                page.focus(".report-table-scroll")
                for _ in range(3):
                    truoc, het = page.evaluate("""()=>{const s=document.querySelector('.report-table-scroll');
                        return [s.scrollLeft, s.scrollWidth-s.clientWidth]}""")
                    if truoc >= het - 2:
                        break          # đã tới mép phải: không còn chỗ tiến
                    page.keyboard.press("ArrowRight")
                    sau_phim = _cho_yen(page)
                    assert sau_phim > truoc, f"mũi tên phải bị kéo lùi: {truoc} → {sau_phim} (mép {het})"
                    # Không cột số nào vắt qua mép vùng đứng yên — trừ khi đã tới mép phải: bảng không cuộn thêm được
                    # nữa, và nhích ngược về cột trước là giật bảng lùi (lỗi sửa 03.10.2026)
                    if sau_phim < het - 2:
                        assert not page.evaluate(VUNG_GHIM)["vat"]
                dinh = page.evaluate("""()=>new Promise(r=>{const s=document.querySelector('.report-table-scroll'),
                    t=s.querySelector('.report-table');s.scrollTop=t.offsetTop+60;requestAnimationFrame(()=>requestAnimationFrame(()=>{
                    const tr=t.querySelector('.report-total'),so=tr.querySelector('td:not(.report-identity)').getBoundingClientRect();
                    r([...tr.querySelectorAll('.report-troi')].map(o=>Math.round(o.getBoundingClientRect().top-so.top)))}))})""")
                assert dinh and all(d == 0 for d in dinh), f"ô trôi của dòng TỔNG CỘNG không dính cùng dòng: {dinh}"
        finally:
            ctx.close()


#: Ngày của dòng/khối đầu tiên nằm dưới phần dính (tiêu đề và dòng tổng) trong khung bảng
NGAY_DANG_XEM = """()=>{const k=document.querySelector('.report-table-scroll'),kb=k.getBoundingClientRect();
    const gop=!!k.querySelector('.report-block-submissions');
    if(!gop){const b=[...k.querySelectorAll('.report-block[data-ngay]')].find(x=>x.getBoundingClientRect().bottom>kb.top+80);
        return b?b.dataset.ngay:null}
    const t=k.querySelector('.report-block-submissions .report-table');
    const tong=[...t.querySelectorAll('.report-total')].map(tr=>tr.firstElementChild.getBoundingClientRect().bottom);
    const day_dinh=Math.max(t.tHead.rows[0].cells[0].getBoundingClientRect().bottom,...tong);
    const r=[...t.querySelectorAll('tbody tr[data-ngay]')].find(x=>x.getBoundingClientRect().top>=day_dinh-2);
    return r?r.dataset.ngay:null}"""


def test_gop_khong_tai_lai_trang(live_server, trinh_duyet_moi, mkt_ba_loai_tien, nguoi_dung):
    """AC-22.26 — Bấm Gộp / Không gộp không tải lại trang (chủ dự án duyệt mockup 02.10.2026): chỉ phần bảng đổi,
    địa chỉ trang đổi theo (`gop=1`), nút, chip Gộp và link Xuất Excel đổi theo, focus ở lại nút vừa bấm, dòng tổng
    vẫn dính đúng chỗ, bảng giữ đúng ngày đang xem; Back và tải lại ra đúng chế độ; máy chủ trả lỗi thì tải cả trang
    như cũ; ở Bảng dữ liệu bấm Gộp vẫn tải cả trang"""
    ky = "tu=2026-08-01&den=2026-08-06"
    url = f"/bao-cao/tong-hop/?nguon={mkt_ba_loai_tien.code}&{ky}"
    ctx, page = _mo(trinh_duyet_moi, live_server, nguoi_dung["manager_mkt"], 1366, 768, url)
    try:
        page.evaluate("()=>{window.__moc=1}")
        page.evaluate(TOI_KHUNG_BANG)
        page.evaluate("""()=>{const k=document.querySelector('.report-table-scroll');
            const b=k.querySelector('.report-block[data-ngay="2026-08-04"]');k.scrollTop+=b.getBoundingClientRect().top-k.getBoundingClientRect().top}""")
        assert page.evaluate(NGAY_DANG_XEM) == "2026-08-04"
        page.click(".report-seg a:text-is('Gộp')")
        page.wait_for_function("()=>location.search.includes('gop=1')&&!!document.querySelector('.report-block-submissions')")
        page.wait_for_function("()=>!document.querySelector('.report-table-scroll').hasAttribute('aria-busy')")
        assert page.evaluate("()=>window.__moc") == 1, "trang đã tải lại"
        assert page.evaluate(NGAY_DANG_XEM) == "2026-08-04", "Gộp xong không còn ở ngày đang xem"
        assert page.locator(".report-seg a:text-is('Gộp')").get_attribute("aria-pressed") == "true"
        assert page.locator(".report-seg a:text-is('Không gộp')").get_attribute("aria-pressed") == "false"
        assert "gop=1" in page.locator("#report-xuat").get_attribute("href")
        assert "Gộp" in page.locator("#report-chips").inner_text()
        assert page.evaluate("()=>document.activeElement.textContent.trim()") == "Gộp"
        assert not _lech(page.evaluate(DO_BANG)), "dòng TỔNG CỘNG của bảng mới dính sai chỗ"
        chup(page, "bao-cao-gop-khong-tai-lai")
        page.click(".report-seg a:text-is('Không gộp')")
        page.wait_for_function("()=>!location.search.includes('gop=1')&&!document.querySelector('.report-block-submissions')")
        page.wait_for_function("()=>!document.querySelector('.report-table-scroll').hasAttribute('aria-busy')")
        assert page.evaluate("()=>window.__moc") == 1 and page.evaluate(NGAY_DANG_XEM) == "2026-08-04"
        page.go_back()
        page.wait_for_function("()=>location.search.includes('gop=1')&&!!document.querySelector('.report-block-submissions')")
        assert page.evaluate("()=>window.__moc") == 1, "Back đã tải lại trang"
        page.reload(wait_until="networkidle")
        assert page.evaluate("()=>window.__moc") is None
        assert page.locator(".report-seg a:text-is('Gộp')").get_attribute("aria-pressed") == "true"
        # Máy chủ trả lỗi: tải cả trang như hôm nay, không để màn hình nửa vời
        page.route(lambda u: "gop=" not in u and "/bao-cao/tong-hop/?" in u,
                   lambda route: route.fulfill(status=500, body="loi may chu", content_type="text/plain"))
        page.evaluate("()=>{window.__moc=2}")
        with page.expect_navigation():
            page.click(".report-seg a:text-is('Không gộp')")
        assert "loi may chu" in page.content()
    finally:
        ctx.close()
    ctx, page = _mo(trinh_duyet_moi, live_server, nguoi_dung["manager_mkt"], 1366, 768,
                    f"/bang/{mkt_ba_loai_tien.code}/?{ky}")
    try:
        page.evaluate("()=>{window.__moc=1}")
        with page.expect_navigation():
            page.click(".report-seg a:text-is('Gộp')")
        page.wait_for_load_state("networkidle")
        assert page.evaluate("()=>window.__moc") is None and "gop=1" in page.url
    finally:
        ctx.close()


def test_bang_vua_man_hinh_va_bo_loc_cuon_rieng(live_server, trinh_duyet_moi, mkt_ba_loai_tien, nguoi_dung):
    """AC-42.15 — Chủ dự án 03.10.2026: Báo cáo tổng hợp không còn đầu trang "Báo cáo tổng hợp / Kết quả thực tế…"
    (tên trang ở thanh trên); khung bảng kéo dài tới sát đáy vùng nội dung (mép dưới và thanh kéo ngang luôn nhìn
    thấy, cách đáy ≤ 40 px); bộ lọc bên trái đứng yên, cao vừa vùng nội dung và cuộn riêng: lăn chuột trên bộ lọc chỉ
    cuộn bộ lọc, trang và bảng đứng yên; báo cáo MKT không có cột Lần nộp, Loại tiền"""
    url = f"/bao-cao/tong-hop/?nguon={mkt_ba_loai_tien.code}&tu=2026-08-01&den=2026-08-06"
    for w, h in ((1366, 768), (1366, 600)):
        ctx, page = _mo(trinh_duyet_moi, live_server, nguoi_dung["manager_mkt"], w, h, url)
        try:
            do = page.evaluate("""()=>{const m=document.querySelector('main.noi-dung'),mb=m.getBoundingClientRect(),
                k=document.querySelector('.report-table-scroll').getBoundingClientRect(),
                pb=document.querySelector('.report-filter-panel>.panel-body');
                return {h1:[...m.querySelectorAll('h1')].map(x=>x.textContent),
                    chu:m.textContent.includes('Kết quả thực tế trong phạm vi'),
                    tren:k.top-mb.top, khoang:Math.round(mb.bottom-k.bottom), cao:Math.round(k.height),
                    loc:[pb.scrollHeight,pb.clientHeight],
                    cot:[...document.querySelectorAll('.report-table thead th.report-identity')].map(t=>t.textContent.trim())}}""")
            assert do["h1"] == [] and not do["chu"], do
            assert "Lần nộp" not in do["cot"] and "Loại tiền" not in do["cot"], do
            if h == 768:
                # Khung đứng gần đầu vùng nội dung thì kéo tới sát đáy (đệm dưới của vùng nội dung 32 px)
                assert 0 <= do["khoang"] <= 40 and do["cao"] >= 300, do
            assert do["loc"][0] > do["loc"][1], f"bộ lọc phải có thanh cuộn riêng ở {w}×{h}: {do}"
            truoc = page.evaluate("()=>[document.querySelector('main.noi-dung').scrollTop,document.querySelector('.report-table-scroll').scrollTop]")
            hop = page.locator(".report-filter-panel>.panel-body").bounding_box()
            page.mouse.move(hop["x"] + hop["width"] / 2, hop["y"] + hop["height"] / 2)
            page.mouse.wheel(0, 300)
            page.wait_for_timeout(300)
            sau = page.evaluate("""()=>[document.querySelector('main.noi-dung').scrollTop,
                document.querySelector('.report-table-scroll').scrollTop,
                document.querySelector('.report-filter-panel>.panel-body').scrollTop]""")
            assert sau[:2] == truoc and sau[2] > 0, f"lăn trên bộ lọc: {truoc} → {sau}"
            chup(page, f"bang-vua-man-hinh-{h}")
        finally:
            ctx.close()
