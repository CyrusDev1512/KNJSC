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
    """AC-36.10 — Hộp Chi tiết hai dòng: Bỏ dòng hai lần thì bảng không còn dòng nào, hiện "Đơn chưa có sản
    phẩm", nút Thêm dòng vẫn còn và thêm lại được một dòng; bỏ dòng đó rồi Lưu → đơn không còn sản phẩm, ô
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
    assert trang.locator("#vd-detail-body [data-items-empty]").is_hidden()
    trang.locator("#vd-detail-body [data-remove-item]").first.click()
    trang.locator("#vd-detail-body [data-remove-item]").first.click()
    assert trang.locator(chon).count() == 0
    assert trang.locator("#vd-detail-body [data-items-empty]").is_visible()
    chup(trang, "bo-dong-cuoi")
    trang.click("#vd-detail-body [data-add-item]")                   # thêm lại được
    assert trang.locator(chon).count() == 1 and trang.eval_on_selector(chon, "s => s.value") == ""
    assert trang.locator("#vd-detail-body [data-items-empty]").is_hidden()
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
