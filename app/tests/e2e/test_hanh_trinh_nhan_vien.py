"""Một hành trình xuyên màn hình của nhân viên, bằng trình duyệt thật.

Các bài kiểm khác cắt hệ thống theo từng mảnh: lưới riêng, lên đơn riêng, hộp lọc
riêng. Hai lỗi chủ dự án báo ngày 19.09.2026 đều **nằm giữa** các mảnh đó — mở hộp
lọc cột thứ hai thì còn mục của cột trước, và lên đơn cho khách cũ thì tên bị giữ
lại. Bài này đi liền mạch một lượt như nhân viên làm thật:

    đăng nhập Vận đơn → mở lưới → gõ thẳng vào ô → tải lại trang kiểm còn dữ liệu
    → mở hộp lọc cột A → gõ tìm → mở hộp lọc cột B → đổi vai sang Sale → lên đơn
    cho khách cũ → kiểm lời nhắc khách

Không thêm tiêu chí nghiệm thu mới: bài xác nhận lại các tiêu chí đã có, nhưng qua
trình duyệt và **nối tiếp nhau**, là chỗ bài kiểm mức đơn vị không với tới.
"""
import pytest

from crm.tests.test_waybill_feedback import feedback  # noqa: F401  (fixture dùng lại)
from forms_builder.models import DataRecord

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]

O_LUOI = ".mg-cell[data-code='thanh_pho']"


@pytest.fixture
def kn_crm(settings):
    """Hành trình này nằm trọn trong dịch vụ KN CRM cổng 8021 — ADR-012."""
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


def _mo_hop_loc(trang, ma_cot):
    trang.evaluate(f"() => document.querySelector(\".mg-filter-icon[data-filter='{ma_cot}']\")?.click()")
    trang.wait_for_selector("#mg-column-filter-body .loc-cot", timeout=15_000)
    return trang.locator("#mg-column-filter-body .loc-cot-meta").inner_text()


def test_hanh_trinh_van_don_roi_sale_len_don(live_server, trinh_duyet, dang_nhap,
                                             kn_crm, feedback, nguoi_dung):  # noqa: F811
    """AC-11.43, AC-11.42, AC-6.10 — Một lượt liền mạch qua trình duyệt: nhân viên Vận đơn
    sửa ô trên lưới và dữ liệu xuống cơ sở dữ liệu; đổi hộp lọc cột thì không sót mục của
    cột trước; nhân viên Sale lên đơn cho khách cũ thì tên tự điền và đổi tên có cảnh báo"""
    bang, _, dong = feedback
    goc = live_server.url
    loi_js = []

    # ── Vai 1: nhân viên Vận đơn sửa dữ liệu trên lưới ──────────────────────
    ctx_vd = trinh_duyet.new_context(viewport={"width": 1366, "height": 800}, locale="vi-VN")
    trang = ctx_vd.new_page()
    trang.set_default_timeout(15_000)
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(trang, nguoi_dung["staff_vd"])

    trang.goto(f"{goc}/bang-tinh/{bang.code}/")
    _cho_luoi_co_du_lieu(trang)

    # Gõ thẳng vào ô như Excel — ADR-033, không còn nút Chế độ Chỉnh sửa
    thanh_pho = "Da Nang E2E"
    trang.locator(O_LUOI).first.click()
    trang.keyboard.type(thanh_pho, delay=30)
    trang.keyboard.press("Enter")
    trang.wait_for_timeout(1_500)          # tự lưu 500 ms cộng thời gian mạng

    # Dữ liệu phải xuống cơ sở dữ liệu thật, không chỉ nằm trên màn hình
    da_luu = [r for r in DataRecord.objects.filter(table=bang) if r.data.get("thanh_pho") == thanh_pho]
    assert da_luu, "gõ ô rồi Enter nhưng không dòng nào mang giá trị mới"

    # …và còn nguyên sau khi tải lại trang
    with trang.expect_response(lambda r: "du-lieu/" in r.url and r.status == 200, timeout=30_000):
        trang.reload(wait_until="domcontentloaded")
    _cho_luoi_co_du_lieu(trang)
    con = trang.evaluate(
        f"() => [...document.querySelectorAll(\"{O_LUOI}\")].some(e => e.textContent.includes({thanh_pho!r}))")
    assert con, "tải lại trang thì mất giá trị vừa gõ"

    # ── Hộp lọc cột: đổi cột không được sót mục của cột trước (TL-49) ───────
    assert "Tên khách" in _mo_hop_loc(trang, "ten_khach")
    o_tim = trang.locator("#mg-column-filter-body input[name=q]")
    o_tim.press_sequentially("Khách", delay=40)      # ô tìm tự gọi lại mảnh lọc
    trang.wait_for_timeout(1_200)

    tieu_de = _mo_hop_loc(trang, "quoc_gia")
    assert "Quốc gia" in tieu_de, f"mở hộp lọc cột khác nhưng vẫn là cột cũ: {tieu_de}"
    o_tich = trang.locator("#mg-column-filter-body input[name='f_quoc_gia__trong']")
    assert o_tich.count() == trang.locator("#mg-column-filter-body .loc-cot-muc input[type=checkbox]").count(), \
        "hộp lọc còn ô tích của cột trước"

    # ── Vai 2: nhân viên Sale lên đơn cho khách đã có (AC-6.10) ─────────────
    ctx_sale = trinh_duyet.new_context(viewport={"width": 1366, "height": 800}, locale="vi-VN")
    don = ctx_sale.new_page()
    don.set_default_timeout(15_000)
    don.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(don, nguoi_dung["staff_sale_1"])

    don.goto(f"{goc}/van-don/len-don/")
    don.wait_for_selector("[name=phone]")
    so = dong[0].data["so_dien_thoai"]
    don.locator("[name=phone]").press_sequentially(so, delay=40)
    don.wait_for_timeout(1_500)
    ten_cu = dong[0].data["ten_khach"]
    assert don.input_value("[name=customer_name]") == ten_cu, "ô Tên khách không tự điền tên đang lưu"

    don.fill("[name=customer_name]", "")
    don.locator("[name=customer_name]").press_sequentially("Nguoi Hoan Toan Khac", delay=30)
    don.wait_for_timeout(1_500)
    nhac = don.locator("#nhac-khach").inner_text()
    assert "sẽ đổi tên khách" in nhac and so in nhac, f"sửa tên mà không cảnh báo: {nhac}"
    assert ten_cu in nhac and "Nguoi Hoan Toan Khac" in nhac, "cảnh báo không nêu đủ tên cũ và tên mới"

    assert not loi_js, f"có lỗi JavaScript trên đường đi: {loi_js}"
    ctx_vd.close()
    ctx_sale.close()
