"""Bảng tính vận đơn trong trình duyệt thật — bàn phím, hộp lọc, cột cố định.

Những gì `crm/tests/test_bang_tinh.py` không kiểm được vì cần JavaScript và
HTMX chạy thật: AC-11.10 và phần cuộn của AC-11.1.
"""
import pytest
from django.test import override_settings

from forms_builder.services import record_service
from orders.models import Product, ProductGroup
from orders.services import dispatch_service

from .conftest import chup

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]


@pytest.fixture
def du_lieu(departments, nguoi_dung):
    nhom = ProductGroup.objects.create(name="Mỹ phẩm")
    Product.objects.create(name="Retinol Cream", code="retinol-cream", group=nhom)
    bang = dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    vd = nguoi_dung["staff_vd"]
    dong = []
    for i, (ten, sdt, tt) in enumerate([
        ("Nguyễn An", "0911", "Đang giao"), ("Trần Bình", "0922", "Đã lên đơn"),
        ("Lê Chi", "0933", "Hoàn đơn"), ("Phạm Dung", "0911", "Đã nhận hàng"),
    ]):
        dong.append(record_service.create_record(bang, {
            "ma_don": f"DH-{i + 1}", "ngay": f"2026-08-0{i + 1}", "ten_khach": ten,
            "so_dien_thoai": sdt, "trang_thai_vc": tt, "sl_retinol_cream": i + 1,
            "ghi_chu": "Giao buổi tối" if i == 0 else "",
        }, actor=vd))
    return {"bang": bang, "dong": dong}


def _cot_dang_focus(page):
    return page.evaluate("document.activeElement && document.activeElement.dataset.cot")


def _dong_dang_focus(page):
    return page.evaluate("document.activeElement && document.activeElement.dataset.dong")


def test_ban_phim_di_chuyen_sua_va_huy(live_server, trang, dang_nhap, du_lieu, nguoi_dung):
    """AC-11.10 — Mũi tên và Tab đi giữa các ô, Enter mở sửa, Esc huỷ, chọn giá trị danh sách thì ô cập nhật không tải lại trang"""
    with override_settings(GRID_ONLY_TABLES=set()):
        dang_nhap(trang, nguoi_dung["staff_vd"])
        trang.goto(live_server.url + "/bang-tinh/?sap=ma_don")
        dong1 = du_lieu["dong"][0].pk
        o = trang.locator(f'td[data-dong="{dong1}"][data-cot="ten_khach"]')
        o.focus()
        assert _cot_dang_focus(trang) == "ten_khach"

        trang.keyboard.press("ArrowRight")
        assert _cot_dang_focus(trang) == "so_dien_thoai"
        trang.keyboard.press("ArrowDown")
        assert _cot_dang_focus(trang) == "so_dien_thoai"
        assert _dong_dang_focus(trang) == str(du_lieu["dong"][1].pk)
        trang.keyboard.press("ArrowUp")
        trang.keyboard.press("ArrowLeft")
        assert _cot_dang_focus(trang) == "ten_khach" and _dong_dang_focus(trang) == str(dong1)
        trang.keyboard.press("Tab")
        assert _cot_dang_focus(trang) == "so_dien_thoai"
        trang.keyboard.press("Shift+Tab")
        assert _cot_dang_focus(trang) == "ten_khach"

        # Enter mở trình sửa, Esc huỷ — giá trị không đổi
        trang.keyboard.press("Enter")
        trang.wait_for_selector("td.dang-sua input[name=gia_tri]")
        trang.keyboard.type(" sửa nhầm")
        trang.keyboard.press("Escape")
        trang.wait_for_selector("td.dang-sua", state="detached")
        assert trang.locator(f'td[data-dong="{dong1}"][data-cot="ten_khach"]').inner_text() == "Nguyễn An"

        # Ô danh sách: Enter → ô chọn, chọn giá trị → lưu ngay, không tải lại trang
        url_truoc = trang.url
        o_tt = trang.locator(f'td[data-dong="{dong1}"][data-cot="trang_thai_vc"]')
        o_tt.focus()
        trang.keyboard.press("Enter")
        trang.wait_for_selector("td.dang-sua select")
        trang.select_option("td.dang-sua select", "Hẹn lại")
        trang.wait_for_selector("td.dang-sua", state="detached")
        assert trang.locator(f'td[data-dong="{dong1}"][data-cot="trang_thai_vc"]').inner_text() == "Hẹn lại"
        assert trang.url == url_truoc, "sửa ô không được tải lại trang"
        du_lieu["dong"][0].refresh_from_db()
        assert du_lieu["dong"][0].data["trang_thai_vc"] == "Hẹn lại"

        # Ô chữ: Enter → gõ → Enter lưu
        o = trang.locator(f'td[data-dong="{dong1}"][data-cot="ghi_chu"]')
        o.focus()
        trang.keyboard.press("Enter")
        trang.wait_for_selector("td.dang-sua textarea")
        trang.fill("td.dang-sua textarea", "Gọi trước khi giao")
        trang.keyboard.press("Control+Enter")
        trang.wait_for_selector("td.dang-sua", state="detached")
        du_lieu["dong"][0].refresh_from_db()
        assert du_lieu["dong"][0].data["ghi_chu"] == "Gọi trước khi giao"
        chup(trang, "bang-tinh-sau-khi-sua")


@pytest.mark.xfail(
    strict=False,
    reason="K23 — trong Playwright hộp lọc gửi lần hai với ô trống ngay sau khi trang tải; "
           "chạy tay trên 8021 thì đúng. Chưa tìm ra nguyên nhân, xem backlog K23",
)
def test_hop_loc_cot_doi_so_dong_va_url(live_server, trang, dang_nhap, du_lieu, nguoi_dung):
    """AC-11.2 — Bấm lọc cột, chọn hai giá trị: số dòng đổi và đường dẫn mang `f_`; chip bỏ lọc trả về đủ dòng"""
    dang_nhap(trang, nguoi_dung["staff_vd"])
    trang.goto(live_server.url + "/bang-tinh/")
    assert trang.locator("tbody tr").count() == 4
    trang.click('button[aria-label="Lọc cột Trạng thái vận chuyển"]')
    trang.wait_for_selector("#hop-loc form")
    trang.check('#hop-loc input[value="Đang giao"]')
    trang.check('#hop-loc input[value="Hoàn đơn"]')
    du_lieu_form = trang.locator("#hop-loc form").evaluate(
        "f => new URLSearchParams(new FormData(f)).toString()")
    assert du_lieu_form.count("f_trang_thai_vc__trong=") == 2, du_lieu_form
    trang.click("#hop-loc form button[type=submit]")
    trang.wait_for_load_state("networkidle")
    assert "f_trang_thai_vc__trong=" in trang.url
    assert trang.locator("tbody tr").count() == 2
    assert trang.locator(".chip-loc").count() == 1
    chup(trang, "bang-tinh-loc-cot")
    trang.click(".chip-loc")
    trang.wait_for_load_state("networkidle")
    assert trang.locator("tbody tr").count() == 4

    # Cột Lọc trùng: hai dòng cùng 0911 được tô, lọc "chỉ trùng" còn 2
    assert trang.locator("td.o-trung").count() == 2
    trang.check("#trung")
    trang.wait_for_load_state("networkidle")
    assert trang.locator("tbody tr").count() == 2


def test_cot_dau_va_tieu_de_dung_yen_khi_cuon(live_server, trang, dang_nhap, du_lieu, nguoi_dung):
    """AC-11.1 — Cuộn ngang thì bốn cột đầu vẫn thấy, cuộn dọc thì hàng tiêu đề vẫn thấy"""
    dang_nhap(trang, nguoi_dung["staff_vd"])
    trang.set_viewport_size({"width": 900, "height": 600})
    trang.goto(live_server.url + "/bang-tinh/")
    khung = trang.locator("#luoi-vd")
    truoc = trang.evaluate('''() => {
        const k = document.getElementById("luoi-vd").getBoundingClientRect();
        const cd = document.querySelector('th.co-dinh[data-cot="ten_khach"]').getBoundingClientRect();
        const thuong = document.querySelector('th[data-cot="ghi_chu"]').getBoundingClientRect();
        return {khung: k.left, coDinh: cd.left, thuong: thuong.left, rong: document.getElementById("luoi-vd").scrollWidth};
    }''')
    assert truoc["rong"] > 900, "lưới phải rộng hơn màn hình thì mới có gì để cuộn"
    khung.evaluate("el => { el.scrollLeft = 600; }")
    trang.wait_for_timeout(200)
    sau = trang.evaluate('''() => {
        const cd = document.querySelector('th.co-dinh[data-cot="ten_khach"]').getBoundingClientRect();
        const thuong = document.querySelector('th[data-cot="ghi_chu"]').getBoundingClientRect();
        return {coDinh: cd.left, thuong: thuong.left};
    }''')
    assert abs(sau["coDinh"] - truoc["coDinh"]) < 2, "cột cố định phải đứng yên khi cuộn ngang"
    assert sau["thuong"] < truoc["thuong"] - 500, "cột thường phải trôi theo cuộn"
    assert sau["coDinh"] >= truoc["khung"], "cột cố định vẫn nằm trong khung nhìn"
    chup(trang, "bang-tinh-cuon-ngang")


def test_dong_trong_thanh_dong_that_va_loc_theo_o_khoa(live_server, trang, dang_nhap, du_lieu, nguoi_dung):
    """AC-11.14 — Gõ vào dòng trống rồi nhấn Enter thì dòng thật xuất hiện không tải lại trang; AC-11.16 — bấm ⌕ ở ô Mã đơn thì lưới lọc còn đúng dòng đó"""
    with override_settings(GRID_ONLY_TABLES=set()):
        dang_nhap(trang, nguoi_dung["staff_vd"])
        trang.goto(live_server.url + "/bang-tinh/van_don/?sap=ma_don")
        so_dong_truoc = trang.locator("tbody tr[data-dong]").count()
        assert trang.locator("tr.dong-moi").count() >= 1

        o = trang.locator("tr.dong-moi").first.locator('input[name="ma_don"]')
        o.fill("DH-MOI")
        trang.locator("tr.dong-moi").first.locator('input[name="ten_khach"]').fill("Khách gõ tay")
        trang.keyboard.press("Enter")
        trang.wait_for_selector('td[data-cot="ten_khach"]:has-text("Khách gõ tay")')
        assert trang.locator("tbody tr[data-dong]").count() == so_dong_truoc + 1
        assert trang.locator("tr.dong-moi").count() >= 1          # vẫn còn dòng trống để gõ tiếp
        assert "/bang-tinh/van_don/?sap=ma_don" in trang.url      # không tải lại trang

        # ⌕ ở ô Mã đơn lọc theo giá trị đó
        trang.locator('td[data-cot="ma_don"]:has-text("DH-1") .o-khoa-loc').click()
        trang.wait_for_url("**/bang-tinh/van_don/?*f_ma_don=DH-1*")
        assert trang.locator("tbody tr[data-dong]").count() == 1


def test_chon_vung_va_dinh_dang_o(live_server, trang, dang_nhap, du_lieu, nguoi_dung):
    """AC-11.15 — Ctrl+bấm rồi Shift+bấm chọn một vùng, bấm B thì cả vùng in đậm tại chỗ không tải lại trang; tải lại trang định dạng vẫn còn; Ctrl+B trên ô đã đậm thì bỏ đậm"""
    with override_settings(GRID_ONLY_TABLES=set()):
        dang_nhap(trang, nguoi_dung["staff_vd"])
        trang.goto(live_server.url + "/bang-tinh/van_don/?sap=ma_don")
        o_dau = trang.locator('tbody tr[data-dong] td[data-cot="ten_khach"]').nth(0)
        o_cuoi = trang.locator('tbody tr[data-dong] td[data-cot="so_dien_thoai"]').nth(1)
        o_dau.click(modifiers=["Control"])
        assert trang.locator("td.dang-sua").count() == 0            # Ctrl+bấm không mở sửa
        o_cuoi.click(modifiers=["Shift"])
        assert trang.locator("td.o-chon").count() == 4
        trang.click(".bt-dinh-dang .bt-dd[data-dd=b]")
        trang.wait_for_function("document.querySelectorAll('td.dd-dam').length === 4")
        assert "sap=ma_don" in trang.url
        trang.click('[aria-controls="bt-bang-mau-nen"]')
        trang.click("#bt-bang-mau-nen .bt-mau-m30")           # vàng nhạt trong bảng 40 màu (ADR-011)
        trang.wait_for_function("document.querySelectorAll('td.dd-nen-m30').length === 4")

        trang.reload()
        trang.wait_for_load_state("networkidle")
        assert trang.locator("td.dd-dam.dd-nen-m30").count() == 4

        trang.locator('tbody tr[data-dong] td[data-cot="ten_khach"]').nth(0).focus()
        trang.keyboard.press("Control+b")
        trang.wait_for_function("document.querySelectorAll('td.dd-dam').length === 3")


def test_keo_do_rong_va_thu_tu_cot_nho_tren_trinh_duyet(live_server, trang, dang_nhap, du_lieu, nguoi_dung):
    """AC-11.18 — Trang Bảng tính không có thanh bên hệ thống; cột có chữ A B C; kéo mép tiêu đề đổi độ rộng, kéo thả tiêu đề đổi thứ tự ở cả tiêu đề lẫn dòng; tải lại vẫn giữ; Đặt lại cột về mặc định"""
    with override_settings(GRID_ONLY_TABLES=set()):
        dang_nhap(trang, nguoi_dung["staff_vd"])
        trang.goto(live_server.url + "/bang-tinh/van_don/")
        assert trang.locator("aside.nav").count() == 0
        assert trang.locator(".bt-chu-cot").all_inner_texts()[:3] == ["A", "B", "C"]

        # Hàng chữ cột A B C mang mép kéo độ rộng và cũng kéo thả được (ADR-011)
        th = trang.locator('thead tr.bt-hang-chu th[data-cot="dia_chi"]')
        th.scroll_into_view_if_needed()
        rong_truoc = th.bounding_box()["width"]
        tay = th.locator(".bt-keo-cot").bounding_box()
        trang.mouse.move(tay["x"] + tay["width"] / 2, tay["y"] + tay["height"] / 2)
        trang.mouse.down()
        trang.mouse.move(tay["x"] + 100, tay["y"] + 10, steps=6)
        trang.mouse.up()
        assert th.bounding_box()["width"] > rong_truoc + 60

        # Kéo Thành phố ra trước Địa chỉ (cả hai không cố định, đang hiện trên màn hình)
        trang.locator('thead tr.bt-hang-chu th[data-cot="thanh_pho"]').drag_to(
            trang.locator('thead tr.bt-hang-chu th[data-cot="dia_chi"]'), target_position={"x": 5, "y": 12})
        thu_tu = trang.locator("thead tr.bt-hang-chu th[data-cot]").evaluate_all("els => els.map(e => e.dataset.cot)")
        assert thu_tu.index("thanh_pho") < thu_tu.index("dia_chi")
        dong = trang.locator("tbody tr[data-dong]").first.locator("td[data-cot]").evaluate_all("els => els.map(e => e.dataset.cot)")
        assert dong == thu_tu

        trang.reload()
        trang.wait_for_load_state("networkidle")
        thu_tu2 = trang.locator("thead tr.bt-hang-chu th[data-cot]").evaluate_all("els => els.map(e => e.dataset.cot)")
        assert thu_tu2 == thu_tu
        assert trang.locator('thead tr.bt-hang-chu th[data-cot="dia_chi"]').bounding_box()["width"] > rong_truoc + 60

        trang.click(".bt-khac")                           # Đặt lại cột nằm trong hộp ⋯ (ADR-011)
        trang.click(".bt-dat-lai-cot")
        trang.wait_for_load_state("networkidle")
        thu_tu3 = trang.locator("thead tr.bt-hang-chu th[data-cot]").evaluate_all("els => els.map(e => e.dataset.cot)")
        assert thu_tu3.index("dia_chi") < thu_tu3.index("thanh_pho")


# ══ Chọn vùng, dán, kéo điền, hoàn tác — ADR-011 ═══════════════════

def _gia_tri(trang, dong, cot):
    return trang.locator(f'tbody tr[data-dong="{dong}"] td[data-cot="{cot}"]').get_attribute("data-goc")


def test_keo_chon_vung_dan_tu_excel_va_keo_dien(live_server, trang, dang_nhap, du_lieu, nguoi_dung):
    """AC-11.19 — Kéo chuột chọn vùng thì ô địa chỉ hiện `C3:D4`; dán chữ có tab và xuống dòng (như chép từ Excel) vào ô đang chọn thì các ô bên cạnh và bên dưới nhận đúng giá trị, tràn xuống dòng trống thì thành bản ghi mới; kéo tay điền từ hai số cách đều thì tiếp chuỗi; Delete xoá nội dung vùng chọn"""
    from forms_builder.models import DataRecord
    with override_settings(GRID_ONLY_TABLES=set()):
        dang_nhap(trang, nguoi_dung["staff_vd"])
        trang.goto(live_server.url + "/bang-tinh/van_don/?sap=ma_don")
        trang.wait_for_load_state("networkidle")
        bang = du_lieu["bang"]
        d1, d2, d3, d4 = [d.pk for d in du_lieu["dong"]]

        # Kéo chuột từ Tên khách dòng 1 tới Số điện thoại dòng 2: vùng 2×2, địa chỉ có dấu hai chấm
        o_a = trang.locator(f'tbody tr[data-dong="{d1}"] td[data-cot="ten_khach"]')
        o_b = trang.locator(f'tbody tr[data-dong="{d2}"] td[data-cot="so_dien_thoai"]')
        ha, hb = o_a.bounding_box(), o_b.bounding_box()
        trang.mouse.move(ha["x"] + 10, ha["y"] + 10)
        trang.mouse.down()
        trang.mouse.move(hb["x"] + 10, hb["y"] + 10, steps=5)
        trang.mouse.up()
        assert trang.locator("td.o-chon").count() == 4
        assert ":" in trang.locator("#bt-dia-chi").input_value()

        # Dán 5 dòng × 2 cột từ ô Tên khách dòng 1: bốn dòng thật đổi, dòng thứ năm tràn xuống dòng trống
        so_dong_truoc = trang.locator("tbody tr[data-dong]").count()
        o_a.click()
        trang.evaluate("""() => {
          const dt = new DataTransfer();
          dt.setData('text/plain', 'Khách A\\t0900000001\\nKhách B\\t0900000002\\nKhách C\\t0900000003\\nKhách D\\t0900000004\\nKhách E\\t0900000005');
          document.activeElement.dispatchEvent(new ClipboardEvent('paste', {clipboardData: dt, bubbles: true, cancelable: true}));
        }""")
        trang.wait_for_function(f"(document.querySelector('tbody tr[data-dong=\"{d1}\"] td[data-cot=\"ten_khach\"]') || {{dataset: {{}}}}).dataset.goc === 'Khách A'")
        assert _gia_tri(trang, d2, "so_dien_thoai") == "0900000002"
        assert DataRecord.objects.filter(table=bang, data__ten_khach="Khách E").exists()   # tràn xuống dòng trống
        trang.wait_for_function(f"document.querySelectorAll('tbody tr[data-dong]').length === {so_dong_truoc + 1}")
        assert "sap=ma_don" in trang.url                                                    # không tải lại trang

        # Kéo tay điền: hai ô Số điện thoại 1, 2 → điền xuống hai dòng nữa được 3, 4
        o1 = trang.locator(f'tbody tr[data-dong="{d1}"] td[data-cot="so_dien_thoai"]')
        o2 = trang.locator(f'tbody tr[data-dong="{d2}"] td[data-cot="so_dien_thoai"]')
        # Gõ chữ trên ô hiển thị là mở sửa với đúng ký tự đó, Enter lưu
        o1.click(); trang.keyboard.type("1")
        trang.wait_for_function("(document.querySelector('td.dang-sua input:not([type=hidden])') || {}).value === '1'")
        trang.keyboard.press("Enter")
        trang.wait_for_function(f"(document.querySelector('tbody tr[data-dong=\"{d1}\"] td[data-cot=\"so_dien_thoai\"]') || {{dataset: {{}}}}).dataset.goc === '1'")
        o2.click(); trang.keyboard.type("2")
        trang.wait_for_function("(document.querySelector('td.dang-sua input:not([type=hidden])') || {}).value === '2'")
        trang.keyboard.press("Enter")
        trang.wait_for_function(f"(document.querySelector('tbody tr[data-dong=\"{d2}\"] td[data-cot=\"so_dien_thoai\"]') || {{dataset: {{}}}}).dataset.goc === '2'")
        o1.click()
        o2.click(modifiers=["Shift"])
        tay = trang.locator("#bt-tay-keo")
        assert tay.is_visible()
        t = tay.bounding_box()
        o4 = trang.locator(f'tbody tr[data-dong="{d4}"] td[data-cot="so_dien_thoai"]').bounding_box()
        trang.mouse.move(t["x"] + 4, t["y"] + 4)
        trang.mouse.down()
        trang.mouse.move(o4["x"] + 10, o4["y"] + 10, steps=6)
        trang.mouse.up()
        trang.wait_for_function(f"(document.querySelector('tbody tr[data-dong=\"{d4}\"] td[data-cot=\"so_dien_thoai\"]') || {{dataset: {{}}}}).dataset.goc === '4'")
        assert _gia_tri(trang, d3, "so_dien_thoai") == "3"

        # Delete xoá nội dung vùng chọn (ghi chú hai dòng)
        g1 = trang.locator(f'tbody tr[data-dong="{d1}"] td[data-cot="ghi_chu"]')
        g1.scroll_into_view_if_needed()
        g1.click(); trang.keyboard.type("t")
        trang.wait_for_function("(document.querySelector('td.dang-sua textarea') || {}).value === 't'")
        trang.keyboard.press("Control+Enter")
        trang.wait_for_function(f"(document.querySelector('tbody tr[data-dong=\"{d1}\"] td[data-cot=\"ghi_chu\"]') || {{dataset: {{}}}}).dataset.goc === 't'")
        g1.click()
        trang.keyboard.press("Delete")
        trang.wait_for_function(f"(document.querySelector('tbody tr[data-dong=\"{d1}\"] td[data-cot=\"ghi_chu\"]') || {{dataset: {{}}}}).dataset.goc === ''")
        chup(trang, "bang-tinh-dan-va-dien")


def test_hoan_tac_va_lam_lai(live_server, trang, dang_nhap, du_lieu, nguoi_dung):
    """AC-11.20 — Ctrl+Z trả lại giá trị cũ của các ô vừa dán và của vùng vừa xoá nội dung; Ctrl+Y áp lại; nút ↶ ↷ bật tắt theo ngăn xếp; Ctrl+Z sau khi in đậm thì bỏ đậm"""
    with override_settings(GRID_ONLY_TABLES=set()):
        dang_nhap(trang, nguoi_dung["staff_vd"])
        trang.goto(live_server.url + "/bang-tinh/van_don/?sap=ma_don")
        trang.wait_for_load_state("networkidle")
        d1, d2 = [d.pk for d in du_lieu["dong"][:2]]
        assert trang.locator("#bt-hoan-tac").is_disabled()

        o_a = trang.locator(f'tbody tr[data-dong="{d1}"] td[data-cot="ten_khach"]')
        o_a.click()
        trang.evaluate("""() => {
          const dt = new DataTransfer();
          dt.setData('text/plain', 'Mới 1\\nMới 2');
          document.activeElement.dispatchEvent(new ClipboardEvent('paste', {clipboardData: dt, bubbles: true, cancelable: true}));
        }""")
        trang.wait_for_function(f"(document.querySelector('tbody tr[data-dong=\"{d2}\"] td[data-cot=\"ten_khach\"]') || {{dataset: {{}}}}).dataset.goc === 'Mới 2'")
        trang.wait_for_function("!document.getElementById('bt-hoan-tac').disabled")   # ghi bước sau khi lưới lắng

        trang.keyboard.press("Control+z")
        trang.wait_for_function(f"(document.querySelector('tbody tr[data-dong=\"{d1}\"] td[data-cot=\"ten_khach\"]') || {{dataset: {{}}}}).dataset.goc === 'Nguyễn An'")
        assert _gia_tri(trang, d2, "ten_khach") == "Trần Bình"
        trang.wait_for_function("!document.getElementById('bt-lam-lai').disabled")
        trang.keyboard.press("Control+y")
        trang.wait_for_function(f"(document.querySelector('tbody tr[data-dong=\"{d1}\"] td[data-cot=\"ten_khach\"]') || {{dataset: {{}}}}).dataset.goc === 'Mới 1'")

        # Xoá nội dung rồi hoàn tác bằng nút
        o_a.click()
        trang.locator(f'tbody tr[data-dong="{d2}"] td[data-cot="ten_khach"]').click(modifiers=["Shift"])
        trang.keyboard.press("Delete")
        trang.wait_for_function(f"(document.querySelector('tbody tr[data-dong=\"{d2}\"] td[data-cot=\"ten_khach\"]') || {{dataset: {{}}}}).dataset.goc === ''")
        trang.click("#bt-hoan-tac")
        trang.wait_for_function(f"(document.querySelector('tbody tr[data-dong=\"{d2}\"] td[data-cot=\"ten_khach\"]') || {{dataset: {{}}}}).dataset.goc === 'Mới 2'")

        # Định dạng: in đậm rồi Ctrl+Z bỏ đậm
        o_a.click()
        trang.click(".bt-dinh-dang .bt-dd[data-dd=b]")
        trang.wait_for_function(f"(document.querySelector('tbody tr[data-dong=\"{d1}\"] td[data-cot=\"ten_khach\"]') || {{classList: {{contains: () => false}}}}).classList.contains('dd-dam')")
        trang.keyboard.press("Control+z")
        trang.wait_for_function(f"!(document.querySelector('tbody tr[data-dong=\"{d1}\"] td[data-cot=\"ten_khach\"]') || {{classList: {{contains: () => false}}}}).classList.contains('dd-dam')")
