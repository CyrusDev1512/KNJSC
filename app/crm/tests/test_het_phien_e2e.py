"""Hết phiên giữa lúc làm việc ở KN CRM bằng Chromium thật — TL-02, TL-18, ADR-053 (sửa một điều khoản của ADR-030).

Phiên mất vì đăng xuất ở tab khác (đăng xuất thật bằng cùng kho cookie của trình duyệt, không mở tab thứ hai). Trước:
lưới coi trang đăng nhập là mất quyền và xoá ô đang gõ; htmx dán cả trang đăng nhập vào hộp Chi tiết, hộp lọc, form Lên
đơn; ô phân công đóng như đã lưu; lượt hỏi chứng từ xoá form đang gõ; đăng nhập lại rồi Thử lại vẫn 403 vì mã CSRF cũ.
Nay: không dán, không xoá nháp, không báo lưu giả, lời tiếng Việt kèm cách làm tiếp; đăng nhập lại đúng người rồi bấm Thử
lại/Lưu là lưu được; người khác đăng nhập thì 409, dữ liệu không đổi.

Đặt ở `crm/tests` (lượt CI thứ hai) để không đè hạn 10 phút của lượt `tests/e2e`. Không chờ cứng: chờ theo DOM hay DB.
"""
import time
import uuid

import pytest
from django.conf import settings
from django.test import Client

from core.identity import employee_code
from crm.models import GridCellHistory, GridMutationReceipt
from forms_builder.models import ColumnDef, DataRecord
from orders.models import Order, PaymentDocument, WaybillAssignment, WaybillItem
from core.models import SubmissionReceipt
from tests.e2e.conftest import LY_DO, MAT_KHAU, chup, sync_playwright

from .test_payment_documents import create_document
from .test_waybill_feedback import feedback  # noqa: F401 — fixture
from .test_waybill_new import setup  # noqa: F401 — fixture

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]

HET_PHIEN = "Phiên đăng nhập đã hết"
DOI_NGUOI = "Tài khoản vừa đăng nhập khác người mở trang — nháp không được lưu"


# Trình duyệt theo từng bài, như test_luoi_dong_trong_va_ghim_e2e.py: chạy chung với tests/e2e không dính lỗi
# "Sync API inside the asyncio loop".
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


def _csrf(trang):
    return next(c["value"] for c in trang.context.cookies() if c["name"] == settings.CSRF_COOKIE_NAME)


def _dang_xuat_ngam(trang, live_server):
    """Đăng xuất thật như ở một tab khác: cùng kho cookie với trang đang mở, trang không hay biết."""
    r = trang.context.request.post(live_server.url + "/dang-xuat/", form={"csrfmiddlewaretoken": _csrf(trang)})
    assert r.ok, r.status
    assert not any(c["name"] == settings.SESSION_COOKIE_NAME and c["value"] for c in trang.context.cookies()), \
        "đăng xuất ngầm không xoá phiên"


def _dang_nhap_ngam(trang, live_server, user):
    """Đăng nhập lại như ở tab khác: Django đổi mã CSRF (rotate_token), trang đang mở vẫn giữ mã cũ trong HTML."""
    trang.context.request.get(live_server.url + "/dang-nhap/")
    r = trang.context.request.post(live_server.url + "/dang-nhap/", form={
        "username": user.username, "password": MAT_KHAU, "csrfmiddlewaretoken": _csrf(trang)})
    assert r.ok and "/dang-nhap/" not in r.url, (r.status, r.url)


def _cho(trang, dat, han=10.0):
    het = time.monotonic() + han
    while not dat() and time.monotonic() < het:
        trang.wait_for_timeout(200)
    return dat()


def _mo_toi_o(trang, live_server, bang, o):
    trang.goto(f"{live_server.url}/bang-tinh/{bang.code}/")
    trang.wait_for_selector(".mg-cell[data-code='ten_khach']")
    trang.wait_for_function(f"""() => {{ const v = document.getElementById('mg-viewport');
        if (document.querySelector("{o}")) return true; v.scrollLeft += 300; return false; }}""", timeout=10_000)
    trang.locator(o).scroll_into_view_if_needed()


def _dang_hien(trang):
    assert trang.evaluate("document.visibilityState") == "visible", "tab ẩn thì lượt hỏi 8 giây không chạy"


def _go_o_roi_mat_phien(trang, live_server, bang, dong, chu):
    """Mở lưới, gõ vào ô Tên khách (chưa Enter), phiên mất ở tab khác."""
    o = f".mg-cell[data-code='ten_khach'][data-id='{dong.pk}']"
    _mo_toi_o(trang, live_server, bang, o)
    trang.click(o)
    trang.keyboard.type(chu)
    trang.wait_for_selector("#mg-input [name=value]")
    _dang_xuat_ngam(trang, live_server)
    return o


def _enter_cho_loi_luu(trang):
    trang.keyboard.press("Enter")
    trang.wait_for_function("""() => document.getElementById('bt-trang-thai').textContent === 'Lỗi lưu'
        && [...document.querySelectorAll('#mg-message button')].some(b => b.textContent === 'Thử lại')""", timeout=10_000)


def _bam_thu_lai(trang):
    trang.locator("#mg-message button", has_text="Thử lại").click()


def test_het_phien_dang_go_o_luoi_giu_nhap_dang_nhap_lai_thu_lai_luu_duoc(live_server, trang, dang_nhap, feedback,
                                                                          nguoi_dung):  # noqa: F811
    """AC-21.4 — TL-02, TL-18, ADR-053: đang gõ ô lưới thì phiên mất (đăng xuất ở tab khác): lượt hỏi 8 giây báo
    "Phiên đăng nhập đã hết" tiếng Việt, không "Quyền xem đã thay đổi", ô đang gõ còn nguyên; Enter thì "Lỗi lưu", dữ
    liệu không đổi, có liên kết đăng nhập lại ở tab mới; đăng nhập lại đúng người rồi bấm Thử lại thì lưu được, lịch
    sử ô ghi đúng người; không lỗi JS"""
    bang, _, rows = feedback
    dong, vd = rows[0], nguoi_dung["staff_vd"]
    cu = dong.data.get("ten_khach")
    loi_js = []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(trang, vd)
    o = _go_o_roi_mat_phien(trang, live_server, bang, dong, "Khách Hết Phiên")

    _dang_hien(trang)
    trang.wait_for_function(f"() => document.getElementById('mg-message').textContent.includes('{HET_PHIEN}')",
                            timeout=15_000)
    assert "Quyền xem đã thay đổi" not in trang.locator("#mg-message").text_content()
    assert trang.locator("#mg-input [name=value]").input_value() == "Khách Hết Phiên"

    _enter_cho_loi_luu(trang)
    trang.wait_for_function(f"() => document.querySelector(\"{o}\")?.textContent.includes('Khách Hết Phiên')")
    assert DataRecord.objects.get(pk=dong.pk).data.get("ten_khach") == cu
    assert trang.locator("#mg-message a[target=_blank][href^='/dang-nhap/']").count() == 1
    chup(trang, "het-phien-luoi-giu-nhap")

    _dang_nhap_ngam(trang, live_server, vd)
    _bam_thu_lai(trang)
    assert _cho(trang, lambda: DataRecord.objects.get(pk=dong.pk).data.get("ten_khach") == "Khách Hết Phiên")
    trang.wait_for_function("() => document.getElementById('bt-trang-thai').textContent === 'Đã lưu'", timeout=8_000)
    lich_su = GridCellHistory.objects.filter(record=dong, column="ten_khach").latest("id")
    assert lich_su.receipt.actor_id == vd.pk
    assert not loi_js, loi_js


def test_dang_nhap_tai_khoan_khac_thu_lai_bi_chan_nhap_con_doi_lai_dung_nguoi_luu_duoc(
        live_server, trang, dang_nhap, feedback, nguoi_dung):  # noqa: F811
    """AC-21.4 — ADR-053: hết phiên khi còn nháp, người khác đăng nhập ở tab khác rồi bấm Thử lại thì báo "Tài khoản
    vừa đăng nhập khác người mở trang — nháp không được lưu", có lời dẫn đăng xuất kèm mã người mở trang, không có liên
    kết đăng nhập, dữ liệu và lịch sử không đổi, nháp còn; đăng xuất, đăng nhập đúng người rồi Thử lại thì lưu dưới tên
    người mở trang"""
    bang, _, rows = feedback
    dong, vd, khac = rows[0], nguoi_dung["staff_vd"], nguoi_dung["leader_vd"]
    cu = dong.data.get("ten_khach")
    loi_js = []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(trang, vd)
    o = _go_o_roi_mat_phien(trang, live_server, bang, dong, "Khách Đổi Người")
    _enter_cho_loi_luu(trang)
    lich_su = GridCellHistory.objects.count()

    _dang_nhap_ngam(trang, live_server, khac)
    _bam_thu_lai(trang)
    trang.wait_for_function(f"() => document.getElementById('mg-message').textContent.includes('{DOI_NGUOI}')",
                            timeout=8_000)
    tin = trang.locator("#mg-message").text_content()
    assert employee_code(vd) in tin, tin
    assert trang.locator("#mg-message a[href^='/dang-nhap/']").count() == 0
    assert DataRecord.objects.get(pk=dong.pk).data.get("ten_khach") == cu
    assert GridMutationReceipt.objects.filter(actor=khac).count() == 0
    assert GridCellHistory.objects.count() == lich_su
    assert "Khách Đổi Người" in trang.locator(o).text_content()
    chup(trang, "het-phien-luoi-doi-nguoi")

    _dang_xuat_ngam(trang, live_server)
    _dang_nhap_ngam(trang, live_server, vd)
    _bam_thu_lai(trang)
    assert _cho(trang, lambda: DataRecord.objects.get(pk=dong.pk).data.get("ten_khach") == "Khách Đổi Người")
    assert GridCellHistory.objects.filter(record=dong, column="ten_khach").latest("id").receipt.actor_id == vd.pk
    assert not loi_js, loi_js


def test_het_phien_hop_chi_tiet_va_hop_loc_khong_dan_trang_dang_nhap(live_server, trang, dang_nhap, feedback,
                                                                       nguoi_dung):  # noqa: F811
    """AC-21.4 — TL-18: hộp Chi tiết đang mở (hộp thoại phủ) bấm Lưu chi tiết lúc phiên đã mất thì lời báo hiện ngay
    trong hộp, ô số lượng đang sửa còn nguyên, liên kết đăng nhập lại bấm được, không dán trang đăng nhập, dữ liệu không
    đổi; mở hộp lọc cột lúc đó thì hộp lọc hiện lời báo thay vì trang đăng nhập; trang không rời lưới"""
    bang, _, rows = feedback
    dong = rows[0]
    so_luong = sorted(WaybillItem.objects.filter(record=dong, deleted_at__isnull=True).values_list("pk", "quantity"))
    loi_js = []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(trang, nguoi_dung["staff_vd"])
    o = f".mg-cell[data-code='san_pham'][data-id='{dong.pk}']"
    _mo_toi_o(trang, live_server, bang, o)
    trang.dblclick(o)
    trang.wait_for_selector("#vd-detail-body form")
    trang.locator("#vd-detail-body [name=quantity]").first.fill("3")
    url = trang.url
    _dang_xuat_ngam(trang, live_server)
    trang.locator("#vd-detail-body button[type=submit]").click()

    bao = trang.wait_for_selector("#vd-detail-body .het-phien-o")
    assert HET_PHIEN in bao.text_content()
    assert trang.locator("#vd-detail-body [name=quantity]").first.input_value() == "3"
    assert trang.locator("#vd-detail-body input[name=password]").count() == 0
    trang.locator("#vd-detail-body .het-phien-o a[target=_blank]").click(trial=True)
    assert sorted(WaybillItem.objects.filter(record=dong, deleted_at__isnull=True)
                  .values_list("pk", "quantity")) == so_luong
    assert trang.url == url
    chup(trang, "het-phien-hop-chi-tiet")

    trang.locator("[data-close-detail]").click()
    trang.locator(".mg-filter-icon[data-filter='ten_khach']").click()
    loc = trang.wait_for_selector("#mg-column-filter-body .het-phien-o")
    assert HET_PHIEN in loc.text_content()
    assert trang.locator("#hop-loc input[name=password]").count() == 0
    assert "Quyền xem đã thay đổi" not in (trang.locator("#mg-message").text_content() or "")
    assert trang.url == url
    assert not loi_js, loi_js


def test_het_phien_an_cot_khong_tu_tai_lai_trang(live_server, trang, dang_nhap, feedback, nguoi_dung):  # noqa: F811
    """AC-21.4 — ADR-053: bấm "Ẩn cho cả công ty" lúc phiên đã mất không coi trang đăng nhập là thành công: trang không
    tải lại, hộp Cột đóng để lời báo hiện ra, cột không đổi"""
    bang = feedback[0]
    cot = ColumnDef.objects.get(table=bang, code="ghi_chu")
    dang_nhap(trang, nguoi_dung["admin"])
    trang.goto(f"{live_server.url}/bang-tinh/{bang.code}/")
    trang.wait_for_selector(".mg-cell[data-code='ten_khach']")
    trang.evaluate("window.__moc = 1")
    trang.locator("#mg-columns-button").click()
    nut = trang.locator(f"button[aria-label='Ẩn {cot.name} với cả công ty']")
    nut.wait_for()
    _dang_xuat_ngam(trang, live_server)
    nut.click()
    trang.wait_for_function(f"() => document.getElementById('mg-message').textContent.includes('{HET_PHIEN}')",
                            timeout=8_000)
    assert trang.evaluate("window.__moc") == 1, "trang đã tự tải lại"
    assert not trang.evaluate("document.getElementById('mg-columns').open")
    cot.refresh_from_db()
    assert cot.is_hidden is False


def _dien_len_don(trang, live_server, setup):  # noqa: F811
    trang.goto(f"{live_server.url}/van-don/len-don/")
    f = trang.locator("form[data-order-preview]")
    f.locator("[name=customer_name]").fill("Khách Hết Phiên")
    f.locator("[name=phone]").fill("0901000444")
    f.locator("[name=market]").select_option("us")
    f.locator("[name=payment_method]").select_option(index=1)
    f.locator("[name=product]").first.select_option(setup[2][0].code)
    f.locator("[name=quantity]").first.fill("1")
    f.locator("[name=unit_price]").first.fill("10")
    trang.wait_for_function("() => document.querySelector('[data-order-summary]').textContent.includes('1 dòng')",
                            timeout=8_000)
    return f


def test_het_phien_len_don_giu_form_dang_nhap_lai_ra_mot_don(live_server, trang, dang_nhap, setup,
                                                             nguoi_dung):  # noqa: F811
    """AC-6.11 — TL-18, ADR-053: Lên đơn lúc phiên đã mất: tóm tắt báo hết phiên không bảo tải lại trang, tra khách và
    Lưu đơn không dán trang đăng nhập, lời báo hiện ở form và ô nổi, dữ liệu đã điền còn nguyên, chưa có đơn; đăng nhập
    lại đúng người rồi bấm Lưu đơn thì ra đúng một đơn với đúng mã lần nộp của form"""
    sale = nguoi_dung["staff_sale_1"]
    loi_js = []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(trang, sale)
    f = _dien_len_don(trang, live_server, setup)
    ma = f.locator("[name=ma_lan_nop]").input_value()
    _dang_xuat_ngam(trang, live_server)

    f.locator("[name=unit_price]").first.fill("11")
    trang.wait_for_function(
        f"() => document.querySelector('[data-order-summary]').textContent.includes('{HET_PHIEN}')", timeout=8_000)
    assert "tải lại trang" not in trang.locator("[data-order-summary]").text_content()

    f.locator("[name=phone]").press_sequentially("5")
    trang.wait_for_selector("#nhac-khach .het-phien-o", timeout=8_000)
    assert HET_PHIEN in trang.locator("#nhac-khach .het-phien-o").text_content()
    # Rời ô điện thoại trước (ô mất focus thì tra khách chạy lại), rồi gỡ lời nổi cũ: lời nổi sau đó phải do chính Lưu đơn
    with trang.expect_response(lambda r: "kiem-khach" in r.url, timeout=8_000):
        f.locator("[name=customer_name]").focus()
    trang.evaluate("document.querySelector('.het-phien-noi')?.remove()")

    f.locator("button[type=submit]").click()
    trang.wait_for_selector("#vd-entry > .het-phien-o", timeout=8_000)
    assert HET_PHIEN in trang.locator("#vd-entry > .het-phien-o").text_content()
    trang.wait_for_selector(".het-phien-noi", timeout=8_000)
    assert HET_PHIEN in trang.locator(".het-phien-noi").text_content()
    assert trang.locator("input[name=password]").count() == 0
    assert f.locator("[name=customer_name]").input_value() == "Khách Hết Phiên"
    assert Order.objects.count() == 0
    chup(trang, "het-phien-len-don")

    _dang_nhap_ngam(trang, live_server, sale)
    trang.locator("form[data-order-preview] button[type=submit]").click()
    assert _cho(trang, lambda: Order.objects.count() == 1)
    assert SubmissionReceipt.objects.filter(key=uuid.UUID(ma), kind="order", actor=sale).count() == 1
    assert not loi_js, loi_js


def test_dang_nhap_tai_khoan_khac_bam_luu_don_bi_chan(live_server, trang, dang_nhap, setup, nguoi_dung):  # noqa: F811
    """AC-6.11 — ADR-053: điền xong Lên đơn, người khác đăng nhập ở tab khác rồi bấm Lưu đơn thì báo "Tài khoản vừa
    đăng nhập khác người mở trang", kèm lời dẫn có mã người mở trang, không có liên kết đăng nhập; form còn nguyên, không
    có đơn, không biên nhận"""
    sale = nguoi_dung["staff_sale_1"]
    dang_nhap(trang, sale)
    f = _dien_len_don(trang, live_server, setup)
    _dang_xuat_ngam(trang, live_server)
    _dang_nhap_ngam(trang, live_server, nguoi_dung["leader_sale_1"])
    f.locator("button[type=submit]").click()
    bao = trang.locator("#vd-entry > .het-phien-o")
    bao.wait_for(timeout=8_000)
    tin = bao.text_content()
    assert "Tài khoản vừa đăng nhập khác người mở trang" in tin and employee_code(sale) in tin, tin
    assert bao.locator("a[href^='/dang-nhap/']").count() == 0
    trang.wait_for_selector(".het-phien-noi", timeout=8_000)
    assert "Tài khoản vừa đăng nhập khác người mở trang" in trang.locator(".het-phien-noi").text_content()
    assert f.locator("[name=customer_name]").input_value() == "Khách Hết Phiên"
    assert Order.objects.count() == 0
    assert not SubmissionReceipt.objects.filter(kind="order").exists()


def test_het_phien_khi_chon_nguoi_phan_cong_khong_dong_o_chon(live_server, trang, dang_nhap, feedback,
                                                              nguoi_dung):  # noqa: F811
    """AC-21.15 — TL-18, ADR-053: chọn người phụ trách lúc phiên đã mất thì ô chọn không đóng như đã lưu, báo "Chưa
    lưu: Phiên đăng nhập đã hết…", phân công không đổi; đăng nhập lại đúng người rồi Enter thì lưu qua endpoint phân
    công"""
    bang, _, rows = feedback
    leader, nv = nguoi_dung["leader_vd"], nguoi_dung["staff_vd"]
    truoc = sorted(WaybillAssignment.objects.values_list("record_id", "delivery_id", "version"))
    dang_nhap(trang, leader)
    o = f".mg-cell[data-code='phu_trach_vd'][data-id='{rows[0].pk}']"
    _mo_toi_o(trang, live_server, bang, o)
    trang.dblclick(o)
    trang.wait_for_selector("#vd-assign-cell[data-ready]:not([hidden])", timeout=5_000)
    _dang_xuat_ngam(trang, live_server)
    trang.select_option("#vd-assign-cell select", str(nv.pk))
    trang.wait_for_function(f"""() => {{ const p = document.querySelector('#vd-assign-cell p').textContent;
        return p.includes('Chưa lưu') && p.includes('{HET_PHIEN}'); }}""", timeout=8_000)
    assert trang.evaluate("() => !document.getElementById('vd-assign-cell').hidden")
    assert sorted(WaybillAssignment.objects.values_list("record_id", "delivery_id", "version")) == truoc

    _dang_nhap_ngam(trang, live_server, leader)
    trang.locator("#vd-assign-cell select").press("Enter")
    assert _cho(trang, lambda: WaybillAssignment.objects.filter(record=rows[0], delivery=nv).exists())


def test_het_phien_sua_chung_tu_khong_mat_chu(live_server, trang, dang_nhap, feedback, nguoi_dung, settings,
                                              tmp_path):  # noqa: F811
    """AC-1.1 — TL-18, ADR-053: đang sửa ghi chú chứng từ thì phiên mất: lượt hỏi 8 giây báo hết phiên tiếng Việt ngay
    trong hộp, không "Unexpected token", không xoá form đang gõ; dữ liệu không đổi; đăng nhập lại rồi Lưu thay đổi thì
    lưu được"""
    settings.PAYMENT_DOCUMENTS_ENABLED = True
    settings.STORAGE_DIR = tmp_path
    admin = nguoi_dung["admin"]
    may = Client()
    may.force_login(admin)
    tao = create_document(may, feedback[2][0])
    assert tao.status_code == 200, tao.content
    pk = tao.json()["id"]

    dang_nhap(trang, admin)
    trang.goto(f"{live_server.url}/chung-tu-thanh-toan/")
    trang.locator(f"[data-payment-id='{pk}']").first.click()
    trang.locator(".payment-dialog details summary").click()
    trang.locator(".payment-dialog input[name=note]").fill("Ghi chú đang gõ")
    _dang_xuat_ngam(trang, live_server)
    # Đếm từ sau khi đăng xuất: một lượt hỏi thành công ngay trước đó không được tính
    dem = {"n": 0}
    trang.on("requestfinished", lambda r: dem.__setitem__("n", dem["n"] + 1)
             if r.url.rstrip("/").endswith(f"/chung-tu-thanh-toan/{pk}") else None)
    _dang_hien(trang)
    assert _cho(trang, lambda: dem["n"] >= 1, han=15.0), "lượt hỏi chứng từ không chạy"
    bao = trang.locator(".payment-dialog > .payment-error")
    bao.wait_for(timeout=5_000)
    assert HET_PHIEN in bao.text_content() and "Unexpected token" not in bao.text_content()
    assert trang.locator(".payment-dialog input[name=note]").input_value() == "Ghi chú đang gõ"
    assert PaymentDocument.objects.get(pk=pk).note != "Ghi chú đang gõ"

    _dang_nhap_ngam(trang, live_server, admin)
    trang.locator(".payment-dialog button", has_text="Lưu thay đổi").click()
    assert _cho(trang, lambda: PaymentDocument.objects.get(pk=pk).note == "Ghi chú đang gõ")
