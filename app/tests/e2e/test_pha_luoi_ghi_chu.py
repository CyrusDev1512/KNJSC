"""Lưới Vận đơn không vỡ khi ghi chú tự giãn dòng — `docs/04` AC-11.44.

Sinh ra từ đợt thử phá ngày 24.09.2026 theo yêu cầu chủ dự án "kiểm như một người
dùng thật các trường hợp dễ vỡ view, vỡ grid". Đợt đó bắt được một lỗi thật (ghi chú
chỉ gồm khoảng trắng làm dòng cao 197 px mà không hiện chữ nào) nên bộ bài được giữ
lại làm lưới bảo vệ.

Khác với `test_ghi_chu_tu_gian_dong.py` — tệp đó kiểm **đặc tả** của AC-11.44, tệp
này kiểm **lưới không vỡ** khi người dùng làm những việc dễ làm hỏng nó. Mỗi bài
làm một việc rồi soát hình học lưới. Soát gồm:

    1. Hai dòng liền nhau phải dính nhau — hở hay chồng lên nhau là vỡ lưới
    2. Mọi ô trong một dòng phải cao đúng bằng dòng, kể cả ô ghim bên trái
    3. Không còn ô `…` (lưới vẽ trước khi dữ liệu về)
    4. Ghi chú không bị cắt chữ, trừ ô đã chạm trần 2000 px
    5. Trang không tràn ngang
    6. Không có lỗi JavaScript nào

Mọi bài mang dấu `trinh_duyet` và `cham`, nên nằm trong lượt `pytest e2e (Chromium)`
của CI. Chạy tay (container `web` đang chạy, đã `playwright install chromium`):

    docker compose -f deploy/docker-compose.yml exec -T -e RUN_MIGRATIONS=0 \
        -e DJANGO_ALLOW_ASYNC_UNSAFE=true web \
        pytest tests/e2e/test_pha_luoi_ghi_chu.py -s -p no:cacheprovider

Thêm `-s` để xem số đo; không có `-s` thì pytest chỉ in khi bài đỏ — đúng thứ cần
lúc đó, vì phần chẩn đoán tự khai báo điểm bấm rơi trúng phần tử nào.
"""
import time

import pytest

from crm.tests.test_waybill_feedback import feedback  # noqa: F401  (fixture dùng lại)
from forms_builder.models import DataRecord

from .conftest import chup
from .ghi_chu_helpers import ghi_chu_nhin_thay

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]

ROW = 28
TRAN = 2000

DAI = ("Khách gọi lại lúc 14h30 nói địa chỉ cũ đã chuyển, nhà mới nằm trong hẻm nên xe "
       "tải lớn không vào được, đề nghị đổi sang xe nhỏ hoặc giao tại đầu hẻm rồi gọi "
       "người ra nhận, đã báo kế toán xác nhận trước khi xuất kho. ") * 2


# ══ Soát hình học lưới ══════════════════════════════════════════════

JS_SOAT = r"""() => {
  const lam_tron = n => Math.round(n);
  const dong = [...document.querySelectorAll('.mg-body > .mg-row')]
      .map(r => ({el: r, i: +r.getAttribute('aria-rowindex')}))
      .sort((a, b) => a.i - b.i);
  const loi = [];

  // 1. Hai dòng liền số thứ tự phải dính nhau
  for (let k = 0; k < dong.length - 1; k++) {
    if (dong[k + 1].i !== dong[k].i + 1) continue;
    const a = dong[k].el.getBoundingClientRect(), b = dong[k + 1].el.getBoundingClientRect();
    const lech = lam_tron(b.top - a.bottom);
    if (Math.abs(lech) > 1) loi.push(`dong ${dong[k].i}-${dong[k + 1].i} lech ${lech} px`);
  }

  // 2. Mọi ô cao bằng dòng chứa nó
  for (const {el, i} of dong) {
    const h = lam_tron(el.getBoundingClientRect().height);
    for (const o of el.querySelectorAll('.mg-cell, .mg-number')) {
      const oh = lam_tron(o.getBoundingClientRect().height);
      if (Math.abs(oh - h) > 1) loi.push(`dong ${i} o "${o.dataset.code || 'so'}" cao ${oh} != dong ${h}`);
    }
  }

  // 3. Ô còn dấu `…`
  const cham = [...document.querySelectorAll('.mg-body .mg-cell')].filter(o => o.textContent === '…').length;

  // 4. Ghi chú bị cắt chữ (bỏ qua ô đã chạm trần)
  const cat = [...document.querySelectorAll('.mg-cell[data-code="ghi_chu"]')]
      .filter(o => { const h = lam_tron(o.getBoundingClientRect().height);
                     return h < 2000 && o.scrollHeight > h + 1; })
      .map(o => `dong ${o.dataset.r}: chu cao ${o.scrollHeight} > o ${lam_tron(o.getBoundingClientRect().height)}`);

  const vp = document.getElementById('mg-viewport');
  return {loi: loi.slice(0, 10), so_loi: loi.length, cham,
          cat: cat.slice(0, 5), so_cat: cat.length,
          cao_canvas: document.getElementById('mg-canvas').offsetHeight,
          cuon_doc: vp.scrollHeight, so_dong_ve: dong.length,
          tran_trang: document.documentElement.scrollWidth > window.innerWidth};
}"""


def _soat(trang, nhan):
    """Soát lưới và in kết quả; trả về bản ghi để bài kiểm khẳng định."""
    kq = trang.evaluate(JS_SOAT)
    van_de = []
    if kq["so_loi"]:
        van_de.append(f"{kq['so_loi']} chỗ lệch hình học")
    if kq["so_cat"]:
        van_de.append(f"{kq['so_cat']} ô cắt chữ")
    if kq["cham"]:
        van_de.append(f"{kq['cham']} ô còn dấu `…`")
    if kq["tran_trang"]:
        van_de.append("trang tràn ngang")
    dau = "VỠ " if van_de else "ổn"
    print(f"    [{dau}] {nhan}: {kq['so_dong_ve']} dòng vẽ, khung cao {kq['cao_canvas']} px"
          + (" — " + ", ".join(van_de) if van_de else ""))
    for d in kq["loi"] + [f"cắt chữ: {c}" for c in kq["cat"]]:
        print(f"           · {d}")
    return kq


def _sach(kq, nhan):
    assert not kq["so_loi"], f"{nhan}: lưới vỡ hình học — {kq['loi']}"
    assert not kq["so_cat"], f"{nhan}: ghi chú bị cắt chữ — {kq['cat']}"
    assert not kq["cham"], f"{nhan}: còn {kq['cham']} ô dấu `…`"


# ══ Tiện ích chung ══════════════════════════════════════════════════

@pytest.fixture
def kn_crm(settings):
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.BANGTINH_URL = ""
    return settings


@pytest.fixture
def nap_dong(feedback, nguoi_dung):  # noqa: F811
    """Tạo thêm dòng vận đơn với ghi chú cho trước; trả danh sách bản ghi."""
    bang, _, dong = feedback
    cot = list(bang.columns.all())

    def _nap(ghi_chus, tien_to="PHA"):
        rows = []
        for i, g in enumerate(ghi_chus):
            r = DataRecord(table=bang, created_by=nguoi_dung["admin"],
                           data={**dong[0].data, "ma_don": f"{tien_to}-{i:04d}",
                                 "ten_khach": f"Khách {i}", "ghi_chu": g})
            r.sync_indexed_columns(cot)
            rows.append(r)
        DataRecord.objects.bulk_create(rows)
        return rows
    return _nap


def _mo(trang, live_server, dang_nhap, nguoi_dung, bang, them=""):
    loi_js = []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    trang.on("console", lambda m: loi_js.append("console.error: " + m.text) if m.type == "error" else None)
    dang_nhap(trang, nguoi_dung["admin"])
    trang.goto(f"{live_server.url}/bang-tinh/{bang.code}/?sap=ma_don{them}")
    trang.wait_for_selector(".mg-cell[data-id]", timeout=30_000)
    trang.evaluate("() => document.fonts.ready")
    trang.wait_for_timeout(600)
    return loi_js


def _cuon_toi_ghi_chu(trang):
    """Lưới chỉ vẽ cột trong tầm nhìn — cuộn ngang tới khi cột Ghi chú hiện ra."""
    return trang.evaluate(
        """async () => {
            const vp = document.getElementById('mg-viewport');
            const cho = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
            for (let x = 0; x <= vp.scrollWidth; x += 300) {
                vp.scrollLeft = x; await cho();
                if (document.querySelector(".mg-cell[data-code='ghi_chu']")) return vp.scrollLeft;
            }
            return -1;
        }"""
    )


def _o(trang, ma_don):
    """Số đo ô Ghi chú của dòng mang mã đơn này."""
    return trang.evaluate(
        """ma => {
            const oma = [...document.querySelectorAll(".mg-cell[data-code='ma_don']")]
                .find(e => e.textContent.trim() === ma);
            if (!oma) return null;
            const g = document.querySelector(`.mg-cell[data-code='ghi_chu'][data-r='${oma.dataset.r}']`);
            if (!g) return null;
            const h = g.getBoundingClientRect().height;
            return {r: oma.dataset.r, cao: Math.round(h), chu_cao: g.scrollHeight,
                    rong: Math.round(g.getBoundingClientRect().width),
                    xuong_dong: g.classList.contains('mg-wrap'), chu: g.textContent};
        }""", ma_don)


def _da_luu(trang):
    trang.wait_for_function(
        "() => document.getElementById('bt-trang-thai')?.textContent === 'Đã lưu'", timeout=40_000)


# ══ 1. Nội dung độc ═════════════════════════════════════════════════

DOC = [
    ("rỗng", ""),
    ("một dấu cách", " "),
    ("mười ký tự xuống dòng", "\n" * 10),
    ("một từ 3000 ký tự không dấu cách", "A" * 3000),
    ("emoji", "🚚📦✅" * 60),
    ("chữ Nhật", "配送先住所が変更されました。" * 20),
    ("khoảng trắng và tab đầu dòng", "   \t  Giao buổi tối\n\t\tGọi trước"),
    ("giống thẻ HTML", "<script>alert(1)</script><b>đậm</b>"),
    ("xuống dòng kiểu Windows", "Dòng 1\r\nDòng 2\r\nDòng 3"),
]


def test_noi_dung_doc(live_server, trang, dang_nhap, kn_crm, feedback, nguoi_dung, nap_dong):  # noqa: F811
    """AC-11.44 — Chín kiểu nội dung dễ làm vỡ ô: rỗng, chỉ khoảng trắng, toàn ký tự xuống
    dòng, một từ 3.000 ký tự không dấu cách, emoji, chữ Nhật, tab đầu dòng, chuỗi giống
    thẻ HTML, xuống dòng kiểu Windows — không ô nào vượt trần, ghi chú không có chữ nào
    để đọc thì giữ 28 px, và chuỗi giống HTML hiện thành chữ chứ không thành thẻ thật"""
    print("\n══ 1. NỘI DUNG ĐỘC ══")
    nap_dong([g for _, g in DOC])
    loi_js = _mo(trang, live_server, dang_nhap, nguoi_dung, feedback[0])
    assert _cuon_toi_ghi_chu(trang) >= 0, "không cuộn tới được cột Ghi chú"

    for i, (ten, goc) in enumerate(DOC):
        o = _o(trang, f"PHA-{i:04d}")
        if o is None:
            print(f"    [?] {ten}: không thấy dòng")
            continue
        print(f"    {ten}: ô cao {o['cao']} px, chữ cao {o['chu_cao']} px, xuống dòng {o['xuong_dong']}")
        assert o["cao"] <= TRAN, f"{ten}: vượt trần ({o['cao']} px)"
        if goc.strip() == "":
            assert o["cao"] == ROW, f"{ten}: ghi chú trắng mà dòng cao {o['cao']} px"

    # Thẻ HTML phải hiện thành chữ, không được thành thẻ thật
    con_the = trang.evaluate(
        "() => !!document.querySelector('.mg-body .mg-cell b, .mg-body .mg-cell script')")
    assert not con_the, "chuỗi giống HTML bị chèn thành thẻ thật trong ô — lỗ hổng hiển thị"
    print("    thẻ HTML: hiện thành chữ, không thành thẻ — đúng")

    _sach(_soat(trang, "sau khi vẽ nội dung độc"), "nội dung độc")
    assert not loi_js, loi_js


# ══ 2. Nhiều dòng cao liên tiếp ═════════════════════════════════════

def test_nhieu_dong_cao_lien_tiep(live_server, trang, dang_nhap, kn_crm, feedback, nguoi_dung, nap_dong):  # noqa: F811
    """AC-11.44 — 40 dòng liền nhau đều ghi chú rất dài: đi cuối bảng, về đầu bảng và 25 lần
    phím mũi tên đều không làm vỡ lưới, ô đang chọn luôn nằm trong khung nhìn"""
    print("\n══ 2. 40 DÒNG CAO LIỀN NHAU ══")
    nap_dong([DAI * 6 + f" số {i}" for i in range(40)])
    loi_js = _mo(trang, live_server, dang_nhap, nguoi_dung, feedback[0])
    _cuon_toi_ghi_chu(trang)
    kq = _soat(trang, "vừa mở")
    _sach(kq, "40 dòng cao")

    trang.click("#mg-viewport")
    for phim, nhan in (("Control+End", "Ctrl+End xuống cuối"), ("Control+Home", "Ctrl+Home về đầu")):
        t = time.time()
        trang.keyboard.press(phim)
        trang.wait_for_timeout(1200)
        print(f"    {nhan}: {int((time.time() - t) * 1000)} ms")
        _sach(_soat(trang, nhan), nhan)

    # Phím mũi tên đi qua vùng dòng cao: ô đang chọn phải luôn nằm trong khung nhìn
    ngoai_khung = trang.evaluate(
        """async () => {
            const vp = document.getElementById('mg-viewport');
            const cho = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
            document.querySelector('.mg-cell[data-r="0"][data-code="ten_khach"]').click();
            let xau = 0;
            for (let i = 0; i < 25; i++) {
                vp.dispatchEvent(new KeyboardEvent('keydown', {key: 'ArrowDown', bubbles: true}));
                await cho();
                const c = document.querySelector('.mg-current');
                if (!c) { xau++; continue; }
                const r = c.getBoundingClientRect(), v = vp.getBoundingClientRect();
                if (r.bottom < v.top + 54 || r.top > v.bottom) xau++;
            }
            return xau;
        }"""
    )
    print(f"    25 lần mũi tên xuống: {ngoai_khung} lần ô chọn nằm ngoài khung nhìn")
    assert ngoai_khung == 0, "phím mũi tên qua dòng cao làm ô đang chọn ra khỏi khung nhìn"
    _sach(_soat(trang, "sau 25 lần mũi tên"), "mũi tên")
    assert not loi_js, loi_js


# ══ 3. Cuộn nhanh ═══════════════════════════════════════════════════

def test_cuon_nhanh_qua_vung_dong_cao(live_server, trang, dang_nhap, kn_crm, feedback, nguoi_dung, nap_dong):  # noqa: F811
    """AC-11.44 — 12 lượt cuộn giật cục qua 150 dòng cao thấp xen kẽ: không dòng nào hở hay
    chồng lên nhau, không ô nào còn dấu `…`"""
    print("\n══ 3. CUỘN NHANH ══")
    nap_dong([(DAI * 4 if i % 3 else "") + f" {i}" for i in range(150)])
    loi_js = _mo(trang, live_server, dang_nhap, nguoi_dung, feedback[0])
    _cuon_toi_ghi_chu(trang)

    xau = 0
    for lan in range(12):
        trang.evaluate(
            """i => { const vp = document.getElementById('mg-viewport');
                      vp.scrollTop = (i % 2) ? vp.scrollHeight * 0.85 : vp.scrollHeight * 0.05; }""", lan)
        trang.wait_for_timeout(450)
        kq = _soat(trang, f"lượt cuộn {lan + 1}")
        if kq["so_loi"] or kq["so_cat"] or kq["cham"]:
            xau += 1
    print(f"    {xau}/12 lượt có vấn đề")
    assert xau == 0, "cuộn nhanh qua vùng dòng cao làm lưới vỡ hoặc để lại ô `…`"
    assert not loi_js, loi_js


# ══ 4. Thu và nới cột Ghi chú ═══════════════════════════════════════

def test_thu_va_noi_cot_ghi_chu(live_server, trang, dang_nhap, kn_crm, feedback, nguoi_dung, nap_dong):  # noqa: F811
    """AC-11.44 — Kéo cột Ghi chú về hẹp nhất rồi nới rộng nhất: chiều cao dòng đo lại theo
    cả hai chiều ngay khi thả chuột, không phải tải lại trang"""
    print("\n══ 4. KÉO ĐỔI RỘNG CỘT ══")
    nap_dong([DAI] * 6)
    loi_js = _mo(trang, live_server, dang_nhap, nguoi_dung, feedback[0])
    _cuon_toi_ghi_chu(trang)
    dau = _o(trang, "PHA-0000")
    print(f"    ban đầu: cột {dau['rong']} px, dòng {dau['cao']} px")

    def keo(dx):
        # Tay kéo nằm ở **mép phải** đầu cột. Cuộn tới khi thấy ô Ghi chú thì mới thấy
        # mép TRÁI của cột — mép phải còn nằm ngoài khung. Phải đẩy thêm cho cả đầu cột
        # lọt vào, nếu không chuột bấm ra chỗ trống và lượt kéo không ăn.
        trang.evaluate(
            """async () => {
                const vp = document.getElementById('mg-viewport');
                const cho = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
                for (let i = 0; i < 4; i++) {
                    const d = document.querySelector('.mg-heading[data-code="ghi_chu"]');
                    if (!d) return;
                    const b = d.getBoundingClientRect();
                    // Vùng cột ghim (z-index 10) đè lên mọi thứ cuộn qua dưới nó, kể cả tay
                    // kéo. Phải đẩy mép phải đầu cột ra **ngoài** dải ghim mới bấm trúng —
                    // đúng như người dùng phải làm. Chừa 120 px cho chắc.
                    const ghim = document.querySelector('.mg-head > .mg-pin-region');
                    const muon = (ghim ? ghim.getBoundingClientRect().right : 46) + 120;
                    const lech = b.right - muon;
                    if (Math.abs(lech) < 8) break;
                    vp.scrollLeft += lech; await cho();
                }
            }"""
        )
        trang.wait_for_timeout(300)
        h = trang.locator('[data-resize="ghi_chu"]').bounding_box()
        khung = trang.evaluate("() => ({w: innerWidth, h: innerHeight})")
        assert h["x"] + h["width"] <= khung["w"], (
            f"tay kéo nằm ngoài khung nhìn (x={h['x']}, khung rộng {khung['w']}) — không bấm trúng được")
        # Đầu cột có ba thứ đè lên nhau: nút chữ cái trải hết bề ngang ở 25 px trên cùng,
        # nút lọc ▾ dán mép dưới, tay kéo rộng 8 px ở mép phải. Trình duyệt tự dò và tự khai
        # báo: hộp của tay kéo, mỗi điểm chạm phần tử nào, và **cả chồng** phần tử ở giữa
        # mép phải — `elementsFromPoint` cho biết tay kéo có trong chồng không và bị ai đè.
        do = trang.evaluate(
            """() => {
                const tay = document.querySelector('[data-resize="ghi_chu"]');
                if (!tay) return {loi: 'không có tay kéo trong DOM'};
                const b = tay.getBoundingClientRect(), dem = {};
                let diem = null;
                for (let dy = 1; dy < b.height - 1; dy += 2) {
                    for (const dx of [b.width - 1, b.width - 3, b.width - 5]) {
                        const x = b.left + dx, y = b.top + dy, e = document.elementFromPoint(x, y);
                        const ten = e ? `${e.tagName}.${e.className}` : 'trống';
                        dem[ten] = (dem[ten] || 0) + 1;
                        if (!diem && e === tay) diem = {x, y};
                    }
                }
                const giua = document.elementsFromPoint(b.right - 2, b.top + b.height / 2)
                    .slice(0, 6).map(e => `${e.tagName}.${e.className}`);
                return {diem, dem, giua,
                        hop: {trai: Math.round(b.left), tren: Math.round(b.top),
                              rong: Math.round(b.width), cao: Math.round(b.height)}};
            }"""
        )
        print(f"       tay kéo: hộp {do.get('hop')} | các điểm chạm: {do.get('dem')}")
        print(f"       chồng phần tử ở giữa mép phải: {do.get('giua')}")
        assert do.get("diem"), f"không điểm nào chạm được tay kéo — {do}"
        x, y, tren = do["diem"]["x"], do["diem"]["y"], "tay kéo cột ghi_chu"
        trang.mouse.move(x, y)
        trang.mouse.down()
        trang.mouse.move(x + dx, y, steps=8)
        trang.mouse.up()
        trang.wait_for_timeout(700)
        nho = trang.evaluate(
            """() => { const c = JSON.parse(document.getElementById('mg-config').textContent);
                 const p = JSON.parse(localStorage.getItem(`kn-master:${c.user}:${c.table}`) || '{}');
                 return (p.widths || {}).ghi_chu ?? null; }""")
        print(f"       kéo {dx:+} px từ ({int(x)},{int(y)}) trên {tren} → rộng đã nhớ: {nho}")

    keo(-400)                                   # thu hết cỡ (lưới kẹp ở 72 px)
    hep = _o(trang, "PHA-0000")
    print(f"    sau khi thu:  cột {hep['rong']} px, dòng {hep['cao']} px")
    assert hep["rong"] < dau["rong"], "kéo thu không ăn"
    assert hep["cao"] > dau["cao"], "cột hẹp lại mà dòng không cao thêm — chưa đo lại"
    _sach(_soat(trang, "cột hẹp nhất"), "cột hẹp")

    keo(600)                                    # nới hết cỡ (lưới kẹp ở 640 px)
    rong = _o(trang, "PHA-0000")
    print(f"    sau khi nới:  cột {rong['rong']} px, dòng {rong['cao']} px")
    assert rong["cao"] < hep["cao"], "cột rộng ra mà dòng không thấp lại — chưa đo lại"
    _sach(_soat(trang, "cột rộng nhất"), "cột rộng")
    assert not loi_js, loi_js


# ══ 5. Ẩn rồi hiện lại cột Ghi chú ══════════════════════════════════

def test_an_va_hien_lai_cot_ghi_chu(live_server, trang, dang_nhap, kn_crm, feedback, nguoi_dung, nap_dong):  # noqa: F811
    """AC-11.44 — Bỏ tích cột Ghi chú trong hộp Cột: mọi dòng co về 28 px; tích lại thì cao
    lên lại theo nội dung"""
    print("\n══ 5. ẨN / HIỆN CỘT ══")
    nap_dong([DAI] * 5)
    loi_js = _mo(trang, live_server, dang_nhap, nguoi_dung, feedback[0])
    _cuon_toi_ghi_chu(trang)
    print(f"    trước khi ẩn: dòng {_o(trang, 'PHA-0000')['cao']} px")

    def bam_tich():
        trang.click("#mg-columns-button")
        trang.wait_for_timeout(300)
        trang.evaluate(
            """() => {
                const d = [...document.querySelectorAll('#mg-column-list .mg-column-option')]
                    .find(e => e.textContent.trim().startsWith('Ghi chú'));
                d.querySelector('input[type=checkbox]').click();
            }"""
        )
        trang.wait_for_timeout(700)
        trang.keyboard.press("Escape")
        trang.wait_for_timeout(400)

    bam_tich()
    cao_khi_an = trang.evaluate(
        "() => Math.max(...[...document.querySelectorAll('.mg-body > .mg-row')]"
        ".map(r => Math.round(r.getBoundingClientRect().height)))")
    print(f"    khi ẩn cột:   dòng cao nhất {cao_khi_an} px")
    assert cao_khi_an == ROW, "ẩn cột Ghi chú rồi mà dòng vẫn cao — chiều cao không được tính lại"
    _sach(_soat(trang, "khi ẩn cột"), "ẩn cột")

    bam_tich()
    _cuon_toi_ghi_chu(trang)
    lai = _o(trang, "PHA-0000")
    print(f"    hiện lại:     dòng {lai['cao'] if lai else '?'} px")
    assert lai and lai["cao"] > ROW, "hiện lại cột mà dòng không cao lên"
    _sach(_soat(trang, "sau khi hiện lại"), "hiện lại cột")
    assert not loi_js, loi_js


# ══ 6. Xoá và hoàn tác ══════════════════════════════════════════════

def test_xoa_roi_hoan_tac_ghi_chu(live_server, trang, dang_nhap, kn_crm, feedback, nguoi_dung, nap_dong):  # noqa: F811
    """AC-11.44 — Xoá ghi chú bằng Delete rồi hoàn tác bằng Ctrl+Z: dòng co về 28 px rồi cao
    lại ngay, không phải tải lại trang"""
    print("\n══ 6. XOÁ VÀ HOÀN TÁC ══")
    nap_dong([DAI] * 3)
    loi_js = _mo(trang, live_server, dang_nhap, nguoi_dung, feedback[0])
    _cuon_toi_ghi_chu(trang)
    truoc = _o(trang, "PHA-0000")
    print(f"    trước:     {truoc['cao']} px")

    trang.click(f".mg-cell[data-code='ghi_chu'][data-r='{truoc['r']}']")
    trang.keyboard.press("Delete")
    trang.wait_for_timeout(900)
    sau_xoa = _o(trang, "PHA-0000")
    print(f"    sau Delete: {sau_xoa['cao']} px")
    assert sau_xoa["cao"] == ROW, "xoá hết ghi chú mà dòng vẫn cao"
    _sach(_soat(trang, "sau khi xoá"), "xoá")

    trang.keyboard.press("Control+z")
    trang.wait_for_timeout(900)
    sau_hoan = _o(trang, "PHA-0000")
    print(f"    sau Ctrl+Z: {sau_hoan['cao']} px")
    assert sau_hoan["cao"] > ROW, "hoàn tác trả lại ghi chú dài mà dòng không cao lại"
    _sach(_soat(trang, "sau khi hoàn tác"), "hoàn tác")
    _da_luu(trang)
    assert not loi_js, loi_js


# ══ 7. Dán nhiều dòng từ Excel ══════════════════════════════════════

def test_dan_nhieu_dong_tu_excel(live_server, trang, dang_nhap, kn_crm, feedback, nguoi_dung, nap_dong):  # noqa: F811
    """AC-11.44 — Dán hai ô từ Excel, ô đầu có ký tự xuống dòng bên trong: cả hai dòng giãn
    theo ngay và giữ nguyên ngắt dòng"""
    print("\n══ 7. DÁN TỪ EXCEL ══")
    nap_dong(["", ""])
    loi_js = _mo(trang, live_server, dang_nhap, nguoi_dung, feedback[0])
    _cuon_toi_ghi_chu(trang)
    o0 = _o(trang, "PHA-0000")
    trang.click(f".mg-cell[data-code='ghi_chu'][data-r='{o0['r']}']")
    trang.wait_for_timeout(300)

    tsv = '"Giao buổi sáng\nGọi trước 30 phút\nKhách hay vắng"\n' + DAI
    trang.evaluate(
        """t => { const dt = new DataTransfer(); dt.setData('text/plain', t);
                  document.getElementById('mg-viewport').dispatchEvent(
                      new ClipboardEvent('paste', {bubbles: true, clipboardData: dt})); }""", tsv)
    trang.wait_for_timeout(1500)

    a, b = _o(trang, "PHA-0000"), _o(trang, "PHA-0001")
    print(f"    dòng 1 (có xuống dòng bên trong): {a['cao']} px, xuống dòng {a['xuong_dong']}")
    print(f"    dòng 2 (một đoạn dài):            {b['cao']} px, xuống dòng {b['xuong_dong']}")
    assert a["cao"] > ROW and "\n" in a["chu"], "dán ô nhiều dòng: dòng không giãn hoặc mất ngắt dòng"
    assert b["cao"] > ROW, "dán đoạn dài: dòng không giãn"
    _sach(_soat(trang, "sau khi dán"), "dán")
    _da_luu(trang)
    assert not loi_js, loi_js


# ══ 8. Màn hình điện thoại ══════════════════════════════════════════

def test_dien_thoai_390(live_server, trang_dien_thoai, dang_nhap, kn_crm, feedback, nguoi_dung, nap_dong):  # noqa: F811
    """AC-11.44 — Màn hình cỡ điện thoại 390 px trong khi cột Ghi chú rộng 400 px: lưới cuộn
    trong khung của nó, trang không tràn ngang"""
    print("\n══ 8. ĐIỆN THOẠI 390 px ══")
    dong = nap_dong([DAI] * 5)
    loi_js = _mo(trang_dien_thoai, live_server, dang_nhap, nguoi_dung, feedback[0])
    o = ghi_chu_nhin_thay(trang_dien_thoai, dong[0].pk, DAI)
    assert o["xuong_dong"] and o["cao_o"] > ROW, o
    assert o["chu"] == DAI and o["cao_chu"] <= o["cao_o"] + 1, o
    print(f"    cột {o['rong_o']} px trên màn hình 390 px, dòng {o['cao_o']} px")
    kq = _soat(trang_dien_thoai, "điện thoại")
    chup(trang_dien_thoai, "pha-ghi-chu-dien-thoai")
    assert not kq["tran_trang"], "trang tràn ngang trên điện thoại"
    _sach(kq, "điện thoại")
    assert not loi_js, loi_js


# ══ 9. Phóng to trình duyệt ═════════════════════════════════════════

def test_phong_to_125(live_server, trang, dang_nhap, kn_crm, feedback, nguoi_dung, nap_dong):  # noqa: F811
    """AC-11.44 — Phóng trình duyệt lên 125 % rồi thu về: chiều cao dòng tính bằng px CSS nên
    không lệch, thu về đúng số cũ"""
    print("\n══ 9. PHÓNG TO 125 % ══")
    nap_dong([DAI] * 6)
    loi_js = _mo(trang, live_server, dang_nhap, nguoi_dung, feedback[0])
    _cuon_toi_ghi_chu(trang)
    thuong = _o(trang, "PHA-0000")["cao"]
    trang.evaluate("() => document.documentElement.style.zoom = '1.25'")
    trang.wait_for_timeout(900)
    kq = _soat(trang, "zoom 125%")
    chup(trang, "pha-ghi-chu-zoom125")
    trang.evaluate("() => document.documentElement.style.zoom = ''")
    trang.wait_for_timeout(600)
    ve = _o(trang, "PHA-0000")["cao"]
    print(f"    100%: {thuong} px → zoom 125% → về 100%: {ve} px")
    assert abs(ve - thuong) <= 2, "chiều cao dòng đổi sau khi phóng to rồi thu về"
    _sach(kq, "zoom")
    _sach(_soat(trang, "sau khi thu về 100%"), "sau zoom")
    assert not loi_js, loi_js
