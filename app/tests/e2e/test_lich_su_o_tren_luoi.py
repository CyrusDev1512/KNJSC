"""Lịch sử từng ô ngay trên lưới Vận đơn — AC-21.13 (chủ dự án 28.09.2026).

Ô bị người khác sửa trong 24 giờ có dấu góc; chuột phải vào ô thì khung lịch sử hiện ngay cạnh ô
(ai sửa, lúc nào, từ gì thành gì), Esc hay bấm ra ngoài thì đóng. Phải kiểm bằng trình duyệt thật:
dấu góc và vị trí khung là chuyện hiển thị.
"""
import pytest
from django.test import Client

from core.constants import Rank
from crm.tests.test_master_grid import write
from crm.tests.test_waybill_feedback import feedback  # noqa: F401  (fixture dùng lại)

from .conftest import chup
from .ghi_chu_helpers import ghi_chu_nhin_thay

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]


@pytest.mark.parametrize("vai", ["admin", "staff_vd"])
@pytest.mark.parametrize("rong", [1366, 390])
def test_bam_dup_ghi_chu_co_dau_cam_luu_dung_hang(
        live_server, trang, dang_nhap, kn_crm, feedback, nguoi_dung,
        make_user, departments, vai, rong):
    """AC-21.13 — Dấu sửa gần đây không làm hàng bên dưới nhận cú bấm của ô."""
    bang, _, dong = feedback
    khac = make_user("vd_sua_ghi_chu", Rank.STAFF, departments["vd"])
    client = Client()
    client.force_login(khac)
    for i, row in enumerate(dong):
        assert write(client, row, column="ghi_chu", old=row.data.get("ghi_chu"),
                     value=f"Ghi chú mẫu {i}").status_code == 200
    trang.set_viewport_size({"width": rong, "height": 844})
    dang_nhap(trang, nguoi_dung[vai])
    url = f"{live_server.url}/bang-tinh/{bang.code}/"
    trang.goto(url)
    trang.wait_for_selector(".mg-cell[data-id]")
    for i, row in enumerate(dong):
        selector = f".mg-cell[data-code='ghi_chu'][data-id='{row.pk}']"
        trang.wait_for_function("""s => {
            if (document.querySelector(s)) return true;
            document.getElementById('mg-viewport').scrollLeft += 150;
            return false;
        }""", arg=selector, timeout=5000)
        geometry = trang.locator(selector).evaluate("""e => ({
            cell: e.getBoundingClientRect().top,
            row: e.closest('.mg-row').getBoundingClientRect().top
        })""")
        assert abs(geometry["cell"] - geometry["row"]) < 1, geometry
        point = ghi_chu_nhin_thay(trang, row.pk, f"Ghi chú mẫu {i}")
        assert trang.locator(selector).evaluate("e => e.classList.contains('mg-moi-sua')")
        # Chuột thật tại phần ô nhìn thấy, không force-click hoặc phát sự kiện giả.
        trang.mouse.dblclick(point["point"]["x"], point["point"]["y"])
        editor = trang.locator("#mg-editor textarea")
        editor.wait_for(state="visible", timeout=5000)
        assert editor.input_value() == f"Ghi chú mẫu {i}"
        value = f"QA {vai} dòng {i}\nĐã kiểm lưu"
        editor.fill(value)
        with trang.expect_response(lambda r: r.request.method == "POST" and "/bang-tinh/" in r.url):
            editor.press("Control+Enter")
        # Chờ phản hồi lưu và đối chiếu đúng ID, không chỉ nhìn nhãn Đã lưu.
        row.refresh_from_db()
        assert row.data["ghi_chu"] == value
        trang.reload()
        trang.wait_for_selector(".mg-cell[data-id]")
        ghi_chu_nhin_thay(trang, row.pk, value)
    chup(trang, f"ghi-chu-dau-cam-{vai}-{rong}")


@pytest.fixture
def kn_crm(settings):
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.BANGTINH_URL = ""
    return settings


def test_chuot_phai_o_xem_lich_su_va_dau_o_vua_sua(live_server, trang, dang_nhap, kn_crm, feedback,
                                                   nguoi_dung, make_user, departments):  # noqa: F811
    """AC-21.13 — Ô Tên khách vừa bị người khác sửa mang dấu góc; ô chưa ai sửa thì không; chuột phải
    ô đó mở khung lịch sử cạnh ô, có mã người sửa và giá trị trước → sau; Esc đóng"""
    bang, _, dong = feedback
    khac = make_user("vd_khac", Rank.STAFF, departments["vd"])
    c = Client()
    c.force_login(khac)
    assert write(c, dong[0], column="ten_khach", old=dong[0].data["ten_khach"], value="Khách Đã Sửa").status_code == 200

    loi_js = []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(trang, nguoi_dung["staff_vd"])
    trang.goto(f"{live_server.url}/bang-tinh/{bang.code}/")
    o = f".mg-cell[data-code='ten_khach'][data-id='{dong[0].pk}']"
    trang.wait_for_selector(o)
    trang.wait_for_function(f"() => document.querySelector(\"{o}\").textContent.includes('Khách Đã Sửa')")

    assert trang.evaluate(f"() => document.querySelector(\"{o}\").classList.contains('mg-moi-sua')"), \
        "ô vừa bị người khác sửa phải có dấu góc"
    assert not trang.evaluate(
        f"() => document.querySelector(\".mg-cell[data-code='ten_khach'][data-id='{dong[1].pk}']\").classList.contains('mg-moi-sua')")

    trang.click(o, button="right")
    trang.wait_for_selector("#mg-cell-history:not([hidden])", timeout=5_000)
    trang.wait_for_function("() => document.querySelector('#mg-cell-history .mg-history-item')", timeout=5_000)
    khung = trang.text_content("#mg-cell-history")
    assert "Khách Đã Sửa" in khung and dong[0].data["ten_khach"] in khung, khung
    assert "Tên khách" in khung
    vi_tri = trang.evaluate(f"""() => {{ const o = document.querySelector("{o}").getBoundingClientRect();
        const k = document.getElementById('mg-cell-history').getBoundingClientRect();
        return {{phai: k.left >= o.right - 1 && k.left - o.right < 16, ngang_hang: Math.abs(k.top - o.top) < 8,
                 rong: k.width}}; }}""")
    assert vi_tri["phai"] and vi_tri["ngang_hang"], f"khung lịch sử phải nằm bên phải ô, ngang hàng ô: {vi_tri}"
    assert vi_tri["rong"] <= 320, f"khung lịch sử phải gọn, rộng tối đa 320 px: {vi_tri}"
    chup(trang, "lich-su-o-tren-luoi")
    trang.keyboard.press("Escape")
    trang.wait_for_function("() => document.getElementById('mg-cell-history').hidden", timeout=3_000)
    assert not loi_js, loi_js


def test_chuot_phai_len_hop_doc_van_mo_lich_su_o(live_server, trang, dang_nhap, kn_crm, feedback,
                                                 nguoi_dung, make_user, departments):  # noqa: F811
    """AC-21.13 — Ô Ghi chú dài chỉ đọc (Kế toán): click đơn chỉ chọn ô, bấm đúp thì ô phồng to tại chỗ
    (bổ sung ADR-033 26.09); chuột phải lên chính ô phồng vẫn mở lịch sử của ô Ghi chú, không ra menu của
    trình duyệt (chủ dự án 28.09)"""
    bang, _, dong = feedback
    khac = make_user("vd_khac", Rank.STAFF, departments["vd"])
    c = Client()
    c.force_login(khac)
    dai = "Ghi chú rất dài " * 30
    assert write(c, dong[0], column="ghi_chu", old=dong[0].data.get("ghi_chu"), value=dai).status_code == 200

    ke_toan = make_user("ke_toan_xem", Rank.STAFF, departments["kt"])
    dang_nhap(trang, ke_toan)
    trang.goto(f"{live_server.url}/bang-tinh/{bang.code}/")
    o = f".mg-cell[data-code='ghi_chu'][data-id='{dong[0].pk}']"
    trang.wait_for_selector(".mg-cell[data-code='ten_khach']")
    trang.wait_for_function(f"""() => {{ const v = document.getElementById('mg-viewport');
        if (document.querySelector("{o}")) return true; v.scrollLeft += 300; return false; }}""", timeout=10_000)
    trang.locator(o).scroll_into_view_if_needed()
    trang.click(o)
    trang.wait_for_timeout(300)
    assert trang.evaluate("() => document.getElementById('mg-reader').hidden"), "click đơn chỉ chọn ô"
    trang.dblclick(o)
    trang.wait_for_selector("#mg-reader:not([hidden])", timeout=5_000)

    chan = trang.evaluate("""() => { const e = new MouseEvent('contextmenu', {bubbles: true, cancelable: true,
        clientX: 1, clientY: 1}); return !document.querySelector('#mg-reader div').dispatchEvent(e); }""")
    assert chan, "chuột phải lên hộp đọc phải chặn menu trình duyệt"
    trang.wait_for_selector("#mg-cell-history:not([hidden])", timeout=5_000)
    trang.wait_for_function("() => document.querySelector('#mg-cell-history .mg-history-item')", timeout=5_000)
    assert "Ghi chú" in trang.text_content("#mg-cell-history strong")
    assert trang.evaluate("() => document.getElementById('mg-reader').hidden"), "hộp đọc phải nhường chỗ cho lịch sử"


def test_boi_den_trong_luoi_mau_xanh_nhu_excel(live_server, trang, dang_nhap, kn_crm, feedback, nguoi_dung):  # noqa: F811
    """AC-21.13 — Bôi đen chữ trong ô đang nhập của lưới là nền xanh nhạt như Excel/Google Sheets,
    không phải màu vàng ô liu của giao diện chung (chủ dự án 28.09)"""
    bang, _, dong = feedback
    dang_nhap(trang, nguoi_dung["staff_vd"])
    trang.goto(f"{live_server.url}/bang-tinh/{bang.code}/")
    o = f".mg-cell[data-code='ten_khach'][data-id='{dong[0].pk}']"
    trang.wait_for_selector(o)
    trang.click(o)
    trang.keyboard.press("F2")
    trang.wait_for_selector("#mg-editor:not([hidden]) #mg-input :is(input,textarea)")
    mau = trang.evaluate("""() => getComputedStyle(document.querySelector('#mg-input :is(input,textarea)'),
        '::selection').backgroundColor""")
    assert mau == "rgb(180, 213, 254)", mau
    chup(trang, "boi-den-xanh")
