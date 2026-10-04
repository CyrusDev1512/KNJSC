"""ADR-046 — Ô số trên form Nộp báo cáo ngày viết theo cách Việt Nam, bằng Chromium thật.

Chạy khi có Playwright và Chromium; thiếu thì tự bỏ qua.
"""
from decimal import Decimal

import pytest

from core.money import parse_money
from forms_builder.models import DataRecord
from reports.models import DailyReport
from reports.tests.test_aggregations import bang_mkt  # noqa: F401
from reports.tests.test_bo_cuc_bao_cao_e2e import _mo, trinh_duyet_moi  # noqa: F401
from reports.tests.test_mkt_derived_revenue import mkt_source  # noqa: F401
from reports.tests.test_xem_truoc_chi_so import du_chi_so  # noqa: F401

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]


def _o(form, ma_cot):
    """Id của ô nhập ứng với cột đích trên form (`o-<mã trường>`)."""
    for f in form.ordered_fields():
        cot = getattr(getattr(f, "link", None), "column", None)
        if cot is not None and cot.code == ma_cot:
            return "#o-" + f.field.code
    raise AssertionError(ma_cot)


def test_o_so_tu_chen_dau_cham_va_may_chu_nhan_dung(live_server, trinh_duyet_moi, bang_mkt, mkt_source, nguoi_dung):
    """AC-46.10 — Ô số trên form Nộp báo cáo: gõ toàn chữ số thì dấu chấm ngăn nghìn tự chèn ngay khi gõ
    (13250000 → 13.250.000, con trỏ vẫn ở cuối); tự gõ "." hay "," thì để nguyên tới khi rời ô rồi viết lại theo
    luật `parse_money` — "8000.50" thành "8.000,5" chứ không thành 800.050 (dấu chấm tự chèn trước đó bị bỏ khi
    người dùng tự gõ dấu); gõ kiểu Việt Nam "13.250.000" giữ đúng số; gõ thêm vào phần lẻ không gộp vào phần nguyên; dán "13 250 000" thành "13.250.000";
    ô số nguyên không có phần lẻ; nộp thật thì máy chủ lưu đúng 13250000, không quy đổi"""
    form = mkt_source.table.forms.get()
    ctx, page = _mo(trinh_duyet_moi, live_server, nguoi_dung["staff_mkt"], 1280, 900, f"/bao-cao/?bieu_mau={form.code}")
    try:
        cpqc, mess = _o(form, "cpqc"), _o(form, "so_mess")
        assert page.get_attribute(cpqc, "data-kieu") == "money" and page.get_attribute(cpqc, "inputmode") == "decimal"
        assert page.get_attribute(mess, "data-kieu") == "integer" and page.get_attribute(mess, "inputmode") == "numeric"
        # Gõ toàn chữ số: chấm tự chèn khi gõ, con trỏ ở cuối để gõ tiếp
        page.click(cpqc)
        page.keyboard.type("13250000")
        assert page.input_value(cpqc) == "13.250.000"
        assert page.evaluate(f"document.querySelector('{cpqc}').selectionStart") == len("13.250.000")
        # Xoá lùi một chữ số: nhóm lại ngay
        page.keyboard.press("Backspace")
        assert page.input_value(cpqc) == "1.325.000"
        # Tự gõ dấu chấm kiểu Mỹ: giữ nguyên khi gõ, rời ô thì viết lại đúng như máy chủ sẽ đọc
        page.fill(cpqc, "")
        page.keyboard.type("8000.50")
        assert page.input_value(cpqc) == "8000.50"
        page.keyboard.press("Tab")
        assert page.input_value(cpqc) == "8.000,5"
        assert parse_money(page.input_value(cpqc)) == Decimal("8000.5")
        # Gõ kiểu Việt Nam có dấu chấm ngăn nghìn: giữ đúng số
        page.fill(cpqc, "")
        page.keyboard.type("13.250.000")
        page.keyboard.press("Tab")
        assert page.input_value(cpqc) == "13.250.000"
        # Ô đã có phần lẻ, gõ thêm chữ số vào phần lẻ: không bị gộp vào phần nguyên
        page.fill(cpqc, "")
        page.keyboard.type("1234,5")
        page.keyboard.press("Tab")
        page.click(cpqc)
        page.keyboard.press("End")
        page.keyboard.type("0")
        assert page.input_value(cpqc) == "1.234,50"
        # Dán số có khoảng trắng
        page.fill(cpqc, "")
        page.evaluate(f"""() => {{
            const o = document.querySelector('{cpqc}');
            o.focus(); o.value = '13 250 000';
            o.dispatchEvent(new InputEvent('input', {{bubbles: true, inputType: 'insertFromPaste'}}));
        }}""")
        assert page.input_value(cpqc) == "13.250.000"
        # Số nguyên: gõ 1234 thành 1.234; gõ dấu phẩy thì rời ô bỏ dấu như máy chủ (12,5 → 125)
        page.click(mess)
        page.keyboard.type("12,5")
        page.keyboard.press("Tab")
        assert page.input_value(mess) == "125"
        page.fill(mess, "")
        page.click(mess)
        page.keyboard.type("1234")
        assert page.input_value(mess) == "1.234"
        # Nộp thật: máy chủ nhận đúng số
        for ma, gia_tri in (("so_don", "12"), ("doanh_so", "25000000")):
            page.click(_o(form, ma))
            page.keyboard.type(gia_tri)
        assert page.input_value(_o(form, "doanh_so")) == "25.000.000"
        # Form MKT không còn Thị trường, Sản phẩm (ADR-048): nộp chỉ với các ô số
        with page.expect_navigation():
            page.click('button[form="bm-bao-cao"]')
        bao_cao = DailyReport.objects.get()
        du_lieu = DataRecord.objects.get(pk=bao_cao.record_id).data
        assert Decimal(str(du_lieu["cpqc"])) == Decimal("13250000") and du_lieu["so_mess"] == 1234
        assert Decimal(str(du_lieu["doanh_so"])) == Decimal("25000000") and du_lieu["loai_tien"] == "VND"
    finally:
        ctx.close()



def test_xem_truoc_chi_so_khi_go(live_server, trinh_duyet_moi, du_chi_so, mkt_source, nguoi_dung):
    """AC-43.6 — Gõ Số Mess 120, CPQC 13.250.000, Số đơn 8, Doanh số 24.000.000 thì thẻ xem trước hiện ngay CPO
    "1.656.250 VND", Giá Mess "110.416,67 VND" (hai số lẻ như Báo cáo tổng hợp), CPQC/Doanh số "0,5521", AOV
    "3.000.000 VND", Tỉ lệ chốt "6,67 %"; xoá Số đơn thì CPO, AOV về "—"; Số đơn 0 thì báo chia cho 0; hậu tố là
    VND dù form MKT không còn ô Loại tiền (báo cáo MKT bằng tiền Việt, ADR-047, ADR-048); thẻ có ô vừa sửa sáng viền;
    nộp thật thì máy chủ lưu đúng số đã xem trước; không lỗi JavaScript"""
    form = mkt_source.table.forms.get()
    ctx, page = _mo(trinh_duyet_moi, live_server, nguoi_dung["staff_mkt"], 1280, 900, f"/bao-cao/?bieu_mau={form.code}")
    loi = []
    page.on("pageerror", lambda e: loi.append(str(e)))

    def the(ma):
        return page.locator(f'.cs[data-ma="{ma}"] .gt').inner_text().replace("\n", " ").replace("\xa0", " ").strip()

    try:
        assert the("cpo").startswith("—")
        for ma, gia_tri in (("so_mess", "120"), ("cpqc", "13250000"), ("so_don", "8"), ("doanh_so", "24000000")):
            page.click(_o(form, ma))
            page.keyboard.type(gia_tri)
        assert the("cpo") == "1.656.250 VND"
        assert the("gia_mess") == "110.416,67 VND"
        assert the("cpqc_doanh_so") == "0,5521"
        assert the("aov") == "3.000.000 VND"
        assert the("ti_le_chot") == "6,67 %"
        assert "vua" in page.get_attribute('.cs[data-ma="aov"]', "class")       # vừa gõ Doanh số
        assert "vua" not in page.get_attribute('.cs[data-ma="ti_le_chot"]', "class")
        page.fill(_o(form, "so_don"), "")
        page.dispatch_event(_o(form, "so_don"), "input")
        assert the("cpo").startswith("—") and the("aov").startswith("—") and the("gia_mess") == "110.416,67 VND"
        page.click(_o(form, "so_don"))
        page.keyboard.type("0")
        assert "chia cho 0" in the("cpo")
        page.fill(_o(form, "so_don"), "")
        page.click(_o(form, "so_don"))
        page.keyboard.type("8")
        assert the("cpo") == "1.656.250 VND"
        with page.expect_navigation():
            page.click('button[form="bm-bao-cao"]')
        du_lieu = DataRecord.objects.get(pk=DailyReport.objects.get().record_id).data
        # Máy chủ lưu bốn số lẻ; làm tròn về số lẻ của thẻ thì trùng số đã xem trước
        luu = {ma: Decimal(str(du_lieu[ma])) for ma in ("cpo", "gia_mess", "cpqc_doanh_so", "aov", "ti_le_chot")}
        assert luu == {"cpo": Decimal("1656250"), "gia_mess": Decimal("110416.6667"),
                       "cpqc_doanh_so": Decimal("0.5521"), "aov": Decimal("3000000"), "ti_le_chot": Decimal("6.67")}
        assert loi == []
    finally:
        ctx.close()


def test_form_mkt_khong_bon_o_van_hien_vnd_va_nop_duoc(live_server, trinh_duyet_moi, bang_mkt, mkt_source, nguoi_dung):
    """AC-48.5 — Form Nộp báo cáo Marketing trên trình duyệt không còn ô Sản phẩm, Thị trường, Tệp khách hàng, Loại
    tiền; gõ CPQC và Số đơn thì thẻ CPO hiện hậu tố "VND"; bấm Nộp chỉ với các ô số thì lưu được, dòng mang Loại
    tiền VND; không lỗi JavaScript"""
    form = mkt_source.table.forms.get()
    ctx, page = _mo(trinh_duyet_moi, live_server, nguoi_dung["staff_mkt"], 1280, 900, f"/bao-cao/?bieu_mau={form.code}")
    loi = []
    page.on("pageerror", lambda e: loi.append(str(e)))
    try:
        for ma in ("san_pham", "thi_truong", "tep_khach_hang", "loai_tien"):
            assert page.locator(f'[name$="{ma}"]').count() == 0, ma
        assert page.locator("[data-report-currency]").count() == 0
        for ma, gia_tri in (("so_mess", "50"), ("cpqc", "2000000"), ("so_don", "4"), ("doanh_so", "9000000")):
            page.click(_o(form, ma))
            page.keyboard.type(gia_tri)
        gia = page.locator('.cs[data-ma="cpo"] .gt').inner_text().replace("\n", " ").replace("\xa0", " ").strip()
        assert gia == "500.000 VND"
        with page.expect_navigation():
            page.click('button[form="bm-bao-cao"]')
        du_lieu = DataRecord.objects.get(pk=DailyReport.objects.get().record_id).data
        assert du_lieu["loai_tien"] == "VND" and Decimal(str(du_lieu["cpqc"])) == Decimal("2000000")
        assert loi == []
    finally:
        ctx.close()
