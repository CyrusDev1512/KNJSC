"""ADR-046 — Ô số trên form Nộp báo cáo ngày viết theo cách Việt Nam, bằng Chromium thật.

Chạy khi có Playwright và Chromium; thiếu thì tự bỏ qua.
"""
from decimal import Decimal

import pytest

from core.money import parse_money
from forms_builder.models import DataRecord
from orders.models import Product
from reports.models import DailyReport
from reports.tests.test_aggregations import bang_mkt  # noqa: F401
from reports.tests.test_bo_cuc_bao_cao_e2e import _mo, trinh_duyet_moi  # noqa: F401
from reports.tests.test_mkt_derived_revenue import mkt_source  # noqa: F401

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
    Product.objects.get_or_create(code="sp1", defaults={"name": "SP1"})
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
        page.select_option(_o(form, "thi_truong"), "Canada")
        san_pham = _o(form, "san_pham")
        if page.evaluate(f"document.querySelector('{san_pham}').tagName") == "SELECT":
            page.select_option(san_pham, "SP1")
        else:
            page.fill(san_pham, "SP1")
        with page.expect_navigation():
            page.click('button[form="bm-bao-cao"]')
        bao_cao = DailyReport.objects.get()
        du_lieu = DataRecord.objects.get(pk=bao_cao.record_id).data
        assert Decimal(str(du_lieu["cpqc"])) == Decimal("13250000") and du_lieu["so_mess"] == 1234
        assert Decimal(str(du_lieu["doanh_so"])) == Decimal("25000000") and du_lieu["loai_tien"] == "CAD"
    finally:
        ctx.close()

