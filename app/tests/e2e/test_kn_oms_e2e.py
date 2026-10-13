"""AC-51.5 → AC-51.9 — KN OMS chạy trong trình duyệt thật (ADR-051, chủ dự án 13.10.2026).

Trang không gọi máy chủ: mọi số liệu sinh trong trình duyệt từ hạt giống cố định. Đồng hồ trình duyệt đóng băng ở một
mốc (`clock.set_fixed_time`, bộ đếm giờ vẫn chạy) nên lần nào dữ liệu cũng như nhau; font Google bị chặn để bài không
phụ thuộc mạng. Bài đọc móc `data-*` của trang, không đoán số cụ thể.
"""
import re
from datetime import datetime, timezone

import pytest
from playwright.sync_api import expect

from orders.services import dispatch_service

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]

#: 10:00 giờ Việt Nam
MOC = datetime(2026, 10, 13, 3, 0, tzinfo=timezone.utc)
MAN = {"baodon": "bao-don", "congno": "cong-no", "ruiro": "khach-rui-ro", "kho": "kho", "kenh": "kenh-ban",
       "lai": "lai-theo-page"}
MUC = {"cao": 3, "chu-y": 2, "thap": 1}


@pytest.fixture
def kn_crm(settings):
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.BANGTINH_URL = ""
    return settings


def _chuan_bi(context):
    """Đóng băng đồng hồ, chặn font Google cho mọi tab của phiên."""
    context.clock.set_fixed_time(MOC)
    context.route(re.compile(r"^https://fonts\.(googleapis|gstatic)\.com/"), lambda route: route.abort())


def _theo_doi(page, live_server, loi, ngoai):
    """Ghi lỗi JS và mọi request không phải trang /oms/ hay tệp tĩnh (font Google đã chặn, không tính)."""
    page.on("pageerror", lambda e: loi.append(str(e)))
    page.on("request", lambda r: ngoai.append(r.url) if not (
        r.url.startswith((f"{live_server.url}/oms/", f"{live_server.url}/static/"))
        or re.match(r"^https://fonts\.(googleapis|gstatic)\.com/", r.url)) else None)


def _cho_man(page, view):
    expect(page.locator(f"#v-{view}")).to_be_visible()
    page.locator(f"#v-{view} > *").first.wait_for()


def _mo_oms(page, live_server, dang_nhap, admin, man="baodon"):
    _chuan_bi(page.context)
    loi = []
    page.on("pageerror", lambda e: loi.append(str(e)))
    dang_nhap(page, admin)
    page.goto(f"{live_server.url}/oms/#{MAN[man]}")
    _cho_man(page, man)
    return loi


def _so_kpi(page, khung, loc):
    return int(page.locator(f'{khung} [data-loc="{loc}"] .gia-tri').inner_text().replace(".", ""))


def test_mo_tu_thanh_ben_nen_dong_bo_ba_man_cu_va_dat_lai(live_server, trang, dang_nhap, kn_crm, nguoi_dung):
    """AC-51.5 — Admin bấm "KN OMS" ở thanh bên KN CRM: tab mới mở /oms/; nền theo KN CRM hai chiều; Báo đơn (lọc tắc,
    ngăn kéo có khối Thanh toán, Esc trả con trỏ), Kho (nhập kho vào sổ), Kênh (lọc nền tảng, page mất kết nối) chạy;
    địa chỉ #màn mở đúng màn kể cả nút Lùi; "Đặt lại demo" về đúng dữ liệu đầu; không lỗi JS, không gọi máy chủ ngoài
    trang và tệp tĩnh"""
    dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    _chuan_bi(trang.context)
    dang_nhap(trang, nguoi_dung["admin"])
    trang.goto(f"{live_server.url}/")
    lk = trang.locator('#thanh-ben a[href="/oms/"]')
    expect(lk).to_have_attribute("target", "_blank")
    loi, ngoai = [], []
    with trang.context.expect_page() as moi:
        lk.click()
    oms = moi.value
    _theo_doi(oms, live_server, loi, ngoai)
    _cho_man(oms, "baodon")
    assert oms.url == f"{live_server.url}/oms/"
    assert oms.title().startswith("KN OMS")
    dau_bao_don = oms.locator("#bd-than").inner_text()

    # Nền: KN CRM đang sáng thì KN OMS sáng; đổi ở OMS thì CRM tải lại thấy tối; đổi ở CRM thì OMS theo ngay
    expect(oms.locator("html")).to_have_attribute("data-theme", "light")
    oms.click("#nut-nen")
    expect(oms.locator("html")).to_have_attribute("data-theme", "dark")
    expect(oms.locator("#nut-nen")).to_have_attribute("aria-pressed", "true")
    trang.reload()
    expect(trang.locator("html")).to_have_attribute("data-theme", "dark")
    trang.click("#nut-nen")
    expect(oms.locator("html")).to_have_attribute("data-theme", "light")

    # Báo đơn: lọc đơn tắc, mở ngăn kéo có khối Thanh toán, Esc đóng và trả con trỏ về dòng vừa mở
    oms.click('#bd-kpi [data-loc="tac"]')
    hang = oms.locator("#bd-than tr[data-don]")
    assert hang.count() > 0
    assert all("Tắc" in t for t in hang.all_inner_texts())
    ma = hang.first.get_attribute("data-don")
    hang.first.click()
    expect(oms.locator("#ngan-tieu-de")).to_have_text(ma)
    expect(oms.locator("#ngan .khoi-tt")).to_be_visible()
    oms.keyboard.press("Escape")
    expect(oms.locator("#ngan")).to_be_hidden()
    assert oms.evaluate("document.activeElement.dataset.don") == ma

    # Kho: nhập 50 thì tồn và sổ nhập xuất đổi theo
    oms.click('.nav-muc[data-view="kho"]')
    _cho_man(oms, "kho")
    expect(oms).to_have_url(f"{live_server.url}/oms/#kho")
    ton = oms.locator("#kho-kpi .o-so").first.inner_text()
    oms.click('#v-kho header [data-act="mo-phieu"][data-loai="nhap"]')
    oms.fill("#p-sl", "50")
    oms.click('#f-phieu button[type="submit"]')
    expect(oms.locator("#thong-bao")).to_contain_text("Đã nhập 50")
    expect(oms.locator("#kho-so tbody tr").first).to_contain_text("+50")
    assert oms.locator("#kho-kpi .o-so").first.inner_text() != ton

    # Kênh: lọc TikTok Shop còn hai gian hàng; page Nhật mất kết nối, ngăn kéo có nút Kết nối lại
    oms.click('.nav-muc[data-view="kenh"]')
    _cho_man(oms, "kenh")
    oms.click('#kn-loc [data-nen="tt"]')
    expect(oms.locator("#kn-luoi article")).to_have_count(2)
    oms.click('#kn-loc [data-nen=""]')
    oms.click('#kn-luoi article[data-kenh="fb-jp"]')
    expect(oms.locator("#ngan")).to_contain_text("Mất kết nối")
    expect(oms.locator('#ngan [data-act="ket-noi-lai"]')).to_be_visible()
    oms.keyboard.press("Escape")

    # Nút Lùi về màn trước; địa chỉ #màn mở thẳng đúng màn ở tab mới
    oms.go_back()
    _cho_man(oms, "kho")
    expect(oms.locator('.nav-muc[data-view="kho"]')).to_have_attribute("aria-current", "page")
    tab2 = trang.context.new_page()
    _theo_doi(tab2, live_server, loi, ngoai)
    tab2.goto(f"{live_server.url}/oms/#lai-theo-page")
    _cho_man(tab2, "lai")
    assert tab2.locator("#v-baodon").is_hidden()
    tab2.close()

    # Đặt lại demo: dữ liệu về đúng như lúc mở (đồng hồ đóng băng nên so được từng chữ)
    oms.click('.nav-muc[data-view="baodon"]')
    _cho_man(oms, "baodon")
    oms.click('[data-act="dat-lai"]')
    expect(oms.locator("#thong-bao")).to_contain_text("Đã đặt lại dữ liệu demo")
    assert oms.locator("#bd-than").inner_text() == dau_bao_don
    oms.click('.nav-muc[data-view="kho"]')
    assert oms.locator("#kho-kpi .o-so").first.inner_text() == ton
    assert not loi, loi
    assert not ngoai, f"KN OMS gọi máy chủ: {ngoai}"


def test_dien_thoai_390_sau_man_khong_tran_ngang(live_server, trang_dien_thoai, dang_nhap, kn_crm, nguoi_dung):
    """AC-51.5 — Điện thoại 390 px: cả sáu màn không tràn ngang trang, không bảng nào phải cuộn ngang, không lỗi JS"""
    trang = trang_dien_thoai
    loi = _mo_oms(trang, live_server, dang_nhap, nguoi_dung["admin"])
    for view, hash_ in MAN.items():
        trang.evaluate(f"location.hash = '#{hash_}'")
        _cho_man(trang, view)
        tran = trang.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        assert tran <= 0, f"màn {view} tràn ngang {tran}px"
        bang = trang.evaluate(f"Array.from(document.querySelectorAll('#v-{view} .bang-cuon')).map(c => c.scrollWidth - c.clientWidth)")
        assert all(x <= 0 for x in bang), f"bảng màn {view} phải cuộn ngang: {bang}"
    assert not loi, loi


def test_cong_no_tien_theo_loai_khop_nhac_ghi_nhan(live_server, trang, dang_nhap, kn_crm, nguoi_dung):
    """AC-51.6 — Công nợ: KPI và tiền sàn tách theo từng loại tiền, không quy ₫; lọc tuổi nợ trên 30 ngày đúng; khớp
    tiền về theo gợi ý thì đơn thành Đã thanh toán + Đã về TK (cả ở ngăn kéo Báo đơn); khớp tay một khoản lệch; nhắc
    khách ghi vào hành trình; ghi nhận tiền kiểm số nhập rồi thành Thanh toán 1 phần; đơn page vừa giao vào Công nợ"""
    loi = _mo_oms(trang, live_server, dang_nhap, nguoi_dung["admin"], "congno")
    chip = re.compile(r"^[\d.,]+ (USD|CAD|PHP|EUR|KRW|JPY|AUD)$")
    tien_kpi = trang.locator("#cn-kpi .tien-o").all_inner_texts()
    assert tien_kpi and all(chip.match(t) for t in tien_kpi), tien_kpi
    assert "₫" not in trang.locator("#cn-kpi").inner_text()
    san = trang.locator("#cn-san li").all_inner_texts()
    assert len(san) >= 2 and all("₫" not in s and re.search(r"(USD|PHP)\s*$", s) for s in san), san

    # Tuổi nợ trên 30 ngày
    trang.click('#cn-tuoi [data-tuoi=">30"]')
    tuoi = [r.get_attribute("data-tuoi") for r in trang.locator("#cn-than tr[data-don]").all()]
    assert tuoi and set(tuoi) == {">30"}, tuoi
    trang.click('#cn-tuoi [data-tuoi=""]')

    # Khớp tiền về theo gợi ý mã đơn → đơn đủ tiền, Đã về TK, rời danh sách phải thu
    tv = trang.locator('#cn-tien-ve li[data-cach="ma"]').first
    ma_tv, don = tv.get_attribute("data-tv"), tv.get_attribute("data-goi-y")
    tv.locator('[data-act="cn-khop"]').click()
    expect(trang.locator(f'#cn-tien-ve li[data-tv="{ma_tv}"]')).to_have_attribute("data-cach", "xong")
    trang.fill("#cn-q", don)
    expect(trang.locator("#cn-than tr[data-don]")).to_have_count(0)
    trang.fill("#cn-q", "")
    trang.click('.nav-muc[data-view="baodon"]')
    _cho_man(trang, "baodon")
    trang.fill("#bd-q", don)
    trang.locator(f'#bd-than tr[data-don="{don}"]').click()
    expect(trang.locator("#ngan .khoi-tt")).to_contain_text("Đã thanh toán")
    expect(trang.locator("#ngan .khoi-tt")).to_contain_text("Đã về TK")
    expect(trang.locator("#ngan .dong-tg")).to_contain_text(f"Tiền về {ma_tv}")
    trang.keyboard.press("Escape")

    # Khoản không khớp sẵn đơn nào: chọn tay đơn cùng loại tiền
    trang.click('.nav-muc[data-view="congno"]')
    _cho_man(trang, "congno")
    lech = trang.locator('#cn-tien-ve li[data-cach=""]').first
    ma_lech = lech.get_attribute("data-tv")
    lech.locator('[data-act="cn-khop"]').click()
    expect(trang.locator(f'#cn-tien-ve li[data-tv="{ma_lech}"]')).to_have_attribute("data-cach", "xong")
    expect(trang.locator("#thong-bao")).to_contain_text(f"Đã khớp {ma_lech}")

    # Nhắc khách: số lần nhắc tăng, hành trình có dòng nhắc
    dau = trang.locator("#cn-than tr[data-don]").first
    don_nhac = dau.get_attribute("data-don")
    cu = re.search(r"Đã nhắc (\d+) lần", dau.inner_text())
    dau.locator('[data-act="cn-nhac"]').click()
    hang = trang.locator(f'#cn-than tr[data-don="{don_nhac}"]')
    expect(hang).to_contain_text(f"Đã nhắc {(int(cu.group(1)) if cu else 0) + 1} lần")
    hang.locator("td").first.click()
    expect(trang.locator("#ngan .dong-tg")).to_contain_text("Nhắc khách thanh toán lần")
    trang.keyboard.press("Escape")

    # Ghi nhận tiền: chữ và số quá phần còn lại bị chặn, số hợp lệ thành Thanh toán 1 phần
    hang.locator('[data-act="cn-ghi"]').click()
    trang.fill("#gt-so", "abc")
    trang.click('#f-ghi-tien button[type="submit"]')
    expect(trang.locator("#gt-loi")).to_contain_text("không hợp lệ")
    trang.fill("#gt-so", "99999999")
    trang.click('#f-ghi-tien button[type="submit"]')
    expect(trang.locator("#gt-loi")).to_contain_text("lớn hơn số còn phải thu")
    trang.fill("#gt-so", "1")
    trang.click('#f-ghi-tien button[type="submit"]')
    expect(trang.locator("#ngan")).to_be_hidden()
    expect(hang).to_contain_text("Thanh toán 1 phần")

    # Đơn page vừa giao sau "Cập nhật từ hãng" vào Công nợ đúng số đơn báo trong thông báo
    truoc = _so_kpi(trang, "#cn-kpi", "chua")
    trang.click('.nav-muc[data-view="baodon"]')
    _cho_man(trang, "baodon")
    trang.click("#bd-hoi")
    bao = trang.locator("#thong-bao .toast", has_text="Đã hỏi hãng")
    expect(bao).to_be_visible(timeout=10_000)
    vao = re.search(r"\((\d+) đơn vào Công nợ\)", bao.inner_text())
    assert vao and int(vao.group(1)) >= 1, bao.inner_text()
    trang.click('.nav-muc[data-view="congno"]')
    _cho_man(trang, "congno")
    assert _so_kpi(trang, "#cn-kpi", "chua") == truoc + int(vao.group(1))
    assert not loi, loi


def test_khach_rui_ro_chip_mau_tim_so_va_chan_len_don(live_server, trang, dang_nhap, kn_crm, nguoi_dung):
    """AC-51.7 — Khách rủi ro: bốn chip mẫu ra đúng mức (Cao, Thấp, Cần chú ý, Chưa có đơn); gõ số hai kiểu đều tìm ra
    một khách; danh sách xếp theo mức rủi ro và SĐT vẫn che; Chặn lên đơn đổi nhãn ở danh sách và thẻ; có khối Cách tính"""
    loi = _mo_oms(trang, live_server, dang_nhap, nguoi_dung["admin"], "ruiro")
    the = trang.locator("#rr-the .rr-the")
    for mau, muc in (("hoan", "cao"), ("tot", "thap"), ("no", "chu-y"), ("moi", "moi")):
        trang.click(f'[data-act="rr-mau"][data-mau="{mau}"]')
        expect(the).to_have_attribute("data-muc", muc)
    expect(the).to_contain_text("Chưa có đơn nào với SĐT này")
    for kieu in ("(408) 555-0142", "+1 408 555 0142"):
        trang.fill("#rr-sdt", kieu)
        expect(the).to_have_attribute("data-kh", "KH-90001")

    muc = [MUC[r.get_attribute("data-muc")] for r in trang.locator("#rr-ds tr[data-muc]").all()]
    assert muc and muc == sorted(muc, reverse=True) and muc[0] == 3, muc
    for dong in trang.locator("#rr-ds tr[data-muc]").all_inner_texts():
        assert "•" in dong and not re.search(r"\d{3}[-\s]?\d{4}\b", dong), dong

    trang.click('[data-act="rr-mau"][data-mau="hoan"]')
    the.locator('[data-act="rr-danh-dau"][data-gia-tri="chan"]').click()
    expect(trang.locator('#rr-ds tr[data-khach="KH-90002"]')).to_contain_text("Chặn lên đơn")
    expect(trang.locator('#rr-loc [data-loc="chan"] .dem')).to_have_text("1")
    expect(the.locator(".nen-lam")).to_contain_text("Đang chặn lên đơn")
    expect(the.locator('[data-gia-tri="chan"]')).to_have_attribute("aria-pressed", "true")
    expect(trang.locator("#v-ruiro .cach-tinh li")).to_have_count(5)
    assert not loi, loi


def test_lai_theo_page_lo_ti_gia_thac_va_cach_xem(live_server, trang, dang_nhap, kn_crm, nguoi_dung):
    """AC-51.8 — Lãi theo page: đúng hai page lỗ (KN Beauty Japan, KN Beauty LazMall) ở cả 30 và 7 ngày; thiếu tỉ giá
    KRW thì báo, nhập tỉ giá thì số đổi theo, tỉ giá sai thì báo lỗi và giữ số cũ; thác chi phí từ sáu bước, kết ở Lãi;
    xem theo sản phẩm chín dòng lãi gộp, theo thị trường bảy dòng; đổi kỳ thì số đổi"""
    loi = _mo_oms(trang, live_server, dang_nhap, nguoi_dung["admin"], "lai")
    lo = trang.locator('#lp-than tr[data-lo="1"]')
    assert sorted(r.get_attribute("data-lai") for r in lo.all()) == ["fb-jp", "lz-ph"]
    expect(trang.locator('#lp-kpi [data-loc="lo"]')).to_contain_text("KN Beauty Japan")
    ds30 = trang.locator('#lp-kpi [data-loc="ds"] .gia-tri').inner_text()
    trang.click('[data-act="lp-ky"][data-ky="7"]')
    expect(trang.locator('#lp-kpi [data-loc="ds"] .gia-tri')).not_to_have_text(ds30)
    assert sorted(r.get_attribute("data-lai") for r in lo.all()) == ["fb-jp", "lz-ph"]
    trang.click('[data-act="lp-ky"][data-ky="30"]')
    expect(trang.locator('#lp-kpi [data-loc="ds"] .gia-tri')).to_have_text(ds30)

    # Thiếu tỉ giá KRW → báo; nhập 18 ₫ thì page Hàn có lãi và doanh số tổng đổi
    han = trang.locator('#lp-than tr[data-lai="fb-kr"]')
    expect(han).to_contain_text("Thiếu tỉ giá KRW")
    expect(trang.locator("#lp-ghi")).to_contain_text("KN Beauty Korea (thiếu tỉ giá KRW)")
    trang.fill("#lp-tg-KRW", "18")
    trang.press("#lp-tg-KRW", "Tab")
    expect(han).not_to_contain_text("Thiếu tỉ giá")
    expect(trang.locator('#lp-kpi [data-loc="ds"] .gia-tri')).not_to_have_text(ds30)
    ds_co_krw = trang.locator('#lp-kpi [data-loc="ds"] .gia-tri').inner_text()

    # Tỉ giá sai: báo lỗi, ô về số cũ, số liệu giữ nguyên
    trang.fill("#lp-tg-USD", "abc")
    trang.press("#lp-tg-USD", "Tab")
    expect(trang.locator("#lp-tg-loi")).to_contain_text("Tỉ giá USD phải là số nguyên dương")
    expect(trang.locator("#lp-tg-USD")).to_have_value("25.500")
    assert trang.locator('#lp-kpi [data-loc="ds"] .gia-tri').inner_text() == ds_co_krw

    # Thác chi phí: page Facebook sáu bước, gian hàng sàn thêm phí sàn; bước cuối là Lãi
    for page_id, so_buoc in (("fb-us", 6), ("lz-ph", 7)):
        trang.click(f'#lp-than tr[data-lai="{page_id}"]')
        buoc = trang.locator("#ngan ol.thac > li")
        expect(buoc).to_have_count(so_buoc)
        expect(buoc.last).to_contain_text("Lãi")
        trang.keyboard.press("Escape")
        expect(trang.locator("#ngan")).to_be_hidden()

    trang.click('[data-act="lp-xem"][data-xem="sp"]')
    expect(trang.locator("#lp-than tr")).to_have_count(9)
    expect(trang.locator("#lp-ghi")).to_contain_text("lãi gộp")
    trang.click('[data-act="lp-xem"][data-xem="tt"]')
    expect(trang.locator("#lp-than tr")).to_have_count(7)
    assert not loi, loi


#: (bộ chọn ở trang chủ KN CRM, bộ chọn ở KN OMS, giả phần tử, thuộc tính so)
SO_DIEN_MAO = [
    ("body", "body", None, ("background-color", "color", "font-family")),
    ("body", "body", "::before", ("background-image", "opacity")),
    ("#thanh-ben", "#oms-ben", None, ("background-color", "border-top-left-radius", "border-top-color", "backdrop-filter",
                                     "box-shadow", "width")),
    (".topbar", ".topbar", None, ("background-color", "border-top-left-radius", "border-top-color", "min-height")),
    (".noi-dung", ".noi-dung", None, ("background-color", "border-top-left-radius", "border-top-color", "padding-top",
                                      "box-shadow")),
    (".trang-dau .nut-chinh", "#bd-hoi", None, ("background-color", "color", "border-top-left-radius", "font-weight",
                                                "min-height")),
    (".trang-dau h1", "#v-baodon .trang-dau h1", None, ("font-family", "font-size", "font-weight", "color")),
    ('.nav-muc[aria-current="page"]', '.nav-muc[aria-current="page"]', None, ("background-color", "color",
                                                                               "border-top-left-radius")),
]


def _kieu(page, chon, gia, ten):
    return page.evaluate("([c, g, t]) => { const s = getComputedStyle(document.querySelector(c), g);"
                         " return Object.fromEntries(t.map(x => [x, s.getPropertyValue(x)])); }", [chon, gia, list(ten)])


def test_dien_mao_kn_crm_va_bieu_mau_trong_ngan_keo(live_server, trang, dang_nhap, kn_crm, nguoi_dung):
    """AC-51.9 — KN OMS cùng diện mạo Solarpunk với trang chủ KN CRM ở cả nền sáng và tối (nền, ảnh nền, thanh bên kính,
    thanh trên, mặt đọc, nút chính, chữ tiêu đề, mục đang chọn); không phần tử nào có viền trái hay phải dày hơn 1 px;
    Ghi nhận tiền, Phiếu kho, Thêm kênh mở trong ngăn kéo bên phải, không có hộp thoại nào khác; Huỷ và Esc ở biểu mẫu
    mở từ ngăn kéo đơn thì quay về ngăn kéo đó"""
    dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    _chuan_bi(trang.context)
    loi = []
    trang.on("pageerror", lambda e: loi.append(str(e)))
    dang_nhap(trang, nguoi_dung["admin"])
    oms = trang.context.new_page()
    oms.on("pageerror", lambda e: loi.append(str(e)))
    for nen in ("light", "dark"):
        trang.evaluate(f"localStorage.setItem('knjsc-nen', '{nen}')")
        trang.goto(f"{live_server.url}/")
        oms.goto(f"{live_server.url}/oms/#bao-don")
        _cho_man(oms, "baodon")
        expect(oms.locator("html")).to_have_attribute("data-theme", nen)
        for crm, rieng, gia, ten in SO_DIEN_MAO:
            assert _kieu(trang, crm, gia, ten) == _kieu(oms, rieng, gia, ten), (nen, crm, rieng, gia)
    assert "solarpunk-office.webp" in _kieu(oms, "body", "::before", ("background-image",))["background-image"]

    for man in MAN:
        oms.goto(f"{live_server.url}/oms/#{MAN[man]}")
        _cho_man(oms, man)
        day = oms.evaluate("""() => Array.from(document.querySelectorAll('body *')).filter(el => {
            const s = getComputedStyle(el);
            return parseFloat(s.borderLeftWidth) > 1 || parseFloat(s.borderRightWidth) > 1; }).map(el => el.className)""")
        assert not day, (man, day)

    # Ba biểu mẫu đều ở ngăn kéo bên phải; trang không có hộp thoại nào khác
    oms.goto(f"{live_server.url}/oms/#kho")
    _cho_man(oms, "kho")
    oms.click('#v-kho header [data-act="mo-phieu"][data-loai="chuyen"]')
    expect(oms.locator("#ngan #f-phieu")).to_be_visible()
    expect(oms.locator('#ngan input[name="loai"][value="chuyen"]')).to_be_checked()
    expect(oms.locator("#p-kho2")).to_be_visible()
    oms.keyboard.press("Escape")
    expect(oms.locator("#ngan")).to_be_hidden()
    oms.goto(f"{live_server.url}/oms/#kenh-ban")
    _cho_man(oms, "kenh")
    oms.click('[data-act="them-kenh"]')
    expect(oms.locator("#ngan #f-kenh")).to_be_visible()
    expect(oms.locator("#k-ten")).to_be_focused()
    oms.click('#f-kenh button[type="submit"]')
    expect(oms.locator("#k-loi")).to_contain_text("Nhập tên page")
    oms.fill("#k-ten", "KN Beauty Canada 2")
    oms.click('#f-kenh button[type="submit"]')
    expect(oms.locator("#ngan-tieu-de")).to_have_text("KN Beauty Canada 2")
    expect(oms.locator("#ngan")).to_contain_text("Đã kết nối", timeout=5_000)
    oms.keyboard.press("Escape")
    expect(oms.locator("#kn-luoi article")).to_have_count(12)
    assert oms.locator("#hop, dialog, .hop").count() == 0
    assert oms.locator('[role="dialog"]').count() == 1

    # Ghi nhận tiền mở từ ngăn kéo đơn: Huỷ và Esc quay về ngăn kéo đơn, Esc lần nữa mới đóng
    oms.goto(f"{live_server.url}/oms/#cong-no")
    _cho_man(oms, "congno")
    hang = oms.locator("#cn-than tr[data-don]").first
    don = hang.get_attribute("data-don")
    hang.locator("td").first.click()
    expect(oms.locator("#ngan-tieu-de")).to_have_text(don)
    oms.click('#ngan .khoi-tt [data-act="cn-ghi"]')
    expect(oms.locator("#ngan #f-ghi-tien")).to_be_visible()
    expect(oms.locator("#gt-so")).to_be_focused()
    oms.click('#f-ghi-tien [data-act="huy-form"]')
    expect(oms.locator("#ngan-tieu-de")).to_have_text(don)
    oms.click('#ngan .khoi-tt [data-act="cn-ghi"]')
    oms.keyboard.press("Escape")
    expect(oms.locator("#ngan-tieu-de")).to_have_text(don)
    oms.keyboard.press("Escape")
    expect(oms.locator("#ngan")).to_be_hidden()
    assert not loi, loi
