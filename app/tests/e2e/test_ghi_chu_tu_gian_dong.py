"""Dòng lưới tự giãn cao vừa ghi chú, xuống dòng và ngắt dòng đúng — `docs/04` AC-11.44.

Ghi chú dài bị cắt một dòng, phải bấm mở hộp đọc mới xem hết. Bộ phận Vận đơn báo
bất tiện (23.09.2026). Cột rộng ra và cờ `auto_height` (vế máy chủ) kiểm ở
`crm/tests/test_ghi_chu_tu_gian_dong.py`; bài này kiểm vế trình duyệt: **chiều cao
dòng tính theo nội dung thật**, kể cả ký tự xuống dòng người dùng gõ.

Phải đi qua trình duyệt thật vì chiều cao do trình duyệt ngắt dòng mà ra — không
bài kiểm mức đơn vị nào tính thay được, và tự đếm ký tự thì sai với tiếng Việt có
dấu cùng quy tắc `overflow-wrap:anywhere` của ô lưới.

Các trường hợp, đúng đặc tả đã chốt:

    ghi chú rỗng           → 28 px, y như cũ
    ghi chú ngắn một dòng  → 28 px, vì vừa một dòng chữ
    ghi chú ngắn có `\\n`   → giãn ra, hiện đúng hai dòng — ngắt dòng không bị dồn
    ghi chú dài            → cao hơn 28, dưới trần 2000, và **không cắt chữ**
    sửa ngay trong ô       → dòng giãn ngay, không tải lại trang; ô nhập cao theo chữ đang gõ
    kéo tay về 28          → thắng chiều cao tự tính và được nhớ; Home về tự động
    quá trần               → cắt ở 2000 px, bấm ô mở hộp đọc
    1000 dòng ghi chú dài  → đo thời gian tính chiều cao mỗi khối, ghi vào biên bản
"""
import pytest

from crm.tests.test_waybill_feedback import feedback  # noqa: F401  (fixture dùng lại)
from forms_builder.models import DataRecord

from .conftest import chup

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]

#: Chiều cao dòng mặc định của lưới (`ROW` trong master-grid.js)
CAO_MAC_DINH = 28
#: Trần chiều cao một dòng — chốt 23.09.2026, ghi chú dài hơn thì đọc bằng hộp đọc
TRAN = 2000

GHI_CHU_NGAN = "Khách hẹn giao buổi chiều."
#: 13 ký tự — ngắn, nhưng người gõ đã ngắt dòng; phải hiện đúng hai dòng
GHI_CHU_HAI_DONG = "Dòng 1\nDòng 2"
#: 427 ký tự, một đoạn liền
GHI_CHU_DAI = (
    "Khách gọi lại lúc 14h30 nói địa chỉ cũ đã chuyển, nhà mới nằm trong hẻm nên xe "
    "tải lớn không vào được, đề nghị đổi sang xe nhỏ hoặc giao tại đầu hẻm rồi gọi "
    "người ra nhận. Khách cũng hỏi đổi phương thức thanh toán từ chuyển khoản sang "
    "tiền mặt khi nhận hàng, đã báo bộ phận kế toán xác nhận lại trước khi xuất kho. "
    "Ngoài ra khách nhắc đơn trước bị giao thiếu một hộp, đã kiểm lại phiếu và xác "
    "nhận giao đủ, khách đồng ý bỏ qua."
)
#: 12.600 ký tự — cao hơn trần 2000 px ở mọi cỡ chữ
GHI_CHU_QUA_TRAN = "Nội dung rất dài. " * 700
#: 400 ký tự cho bài đo hiệu năng; mỗi dòng nối thêm số thứ tự để không trùng nhau
GHI_CHU_400 = ("Khách hẹn giao chiều, gọi trước khi tới; địa chỉ trong hẻm nhỏ, xe lớn "
               "không vào được, giao ở đầu hẻm rồi gọi người ra nhận. " * 4)[:400]

#: Ngưỡng đỏ cho một lượt đo chiều cao cả khối 100 dòng (p95); mục tiêu báo cáo 16 ms
NGUONG_DO_MOT_KHOI_MS = 100


@pytest.fixture
def kn_crm(settings):
    """Lưới nằm trọn trong dịch vụ KN CRM cổng 8021 — ADR-012."""
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.BANGTINH_URL = ""
    return settings


def _cho_luoi_co_du_lieu(trang):
    """Lưới vẽ ô rỗng `…` trước, JSON về sau — chờ đúng lúc ô đã có dữ liệu."""
    trang.wait_for_selector(".mg-cell", timeout=30_000)
    trang.wait_for_function(
        "() => [...document.querySelectorAll('.mg-cell')].some(e => e.textContent && e.textContent !== '…')",
        timeout=30_000,
    )


def _mo_luoi(trang, live_server, dang_nhap, nguoi_dung, bang, truy_van=""):
    """Đăng nhập Vận đơn, mở lưới, đợi dữ liệu và phông chữ — phần mở đầu chung của mọi bài."""
    loi_js = []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(trang, nguoi_dung["staff_vd"])
    trang.goto(f"{live_server.url}/bang-tinh/{bang.code}/{truy_van}")
    _cho_luoi_co_du_lieu(trang)
    # Chiều cao đo sau khi phông chữ sẵn sàng, nếu không số đo lệch
    trang.evaluate("() => document.fonts.ready")
    trang.wait_for_timeout(500)
    return loi_js


def _o_ghi_chu(trang, ma_don):
    """Ô Ghi chú của đúng dòng mang mã đơn này, kèm chiều cao ô, chiều cao chữ và số dòng chữ.

    Lưới chỉ vẽ cột đang trong tầm nhìn, mà Ghi chú nằm mãi bên phải — phải cuộn
    ngang tới nơi rồi mới đo được. Mã đơn là cột ghim nên luôn có mặt để dò số dòng.
    Số dòng chữ suy từ `scrollHeight` (đã trừ padding 4+4) chia cho `line-height`
    của chính ô.
    """
    return trang.evaluate(
        """async (ma) => {
            const vp = document.getElementById('mg-viewport');
            const doi_ve = () => new Promise(r => requestAnimationFrame(
                () => requestAnimationFrame(r)));
            const o_ma = [...document.querySelectorAll(".mg-cell[data-code='ma_don']")]
                .find(e => e.textContent.trim() === ma);
            if (!o_ma) return {loi: 'không thấy dòng mã ' + ma};
            const r = o_ma.dataset.r;
            for (let x = 0; x <= vp.scrollWidth; x += 300) {
                vp.scrollLeft = x;
                await doi_ve();
                const ghi = document.querySelector(
                    ".mg-cell[data-code='ghi_chu'][data-r='" + r + "']");
                if (ghi) {
                    const cao_dong_chu = parseFloat(getComputedStyle(ghi).lineHeight);
                    return {r, id: ghi.dataset.id,
                            cao_o: Math.round(ghi.getBoundingClientRect().height),
                            cao_chu: ghi.scrollHeight,
                            cao_dong_chu,
                            so_dong: Math.round((ghi.scrollHeight - 8) / cao_dong_chu),
                            rong_o: Math.round(ghi.getBoundingClientRect().width),
                            chu: ghi.textContent.trim(),
                            xuong_dong: ghi.classList.contains('mg-wrap')};
                }
            }
            return {loi: 'cuộn hết bảng vẫn không thấy ô ghi_chu của dòng ' + r};
        }""",
        ma_don,
    )


def _cho_da_luu(trang):
    """Lưới tự lưu sau 500 ms–2 s; chờ tới khi thanh trạng thái báo đã lưu."""
    trang.wait_for_function(
        "() => document.getElementById('bt-trang-thai')?.textContent === 'Đã lưu'", timeout=40_000)


def _chieu_cao_da_nho(trang):
    """Chiều cao dòng lưới đang nhớ trong trình duyệt (`kn-master:<user>:<bảng>`)."""
    return trang.evaluate(
        """() => {
            const c = JSON.parse(document.getElementById('mg-config').textContent);
            const p = JSON.parse(localStorage.getItem(`kn-master:${c.user}:${c.table}`) || '{}');
            return p.rowHeights || {};
        }"""
    )


def _ghi(dong, ghi_chu):
    dong.data["ghi_chu"] = ghi_chu
    dong.save(update_fields=["data"])
    return dong.data["ma_don"]


# ── Chiều cao theo nội dung ──────────────────────────────────────────────────

def test_dong_tu_gian_cao_vua_ghi_chu(live_server, trang, dang_nhap,
                                      kn_crm, feedback, nguoi_dung):  # noqa: F811
    """AC-11.44 — Dòng lưới cao vừa ghi chú: rỗng và ngắn giữ 28 px, dài thì giãn ra
    dưới trần 2000 px và hiện hết chữ, không phải bấm hộp đọc"""
    bang, _, dong = feedback
    assert len(dong) >= 2, "fixture feedback phải có ít nhất hai dòng"
    ma_ngan, ma_dai = _ghi(dong[0], GHI_CHU_NGAN), _ghi(dong[1], GHI_CHU_DAI)

    loi_js = _mo_luoi(trang, live_server, dang_nhap, nguoi_dung, bang)
    ngan, dai = _o_ghi_chu(trang, ma_ngan), _o_ghi_chu(trang, ma_dai)
    assert ngan and "loi" not in ngan, ngan
    assert dai and "loi" not in dai, dai

    # ── Ghi chú ngắn: vừa một dòng chữ, giữ nguyên chiều cao cũ ─────────────
    assert ngan["cao_o"] == CAO_MAC_DINH, ngan

    # ── Ghi chú dài: giãn ra, dưới trần, và không cắt chữ ──────────────────
    assert CAO_MAC_DINH < dai["cao_o"] <= TRAN, dai
    assert dai["xuong_dong"], "ô ghi chú dài phải mang lớp mg-wrap để chữ xuống dòng"
    # scrollHeight lớn hơn chiều cao ô nghĩa là còn chữ bị giấu — đúng lỗi cần sửa
    assert dai["cao_chu"] <= dai["cao_o"] + 1, (
        f"chữ còn bị cắt: nội dung cao {dai['cao_chu']} px trong ô {dai['cao_o']} px"
    )
    assert not loi_js, loi_js
    print(f"\nAC-11.44 đo được — ngắn: {ngan}\n                  dài : {dai}")


def test_ghi_chu_ngan_co_xuong_dong_van_gian(live_server, trang, dang_nhap,
                                             kn_crm, feedback, nguoi_dung):  # noqa: F811
    """AC-11.44 — Ghi chú ngắn nhưng có ký tự xuống dòng: dòng giãn ra và hiện đúng hai
    dòng chữ, không bị dồn thành một dòng"""
    bang, _, dong = feedback
    ma = _ghi(dong[0], GHI_CHU_HAI_DONG)

    loi_js = _mo_luoi(trang, live_server, dang_nhap, nguoi_dung, bang)
    o = _o_ghi_chu(trang, ma)
    assert o and "loi" not in o, o
    assert o["cao_o"] > CAO_MAC_DINH, o
    assert o["xuong_dong"], "ô phải mang lớp mg-wrap để `\\n` thành dòng riêng"
    assert o["so_dong"] == 2, o
    assert o["cao_chu"] <= o["cao_o"] + 1, o
    assert not loi_js, loi_js
    print(f"\nAC-11.44 hai dòng: {o}")


def test_sua_ghi_chu_trong_o_thi_dong_gian_ngay_khong_tai_lai(live_server, trang, dang_nhap,
                                                              kn_crm, feedback, nguoi_dung):  # noqa: F811
    """AC-11.44 — Gõ ghi chú hai dòng ngay trong ô (Enter xuống dòng, Ctrl+Enter xong):
    ô nhập cao theo chữ đang gõ, dòng giãn ngay khi đóng ô — chưa tải lại trang —
    ghi chú lưu về máy chủ giữ nguyên ký tự xuống dòng, tải lại vẫn cao"""
    bang, _, dong = feedback
    ma = _ghi(dong[0], "")
    dong_1, dong_2 = "Khách đổi địa chỉ, gọi trước khi giao", "Thanh toán tiền mặt khi nhận"

    loi_js = _mo_luoi(trang, live_server, dang_nhap, nguoi_dung, bang)
    truoc = _o_ghi_chu(trang, ma)
    assert truoc and "loi" not in truoc and truoc["cao_o"] == CAO_MAC_DINH, truoc

    trang.click(f".mg-cell[data-code='ghi_chu'][data-r='{truoc['r']}']")
    trang.keyboard.press("F2")
    trang.wait_for_selector("#mg-editor textarea", state="visible")
    trang.keyboard.press("Control+a")
    trang.keyboard.type(dong_1)
    trang.keyboard.press("Enter")
    trang.keyboard.type(dong_2)
    assert "\n" in trang.evaluate("() => document.querySelector('#mg-editor textarea').value")
    # Ô nhập phải cao lên theo chữ đang gõ, không kẹt ở 28 px chỉ thấy một dòng
    cao_khung = trang.evaluate("() => document.getElementById('mg-editor').getBoundingClientRect().height")
    assert cao_khung > CAO_MAC_DINH, f"ô nhập vẫn {cao_khung} px khi đã gõ hai dòng"

    trang.keyboard.press("Control+Enter")
    sau = _o_ghi_chu(trang, ma)
    assert sau and "loi" not in sau, sau
    assert sau["cao_o"] > CAO_MAC_DINH, f"dòng chưa giãn ngay sau khi sửa: {sau}"
    assert sau["xuong_dong"] and sau["so_dong"] == 2, sau
    assert dong_1 in sau["chu"] and dong_2 in sau["chu"], sau

    _cho_da_luu(trang)
    dong[0].refresh_from_db()
    assert dong[0].data["ghi_chu"] == f"{dong_1}\n{dong_2}"

    trang.reload()
    _cho_luoi_co_du_lieu(trang)
    lai = _o_ghi_chu(trang, ma)
    assert lai and "loi" not in lai and lai["cao_o"] > CAO_MAC_DINH, lai
    assert not loi_js, loi_js
    print(f"\nAC-11.44 sửa trong ô — trước: {truoc['cao_o']} px, ô nhập: {cao_khung} px, sau: {sau}")


def test_keo_tay_ve_28_thang_tu_tinh_va_home_ve_tu_dong(live_server, trang, dang_nhap,
                                                        kn_crm, feedback, nguoi_dung):  # noqa: F811
    """AC-11.44 — Người dùng thu dòng ghi chú dài về 28 px thì 28 px thắng chiều cao
    tự tính và được nhớ qua lần tải lại; Home trả dòng về chiều cao tự động"""
    bang, _, dong = feedback
    ma = _ghi(dong[1], GHI_CHU_DAI)

    loi_js = _mo_luoi(trang, live_server, dang_nhap, nguoi_dung, bang)
    tu_dong = _o_ghi_chu(trang, ma)
    assert tu_dong and "loi" not in tu_dong and tu_dong["cao_o"] > CAO_MAC_DINH, tu_dong

    # ↑ trên tay kéo bớt 4 px mỗi lần; 40 lần là chắc chắn chạm đáy 28 px
    trang.locator(f"[data-row-resize='{tu_dong['r']}']").focus()
    for _ in range(40):
        trang.keyboard.press("ArrowUp")
    keo = _o_ghi_chu(trang, ma)
    assert keo["cao_o"] == CAO_MAC_DINH, keo
    assert _chieu_cao_da_nho(trang).get(str(dong[1].pk)) == CAO_MAC_DINH, _chieu_cao_da_nho(trang)

    trang.reload()
    _cho_luoi_co_du_lieu(trang)
    trang.wait_for_timeout(300)
    sau_tai = _o_ghi_chu(trang, ma)
    assert sau_tai["cao_o"] == CAO_MAC_DINH, f"28 px kéo tay bị chiều cao tự tính đè sau khi tải lại: {sau_tai}"

    trang.locator(f"[data-row-resize='{sau_tai['r']}']").focus()
    trang.keyboard.press("Home")
    home = _o_ghi_chu(trang, ma)
    assert home["cao_o"] > CAO_MAC_DINH, f"Home phải trả về chiều cao tự động: {home}"
    assert str(dong[1].pk) not in _chieu_cao_da_nho(trang)
    assert not loi_js, loi_js
    print(f"\nAC-11.44 kéo tay — tự động {tu_dong['cao_o']} → kéo {keo['cao_o']} → tải lại {sau_tai['cao_o']} → Home {home['cao_o']}")


def test_ghi_chu_qua_tran_cat_o_2000_va_mo_hop_doc(live_server, trang, dang_nhap,
                                                   kn_crm, feedback, nguoi_dung):  # noqa: F811
    """AC-11.44 — Ghi chú dài hơn trần: dòng dừng ở 2000 px, phần còn lại đọc bằng hộp
    đọc khi bấm ô"""
    bang, _, dong = feedback
    ma = _ghi(dong[1], GHI_CHU_QUA_TRAN)

    loi_js = _mo_luoi(trang, live_server, dang_nhap, nguoi_dung, bang)
    o = _o_ghi_chu(trang, ma)
    assert o and "loi" not in o, o
    assert o["cao_o"] == TRAN, o
    assert o["cao_chu"] > TRAN, "nội dung phải còn dài hơn trần mới có gì để hộp đọc hiện"

    trang.click(f".mg-cell[data-code='ghi_chu'][data-r='{o['r']}']", position={"x": 20, "y": 10})
    trang.wait_for_selector("#mg-reader:not([hidden])", timeout=5_000)
    assert "Nội dung rất dài" in trang.text_content("#mg-reader")
    assert not loi_js, loi_js
    print(f"\nAC-11.44 quá trần: {dict(o, chu=o['chu'][:40] + '…')}")


def _phan_tram(so, p):
    so = sorted(so)
    return so[min(len(so) - 1, int(round(p * (len(so) - 1))))] if so else None


def test_do_hieu_nang_1000_dong_ghi_chu_400(live_server, trang, dang_nhap,
                                            kn_crm, feedback, nguoi_dung):  # noqa: F811
    """AC-11.44 — 1000 dòng, dòng nào cũng có ghi chú 400 ký tự khác nhau: cuộn hết bảng,
    mỗi khối 100 dòng đo chiều cao một lượt; p95 một lượt dưới ngưỡng đỏ 100 ms, ghi số
    vào biên bản kiểm chứng"""
    bang, _, dong = feedback
    cot = list(bang.columns.all())
    them = []
    for i in range(1000):
        r = DataRecord(table=bang, created_by=nguoi_dung["admin"],
                       data={**dong[0].data, "ma_don": f"HN-{i:04d}", "ten_khach": f"Khách đo {i}",
                             "ghi_chu": f"{GHI_CHU_400} #{i:04d}"})
        r.sync_indexed_columns(cot)
        them.append(r)
    DataRecord.objects.bulk_create(them)

    loi_js = _mo_luoi(trang, live_server, dang_nhap, nguoi_dung, bang)
    trang.evaluate(
        """() => { window.__viec_dai = [];
                   new PerformanceObserver(l => window.__viec_dai.push(
                       ...l.getEntries().map(e => Math.round(e.duration))))
                     .observe({type: 'longtask', buffered: true}); }"""
    )
    cuon = trang.evaluate(
        """async () => {
            const vp = document.getElementById('mg-viewport');
            const doi_ve = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
            const cho_du_lieu = () => new Promise(res => { const t0 = performance.now();
                (function k() {
                    const o = [...document.querySelectorAll(".mg-body .mg-cell[data-code='ma_don']")];
                    if ((o.length && o.every(e => e.dataset.id)) || performance.now() - t0 > 8000) res();
                    else requestAnimationFrame(k);
                })(); });
            let buoc = 0;
            while (vp.scrollTop + vp.clientHeight < vp.scrollHeight - 1 && buoc < 600) {
                vp.scrollTop += vp.clientHeight; buoc++;
                await doi_ve(); await cho_du_lieu();
            }
            return {buoc, cao_bang: vp.scrollHeight, tong: window.KNJSC_MASTER.diagnostics().total};
        }"""
    )
    do = trang.evaluate(
        "() => performance.getEntriesByName('mg-auto-height').map(e => Math.round(e.duration * 10) / 10)")
    viec_dai = trang.evaluate("() => window.__viec_dai")
    assert cuon["tong"] >= 1002, cuon
    assert len(do) >= 10, f"phải có ít nhất một lượt đo cho mỗi khối 100 dòng: {do}"
    ket_qua = {"so_luot_do": len(do), "p50_ms": _phan_tram(do, .5), "p95_ms": _phan_tram(do, .95),
               "max_ms": max(do), "viec_dai_50ms": len(viec_dai), "viec_dai_max_ms": max(viec_dai, default=0),
               "cuon": cuon}
    print(f"\nAC-11.44 hiệu năng 1000 dòng × ghi chú 400 ký tự: {ket_qua}")
    assert ket_qua["p95_ms"] <= NGUONG_DO_MOT_KHOI_MS, ket_qua
    assert not loi_js, loi_js


def test_nguoi_khac_sua_thi_dong_do_lai_va_dong_cao_khong_co_ve_28(
        live_server, trang, dang_nhap, kn_crm, feedback, nguoi_dung):  # noqa: F811
    """AC-11.44 — Người khác sửa ghi chú: lưới hỏi mốc mỗi 8 giây, thấy đổi thì tải lại mềm.
    Dòng vừa được sửa phải cao lên **không cần tải lại trang**, và dòng đang cao **không
    được co về 28 px** trong suốt lượt tải lại đó"""
    bang, _, dong = feedback
    ma_ngan, ma_dai = _ghi(dong[0], GHI_CHU_NGAN), _ghi(dong[1], GHI_CHU_DAI)

    loi_js = _mo_luoi(trang, live_server, dang_nhap, nguoi_dung, bang)
    ngan, dai = _o_ghi_chu(trang, ma_ngan), _o_ghi_chu(trang, ma_dai)
    assert ngan["cao_o"] == CAO_MAC_DINH and dai["cao_o"] > CAO_MAC_DINH, (ngan, dai)
    trang.wait_for_timeout(1500)   # để lưới kịp ghi mốc đầu tiên trước khi dữ liệu đổi

    # Theo dõi liên tục chiều cao dòng đang cao: nó không được tụt xuống 28 px lúc nào
    trang.evaluate(
        """r => { window.__thap_nhat = 9999;
                  window.__theo_doi = setInterval(() => {
                      const o = document.querySelector(`.mg-cell[data-code='ghi_chu'][data-r='${r}']`);
                      if (o) window.__thap_nhat = Math.min(window.__thap_nhat,
                          Math.round(o.getBoundingClientRect().height));
                  }, 100); }""", dai["r"])

    # "Người khác" sửa: lưu trọn bản ghi để mốc sửa gần nhất đổi theo
    dong[0].data["ghi_chu"] = GHI_CHU_DAI
    dong[0].save()

    # Poll chạy mỗi 8 giây; chờ rộng tay tới 30 giây rồi mới kết luận
    trang.wait_for_function(
        """r => { const o = document.querySelector(`.mg-cell[data-code='ghi_chu'][data-r='${r}']`);
                  return o && o.getBoundingClientRect().height > 28; }""",
        arg=ngan["r"], timeout=30_000)
    thap_nhat = trang.evaluate("() => { clearInterval(window.__theo_doi); return window.__thap_nhat; }")

    sau = _o_ghi_chu(trang, ma_ngan)
    assert sau["cao_o"] > CAO_MAC_DINH and sau["xuong_dong"], sau
    assert thap_nhat > CAO_MAC_DINH, (
        f"dòng đang cao đã tụt xuống {thap_nhat} px trong lượt tải lại mềm — chiều cao bị xoá sạch")
    assert not loi_js, loi_js
    print(f"\nAC-11.44 người khác sửa — dòng ngắn 28 → {sau['cao_o']} px; "
          f"dòng đang cao thấp nhất chạm {thap_nhat} px")


def test_dong_trong_cuoi_bang_go_ghi_chu_dai(live_server, trang, dang_nhap,
                                             kn_crm, feedback, nguoi_dung):  # noqa: F811
    """AC-11.44 — Gõ ghi chú dài vào dòng trống sẵn cuối bảng: dòng giãn ngay lúc gõ, và giữ
    nguyên chiều cao sau khi dòng nháp thành bản ghi thật"""
    bang, _, dong = feedback
    loi_js = _mo_luoi(trang, live_server, dang_nhap, nguoi_dung, bang)

    tong = trang.evaluate("() => window.KNJSC_MASTER.diagnostics().total")
    that = len(dong)
    assert tong > that, f"bảng phải có dòng trống sẵn để nhập (tổng {tong}, dòng thật {that})"

    # Dòng trống đầu tiên đứng ngay sau các dòng thật
    r = that
    trang.evaluate("r => document.getElementById('mg-viewport').scrollTop = r * 28", r)
    trang.wait_for_timeout(400)
    _o_ghi_chu(trang, dong[0].data["ma_don"])       # cuộn ngang tới cột Ghi chú
    o = trang.locator(f".mg-cell[data-code='ghi_chu'][data-r='{r}']")
    assert o.count(), f"không thấy ô Ghi chú của dòng trống thứ {r}"
    o.click()
    trang.keyboard.press("F2")
    trang.wait_for_selector("#mg-editor textarea", state="visible")
    trang.keyboard.type(GHI_CHU_DAI[:200])
    trang.keyboard.press("Control+Enter")
    trang.wait_for_timeout(700)

    cao_khi_go = trang.evaluate(
        f"() => Math.round(document.querySelector(\".mg-cell[data-code='ghi_chu'][data-r='{r}']\")"
        ".getBoundingClientRect().height)")
    assert cao_khi_go > CAO_MAC_DINH, f"dòng trống gõ ghi chú dài mà không giãn: {cao_khi_go} px"

    _cho_da_luu(trang)
    trang.wait_for_timeout(600)
    cao_sau_luu = trang.evaluate(
        f"() => {{ const o = document.querySelector(\".mg-cell[data-code='ghi_chu'][data-r='{r}']\");"
        "return o ? Math.round(o.getBoundingClientRect().height) : null; }")
    assert cao_sau_luu and cao_sau_luu > CAO_MAC_DINH, (
        f"dòng nháp thành bản ghi thật xong lại co về {cao_sau_luu} px")
    assert not loi_js, loi_js
    print(f"\nAC-11.44 dòng trống — lúc gõ {cao_khi_go} px, sau khi lưu {cao_sau_luu} px")


def test_hoan_tac_roi_lam_lai(live_server, trang, dang_nhap,
                              kn_crm, feedback, nguoi_dung):  # noqa: F811
    """AC-11.44 — Xoá ghi chú, hoàn tác bằng Ctrl+Z rồi làm lại bằng Ctrl+Y: dòng co rồi cao
    rồi co lại theo đúng từng bước, không phải tải lại trang"""
    bang, _, dong = feedback
    ma = _ghi(dong[1], GHI_CHU_DAI)
    loi_js = _mo_luoi(trang, live_server, dang_nhap, nguoi_dung, bang)
    dau = _o_ghi_chu(trang, ma)
    assert dau["cao_o"] > CAO_MAC_DINH, dau

    def cao():
        trang.wait_for_timeout(800)
        return trang.evaluate(
            f"() => Math.round(document.querySelector(\".mg-cell[data-code='ghi_chu']"
            f"[data-r='{dau['r']}']\").getBoundingClientRect().height)")

    trang.click(f".mg-cell[data-code='ghi_chu'][data-r='{dau['r']}']")
    trang.keyboard.press("Delete")
    sau_xoa = cao()
    trang.keyboard.press("Control+z")
    sau_hoan_tac = cao()
    trang.keyboard.press("Control+y")
    sau_lam_lai = cao()

    print(f"\nAC-11.44 hoàn tác/làm lại — đầu {dau['cao_o']} → xoá {sau_xoa} → "
          f"Ctrl+Z {sau_hoan_tac} → Ctrl+Y {sau_lam_lai}")
    assert sau_xoa == CAO_MAC_DINH, f"xoá ghi chú mà dòng vẫn {sau_xoa} px"
    assert sau_hoan_tac > CAO_MAC_DINH, f"Ctrl+Z trả lại ghi chú dài mà dòng vẫn {sau_hoan_tac} px"
    assert sau_lam_lai == CAO_MAC_DINH, f"Ctrl+Y xoá lại ghi chú mà dòng vẫn {sau_lam_lai} px"
    _cho_da_luu(trang)
    assert not loi_js, loi_js


@pytest.mark.parametrize("nen", ["sang", "toi"])
def test_anh_doi_chieu(live_server, trinh_duyet, dang_nhap, kn_crm,
                       feedback, nguoi_dung, nen):  # noqa: F811
    """AC-11.44 — Ảnh chụp lưới để người xem đối chiếu, hai cỡ màn hình và hai nền.

    Không khẳng định gì ngoài việc trang mở được: đây là bằng chứng nhìn cho biên bản
    kiểm chứng, theo yêu cầu chụp 1440 và 390 px, sáng và tối.
    """
    bang, _, dong = feedback
    _ghi(dong[0], GHI_CHU_HAI_DONG)
    _ghi(dong[1], GHI_CHU_DAI)

    for ten, khung in (("1440", {"width": 1440, "height": 900}),
                       ("390", {"width": 390, "height": 844})):
        ctx = trinh_duyet.new_context(viewport=khung, locale="vi-VN")
        trang = ctx.new_page()
        trang.set_default_timeout(15_000)
        dang_nhap(trang, nguoi_dung["staff_vd"])
        trang.add_init_script(f"localStorage.setItem('knjsc-nen','{'dark' if nen == 'toi' else 'light'}')")
        trang.goto(f"{live_server.url}/bang-tinh/{bang.code}/")
        trang.evaluate(f"() => document.documentElement.dataset.theme = '{'dark' if nen == 'toi' else 'light'}'")
        _cho_luoi_co_du_lieu(trang)
        # Cuộn tới cột Ghi chú, nếu không ảnh chỉ thấy dòng cao lên mà không thấy chữ
        trang.evaluate(
            """async () => {
                const vp = document.getElementById('mg-viewport');
                const doi_ve = () => new Promise(r => requestAnimationFrame(
                    () => requestAnimationFrame(r)));
                for (let x = 0; x <= vp.scrollWidth; x += 300) {
                    vp.scrollLeft = x;
                    await doi_ve();
                    const o = document.querySelector(".mg-cell[data-code='ghi_chu']");
                    if (!o) continue;
                    // Đẩy thêm cho cả cột lọt vào khung, không bị mép phải cắt
                    const hop = o.getBoundingClientRect();
                    const thua = hop.right - vp.getBoundingClientRect().right;
                    if (thua > 0) { vp.scrollLeft = x + thua + 24; await doi_ve(); }
                    return vp.scrollLeft;
                }
            }"""
        )
        trang.wait_for_timeout(800)
        chup(trang, f"ghi-chu-tu-gian-dong-{ten}-{nen}")
        ctx.close()
