"""Admin sửa lần nộp ngay trên Báo cáo tổng hợp bằng Chromium thật (ADR-050, chủ dự án duyệt mockup 10.10.2026).

Bấm ✎ mở hộp sửa, gõ số tự chèn dấu chấm, Lưu → dòng, TỔNG CỘNG của ngày và của toàn kỳ đổi tại chỗ, không tải lại
trang; người khác lưu trước → 409, hộp nạp số mới, ô bị đổi tô vàng; Escape chỉ đóng hộp; điện thoại hộp chiếm cả
màn hình. Chạy khi có Chromium (`playwright install chromium`); thiếu thì tự bỏ qua.
"""
import pytest

from reports.services import daily_service
from reports.tests.test_admin_sua_tong_hop import _ma_truong, mkt  # noqa: F401 — fixture
from reports.tests.test_aggregations import bang_mkt  # noqa: F401 — fixture
from reports.tests.test_bo_cuc_bao_cao_e2e import _mo, trinh_duyet_moi  # noqa: F401 — fixture
from reports.tests.test_mkt_derived_revenue import mkt_source  # noqa: F401 — fixture
from tests.e2e.conftest import chup

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]

HOP_MO = "()=>document.getElementById('report-sua-hop').open"
HOP_DONG = "()=>!document.getElementById('report-sua-hop').open"


def _url(mkt):
    q = mkt["nguon"]
    return f"/bao-cao/tong-hop/?nguon={q['nguon']}&tu={q['tu']}&den={q['den']}"


def _so(text):
    return int(text.replace(".", "").strip())


def _loi_console(page):
    """Lỗi JS và lỗi tải trên console. Phản hồi 409 của lượt lưu gặp xung đột là đúng thiết kế (Chromium vẫn in
    "Failed to load resource … 409") nên không tính."""
    loi = []
    page.on("console", lambda m: loi.append(m.text) if m.type == "error" and "fonts.g" not in m.text
            and "status of 409" not in m.text else None)
    page.on("pageerror", lambda e: loi.append(str(e)))
    return loi


def test_sua_trong_hop_bang_doi_tai_cho(live_server, trinh_duyet_moi, mkt, nguoi_dung):  # noqa: F811
    """AC-50.9 — Admin bấm ✎ ở một dòng lần nộp: hộp mở, con trỏ ở ô Số Mess, gõ 1250 thành 1.250 và Xem trước chỉ
    số tính ngay; Lưu → hộp đóng, báo "Đã lưu", ô của dòng, TỔNG CỘNG của ngày và TỔNG CỘNG toàn kỳ đổi đúng mà không
    tải lại trang, dòng sáng lên, focus về ✎; Escape chỉ đóng hộp (vẫn ở chế độ mở rộng ERP); Manager lưu trước thì
    Admin bấm Lưu nhận 409: hộp nạp Số đơn mới, tô vàng ô đó, Lưu lại được; không lỗi console"""
    bao_cao, bm = mkt["lan"][0], mkt["bm"]
    o_mess, o_don = _ma_truong(bm, "so_mess"), _ma_truong(bm, "so_don")
    ctx, page = _mo(trinh_duyet_moi, live_server, nguoi_dung["admin"], 1366, 768, _url(mkt))
    loi = _loi_console(page)
    try:
        dong = page.locator(f'tr[data-lan-nop="{bao_cao.pk}"]')
        ngay = page.locator(f'section.report-block-day[data-ngay="{bao_cao.report_date:%Y-%m-%d}"]')
        o_dong = lambda: dong.locator("td:not(.report-identity)").first.inner_text()  # noqa: E731 — Số Mess
        tong_ngay = lambda: ngay.locator("tr.report-total td:not(.report-identity)").first.inner_text()  # noqa: E731
        tong_ky = lambda: page.locator("section.report-block-period tr.report-total td:not(.report-identity)").first.inner_text()  # noqa: E731
        truoc_dong, truoc_ngay, truoc_ky = _so(o_dong()), _so(tong_ngay()), _so(tong_ky())
        assert truoc_dong == 120
        page.evaluate("()=>{window.__moc=1}")

        dong.locator(".report-sua").click()
        page.wait_for_function(HOP_MO)
        assert page.evaluate("()=>document.activeElement.name") == o_mess
        o = page.locator(f"#report-sua-hop [name='{o_mess}']")
        o.press("Control+a")
        o.press_sequentially("1250", delay=10)
        assert o.input_value() == "1.250"
        assert "chưa đủ số" not in page.locator("#report-sua-hop #xem-truoc-chi-so").inner_text()
        chup(page, "admin-sua-hop-1366")
        page.click("#report-sua-hop button[type=submit]")
        page.wait_for_function(HOP_DONG)
        page.wait_for_function(f"()=>document.querySelector('tr[data-lan-nop=\"{bao_cao.pk}\"].report-vua-sua')")
        assert _so(o_dong()) == 1250
        assert _so(tong_ngay()) == truoc_ngay + 1130 and _so(tong_ky()) == truoc_ky + 1130
        assert page.evaluate("()=>window.__moc===1"), "không tải lại trang"
        assert "Đã lưu" in page.locator(".report-sua-bao").inner_text()
        assert page.evaluate(f"()=>document.activeElement.closest('tr')?.dataset.lanNop") == str(bao_cao.pk)
        chup(page, "admin-sua-da-luu-1366")

        dong.locator(".report-sua").click()
        page.wait_for_function(HOP_MO)
        page.keyboard.press("Escape")
        page.wait_for_function(HOP_DONG)
        assert page.evaluate("()=>document.documentElement.classList.contains('sp-erp-immersive')")

        # Người khác lưu trước khi Admin bấm Lưu: 409, hộp nạp số mới, ô bị đổi tô vàng, Lưu lại được
        dong.locator(".report-sua").click()
        page.wait_for_function(HOP_MO)
        bao_cao.record.refresh_from_db()
        daily_service.amend(bao_cao, {o_don: "77"}, version=bao_cao.record.updated_at.isoformat(),
                            actor=nguoi_dung["manager_mkt"])
        o = page.locator(f"#report-sua-hop [name='{o_mess}']")
        o.press("Control+a")
        o.press_sequentially("1300", delay=10)
        page.click("#report-sua-hop button[type=submit]")
        page.wait_for_selector("#report-sua-hop .bao-cho")
        assert page.locator(f"#report-sua-hop [name='{o_don}']").input_value() == "77"
        assert page.locator("#report-sua-hop .truong.vua-doi").count() == 1
        assert page.locator(f"#report-sua-hop [name='{o_mess}']").input_value() == "1.250", "số vừa gõ chưa lưu bị bỏ"
        chup(page, "admin-sua-xung-dot-1366")
        page.click("#report-sua-hop button[type=submit]")
        page.wait_for_function(HOP_DONG)
        bao_cao.record.refresh_from_db()
        assert bao_cao.record.data["so_don"] == 77 and bao_cao.record.data["so_mess"] == 1250
        assert not loi, loi
    finally:
        ctx.close()


def test_hop_sua_tren_dien_thoai(live_server, trinh_duyet_moi, mkt, nguoi_dung):  # noqa: F811
    """AC-50.10 — Điện thoại 390 px: nút ✎ nằm trong ô STT đứng yên, hộp sửa chiếm cả màn hình, trang không cuộn
    ngang; Huỷ đóng hộp, không lỗi console"""
    ctx, page = _mo(trinh_duyet_moi, live_server, nguoi_dung["admin"], 390, 844, _url(mkt))
    loi = _loi_console(page)
    try:
        assert page.evaluate("()=>document.scrollingElement.scrollWidth-innerWidth") <= 0
        page.locator(f'tr[data-lan-nop="{mkt["lan"][0].pk}"] .report-sua').click()
        page.wait_for_function(HOP_MO)
        khung = page.evaluate("()=>{const r=document.getElementById('report-sua-hop').getBoundingClientRect();"
                              "return [Math.round(r.width),Math.round(r.height)]}")
        assert khung == [390, 844]
        chup(page, "admin-sua-hop-390")
        page.locator("#report-sua-hop .report-sua-chan [data-dong]").click()
        page.wait_for_function(HOP_DONG)
        assert not loi, loi
    finally:
        ctx.close()
