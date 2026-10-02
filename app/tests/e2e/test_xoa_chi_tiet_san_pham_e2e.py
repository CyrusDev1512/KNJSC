"""Delete xoá được ô Sản phẩm, Bỏ dòng xoá được dòng cuối — bấm thật trên lưới Vận đơn (chủ dự án 02.10.2026).

Bài máy chủ ở `crm/tests/test_xoa_chi_tiet_san_pham.py`; bài này kiểm phần chỉ trình duyệt mới thấy: hộp hỏi
lại khi Delete trúng ô tổng, ba lựa chọn, và nút Bỏ dòng ở dòng cuối của hộp Chi tiết.
"""
import pytest

from crm.tests.test_waybill_new import order, setup  # noqa: F401  (fixture dùng lại)
from orders.models import WaybillItem

from .conftest import chup

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]


@pytest.fixture
def kn_crm(settings):
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.BANGTINH_URL = ""
    return settings


def _o(dong, ma):
    return f".mg-cell[data-code='{ma}'][data-id='{dong.pk}']"


def _con(dong):
    return WaybillItem.objects.filter(record=dong, deleted_at__isnull=True).count()


def test_delete_o_san_pham_hoi_lai_roi_bo_chi_tiet(live_server, trang, dang_nhap, kn_crm, setup,  # noqa: F811
                                                   nguoi_dung):
    """AC-36.9 — Bôi đen từ ô Sản phẩm tới ô Số lượng rồi Delete: hiện hộp "Xoá cả sản phẩm của đơn?";
    Huỷ thì không đổi gì; "Bỏ chi tiết và xoá" thì ô Sản phẩm trống trên lưới, chi tiết bị bỏ, ô thường
    trong vùng (Chi tiết số nhà) cũng trống; không lỗi JS"""
    dong = order(setup, nguoi_dung["staff_sale_1"]).record
    dong.data["dia_chi"] = "12 Phố Thử"
    dong.save()
    loi_js = []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(trang, nguoi_dung["staff_vd"])
    trang.goto(f"{live_server.url}/bang-tinh/van_don/")
    trang.wait_for_selector(_o(dong, "san_pham"))
    assert "Sản phẩm thử" in trang.locator(_o(dong, "san_pham")).text_content()

    trang.click(_o(dong, "san_pham"))
    trang.keyboard.press("Delete")
    trang.wait_for_selector("#mg-bo-chi-tiet[open]", timeout=5_000)
    assert trang.locator("#mg-bo-chi-tiet-so").text_content() == "1"
    assert trang.locator("#mg-bo-chi-tiet [data-choice='normal']").is_hidden()   # không có ô thường
    trang.click("#mg-bo-chi-tiet .vd-actions [data-choice='cancel']")
    trang.wait_for_selector("#mg-bo-chi-tiet:not([open])", state="attached")
    assert _con(dong) == 2

    trang.click(_o(dong, "san_pham"))
    trang.wait_for_function(f"""() => {{ const v = document.getElementById('mg-viewport');
        if (document.querySelector("{_o(dong, 'so_luong')}")) return true; v.scrollLeft += 200; return false; }}""",
        timeout=10_000)
    trang.locator(_o(dong, "so_luong")).scroll_into_view_if_needed()
    trang.click(_o(dong, "so_luong"), modifiers=["Shift"])
    trang.keyboard.press("Delete")
    trang.wait_for_selector("#mg-bo-chi-tiet[open]", timeout=5_000)
    assert trang.locator("#mg-bo-chi-tiet [data-choice='normal']").is_visible()
    chup(trang, "xoa-chi-tiet-hoi-lai")
    trang.click("#mg-bo-chi-tiet [data-choice='details']")
    trang.wait_for_function(f"""() => {{ const o = document.querySelector("{_o(dong, 'san_pham')}");
        return o && !o.textContent.includes('Sản phẩm thử'); }}""", timeout=8_000)
    trang.wait_for_function("() => document.getElementById('bt-trang-thai').textContent === 'Đã lưu'",
                            timeout=8_000)
    dong.refresh_from_db()
    assert _con(dong) == 0 and dong.data.get("gia_tien") in (None, "") and dong.data.get("dia_chi") in (None, "")
    assert "bỏ chi tiết sản phẩm của 1 dòng" in trang.locator("#mg-message").text_content()
    assert not loi_js, loi_js


def test_bo_dong_cuoi_trong_hop_chi_tiet(live_server, trang, dang_nhap, kn_crm, setup, nguoi_dung):  # noqa: F811
    """AC-36.10 — Hộp Chi tiết hai dòng: Bỏ dòng hai lần thì bảng không còn dòng nào, nút Thêm dòng vẫn còn và
    thêm lại được một dòng; bỏ dòng đó rồi Lưu → đơn không còn sản phẩm, ô
    Sản phẩm trên lưới trống; mở lại hộp thì vẫn có sẵn một ô chọn sản phẩm như trước"""
    dong = order(setup, nguoi_dung["staff_sale_1"]).record
    loi_js = []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(trang, nguoi_dung["staff_vd"])
    trang.goto(f"{live_server.url}/bang-tinh/van_don/")
    trang.wait_for_selector(_o(dong, "san_pham"))
    trang.dblclick(_o(dong, "san_pham"))
    trang.wait_for_selector("#vd-detail-body [data-remove-item]", timeout=8_000)
    chon = "#vd-detail-body .vd-items select[name='product']"
    assert trang.locator(chon).count() == 2
    trang.locator("#vd-detail-body [data-remove-item]").first.click()
    trang.locator("#vd-detail-body [data-remove-item]").first.click()
    assert trang.locator(chon).count() == 0
    chup(trang, "bo-dong-cuoi")
    trang.click("#vd-detail-body [data-add-item]")                   # thêm lại được
    assert trang.locator(chon).count() == 1 and trang.eval_on_selector(chon, "s => s.value") == ""
    trang.locator("#vd-detail-body [data-remove-item]").first.click()
    trang.click("#vd-detail-body button[type='submit']")
    trang.wait_for_function("() => !document.getElementById('vd-detail').open", timeout=8_000)
    trang.wait_for_function(f"""() => {{ const o = document.querySelector("{_o(dong, 'san_pham')}");
        return o && !o.textContent.includes('Sản phẩm thử'); }}""", timeout=8_000)
    assert _con(dong) == 0
    trang.dblclick(_o(dong, "san_pham"))                             # mở lại: vẫn có sẵn ô chọn sản phẩm
    trang.wait_for_selector(chon, timeout=8_000)
    assert trang.locator(chon).count() == 1 and trang.eval_on_selector(chon, "s => s.value") == ""
    assert not loi_js, loi_js


# ---- Đóng vai người dùng: thao tác dễ sai (kiểm toàn diện trước khi gộp Staging, 02.10.2026) ----

def _mo_luoi(trang, live_server, dang_nhap, ai, dong):
    loi_js = []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(trang, ai)
    trang.goto(f"{live_server.url}/bang-tinh/van_don/")
    trang.wait_for_selector(_o(dong, "san_pham"))
    return loi_js


def _cho_luu(trang):
    trang.wait_for_function("() => document.getElementById('bt-trang-thai').textContent === 'Đã lưu'",
                            timeout=8_000)


def test_delete_roi_enter_hay_esc_khong_mat_gi(live_server, trang, dang_nhap, kn_crm, setup,  # noqa: F811
                                               nguoi_dung):
    """AC-36.9 — Người dùng ấn Delete rồi Enter theo thói quen, hay Esc, hay bấm ×: con trỏ đứng ở Huỷ nên
    không bỏ gì; chi tiết và chữ Sản phẩm giữ nguyên"""
    dong = order(setup, nguoi_dung["staff_sale_1"]).record
    loi_js = _mo_luoi(trang, live_server, dang_nhap, nguoi_dung["staff_vd"], dong)
    for dong_hop in ("Enter", "Escape", "×"):
        trang.click(_o(dong, "san_pham"))
        trang.keyboard.press("Delete")
        trang.wait_for_selector("#mg-bo-chi-tiet[open]", timeout=5_000)
        if dong_hop == "×":
            trang.click("#mg-bo-chi-tiet .mg-close")
        else:
            trang.keyboard.press(dong_hop)
        trang.wait_for_selector("#mg-bo-chi-tiet:not([open])", state="attached")
        trang.wait_for_timeout(300)
        assert _con(dong) == 2, dong_hop
    assert "Sản phẩm thử" in trang.locator(_o(dong, "san_pham")).text_content()
    assert not loi_js, loi_js


def test_chi_xoa_o_thuong_va_ctrl_z(live_server, trang, dang_nhap, kn_crm, setup, nguoi_dung):  # noqa: F811
    """AC-36.9 — Bôi đen Sản phẩm → Chi tiết số nhà, Delete, chọn "Chỉ xoá ô thường": sản phẩm giữ, ô thường
    trống; Ctrl+Z trả lại ô thường"""
    dong = order(setup, nguoi_dung["staff_sale_1"]).record
    dong.data["dia_chi"] = "12 Phố Thử"
    dong.save()
    loi_js = _mo_luoi(trang, live_server, dang_nhap, nguoi_dung["staff_vd"], dong)
    hoi = []
    # Vùng có ô Quốc gia: xoá Quốc gia của đơn có tiền thì lưới hỏi "Loại tiền sẽ trống" (ADR-031) — bấm OK
    trang.on("dialog", lambda d: (hoi.append(d.message), d.accept()))
    trang.click(_o(dong, "san_pham"))
    trang.wait_for_function(f"""() => {{ const v = document.getElementById('mg-viewport');
        if (document.querySelector("{_o(dong, 'dia_chi')}")) return true; v.scrollLeft += 200; return false; }}""",
        timeout=10_000)
    trang.click(_o(dong, "dia_chi"), modifiers=["Shift"])
    trang.keyboard.press("Delete")
    trang.wait_for_selector("#mg-bo-chi-tiet[open]", timeout=5_000)
    trang.click("#mg-bo-chi-tiet [data-choice='normal']")
    _cho_luu(trang)
    dong.refresh_from_db()
    assert _con(dong) == 2 and dong.data.get("dia_chi") in (None, "") and dong.data["san_pham"]
    trang.keyboard.press("Control+z")
    trang.wait_for_function(f"""() => document.querySelector("{_o(dong, 'dia_chi')}")?.textContent
        .includes('12 Phố Thử')""", timeout=8_000)
    _cho_luu(trang)
    dong.refresh_from_db()
    assert dong.data.get("dia_chi") == "12 Phố Thử" and _con(dong) == 2
    assert not loi_js, loi_js


def test_nhieu_dong_mot_lan_va_dong_da_trong(live_server, trang, dang_nhap, kn_crm, setup,  # noqa: F811
                                             nguoi_dung):
    """AC-36.9 — Bôi đen cột Sản phẩm qua ba dòng, một dòng đã trống từ trước: hộp hỏi đếm đúng 2 dòng; bỏ xong
    cả ba đều trống, không lỗi"""
    from orders.services import waybill_service
    dongs = [order(setup, nguoi_dung["staff_sale_1"]).record for _ in range(3)]
    waybill_service.clear_items(nguoi_dung["staff_vd"], setup[1],
                                [{"id": dongs[1].pk, "column": "san_pham", "old": dongs[1].data["san_pham"]}])
    loi_js = _mo_luoi(trang, live_server, dang_nhap, nguoi_dung["staff_vd"], dongs[0])
    ids = trang.eval_on_selector_all(".mg-cell[data-code='san_pham']", "os => os.map(o => +o.dataset.id)")
    dau, cuoi = ids[0], ids[-1]
    trang.click(f".mg-cell[data-code='san_pham'][data-id='{dau}']")
    trang.click(f".mg-cell[data-code='san_pham'][data-id='{cuoi}']", modifiers=["Shift"])
    trang.keyboard.press("Delete")
    trang.wait_for_selector("#mg-bo-chi-tiet[open]", timeout=5_000)
    assert trang.locator("#mg-bo-chi-tiet-so").text_content() == "2"
    trang.click("#mg-bo-chi-tiet [data-choice='details']")
    trang.wait_for_function("() => document.getElementById('mg-message').textContent.includes('2 dòng')",
                            timeout=8_000)
    assert [_con(d) for d in dongs] == [0, 0, 0]
    assert not loi_js, loi_js


def test_nguoi_khac_vua_sua_thi_bao_khong_bo(live_server, trang, dang_nhap, kn_crm, setup,  # noqa: F811
                                            nguoi_dung):
    """AC-36.9 — Đang mở hộp hỏi thì người khác sửa đơn (ô Sản phẩm đổi): bấm "Bỏ chi tiết và xoá" → báo "vừa
    được người khác sửa", không bỏ gì"""
    dong = order(setup, nguoi_dung["staff_sale_1"]).record
    loi_js = _mo_luoi(trang, live_server, dang_nhap, nguoi_dung["staff_vd"], dong)
    trang.click(_o(dong, "san_pham"))
    trang.keyboard.press("Delete")
    trang.wait_for_selector("#mg-bo-chi-tiet[open]", timeout=5_000)
    dong.data["san_pham"] = "Người khác vừa đổi"
    dong.save()
    trang.click("#mg-bo-chi-tiet [data-choice='details']")
    trang.wait_for_function("() => document.getElementById('mg-message').textContent.includes('người khác')",
                            timeout=8_000)
    assert _con(dong) == 2
    assert not loi_js, loi_js


def test_bo_xong_mo_chi_tiet_chon_lai_san_pham(live_server, trang, dang_nhap, kn_crm, setup,  # noqa: F811
                                               nguoi_dung):
    """AC-36.10 — Bỏ chi tiết xong, bấm đúp ô Sản phẩm: hộp có sẵn một dòng chọn trống như cũ; lỡ bấm Lưu ngay
    thì báo "chưa chọn sản phẩm", không đổi gì; chọn sản phẩm, đơn giá rồi Lưu → ô Sản phẩm hiện lại"""
    from orders.services import waybill_service
    dong = order(setup, nguoi_dung["staff_sale_1"]).record
    waybill_service.clear_items(nguoi_dung["staff_vd"], setup[1],
                                [{"id": dong.pk, "column": "san_pham", "old": dong.data["san_pham"]}])
    loi_js = _mo_luoi(trang, live_server, dang_nhap, nguoi_dung["staff_vd"], dong)
    trang.dblclick(_o(dong, "san_pham"))
    chon = "#vd-detail-body .vd-items select[name='product']"
    trang.wait_for_selector(chon, timeout=8_000)
    assert trang.locator(chon).count() == 1
    trang.click("#vd-detail-body button[type='submit']")
    trang.wait_for_selector("#vd-detail-body .vd-error", timeout=8_000)
    assert "chưa chọn sản phẩm" in trang.locator("#vd-detail-body .vd-error").text_content()
    assert _con(dong) == 0
    trang.select_option(chon, "new-0")
    trang.fill("#vd-detail-body input[name='unit_price']", "12.50")
    trang.click("#vd-detail-body button[type='submit']")
    trang.wait_for_function("() => !document.getElementById('vd-detail').open", timeout=8_000)
    trang.wait_for_function(f"""() => document.querySelector("{_o(dong, 'san_pham')}")?.textContent
        .includes('Sản phẩm thử')""", timeout=8_000)
    dong.refresh_from_db()
    assert _con(dong) == 1 and dong.data["gia_tien"] == "12.50"
    assert not loi_js, loi_js


def test_don_nhap_tep_lo_bam_luu_khong_mat_chu(live_server, trang, dang_nhap, kn_crm, setup,  # noqa: F811
                                               nguoi_dung):
    """AC-36.10 — Đơn nhập từ tệp (ô Sản phẩm chỉ là chữ, không chi tiết): mở Chi tiết, lỡ bấm Lưu → báo lỗi,
    chữ và tổng tiền giữ; Bỏ dòng rồi Lưu → ô Sản phẩm trống"""
    from django.utils import timezone
    dong = order(setup, nguoi_dung["staff_sale_1"]).record
    WaybillItem.objects.filter(record=dong).update(deleted_at=timezone.now())
    dong.data["san_pham"] = "Retinol Cream ×2 + Retinol Serum ×3"
    dong.save()
    loi_js = _mo_luoi(trang, live_server, dang_nhap, nguoi_dung["staff_vd"], dong)
    trang.dblclick(_o(dong, "san_pham"))
    trang.wait_for_selector("#vd-detail-body [data-remove-item]", timeout=8_000)
    trang.click("#vd-detail-body button[type='submit']")
    trang.wait_for_selector("#vd-detail-body .vd-error", timeout=8_000)
    dong.refresh_from_db()
    assert dong.data["san_pham"] == "Retinol Cream ×2 + Retinol Serum ×3" and dong.data["gia_tien"] == "40.40"
    trang.locator("#vd-detail-body [data-remove-item]").first.click()
    trang.click("#vd-detail-body button[type='submit']")
    trang.wait_for_function("() => !document.getElementById('vd-detail').open", timeout=8_000)
    trang.wait_for_function(f"""() => !document.querySelector("{_o(dong, 'san_pham')}")?.textContent
        .includes('Retinol')""", timeout=8_000)
    dong.refresh_from_db()
    assert dong.data.get("san_pham") in (None, "")
    assert not loi_js, loi_js


def test_len_don_khong_doi(live_server, trang, dang_nhap, kn_crm, setup, nguoi_dung):  # noqa: F811
    """AC-36.10 — Lên đơn giữ như cũ: Bỏ dòng ở dòng duy nhất không làm mất dòng; Thêm dòng thêm được; lên đơn
    hai sản phẩm lưu đúng"""
    loi_js = []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(trang, nguoi_dung["staff_sale_1"])
    trang.goto(f"{live_server.url}/van-don/len-don/")
    chon = ".vd-items select[name='product']"
    trang.wait_for_selector(chon)
    trang.click("[data-remove-item]")
    assert trang.locator(chon).count() == 1
    trang.click("[data-add-item]")
    assert trang.locator(chon).count() == 2
    trang.locator(chon).nth(0).select_option("new-0")
    trang.locator(chon).nth(1).select_option("new-1")
    trang.fill("[name='phone']", "0901234599")
    trang.fill("[name='customer_name']", "Khách thử lên đơn")
    from orders.constants import Market, PaymentMethod
    trang.select_option("[name='market']", Market.US)
    trang.select_option("[name='payment_method']", PaymentMethod.ZELLE)
    trang.locator("input[name='unit_price']").nth(0).fill("10.00")
    trang.locator("input[name='unit_price']").nth(1).fill("5.00")
    trang.click("#vd-entry .vd-actions button[type='submit']")
    trang.wait_for_selector(".vd-success, .vd-error", timeout=8_000)
    assert trang.locator(".vd-error").count() == 0, trang.locator(".vd-error").text_content()
    from orders.models import Order
    don = Order.objects.latest("pk")
    assert don.lines.count() == 2 and _con(don.record) == 2
    assert not loi_js, loi_js
