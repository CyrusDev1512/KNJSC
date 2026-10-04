"""Xem trước chỉ số trên form Nộp báo cáo ngày — AC-43.6 (khách hàng yêu cầu, chủ dự án chốt mockup 02.10.2026).

Marketing gõ Số Mess, CPQC, Số đơn, Doanh số thì CPO, Giá Mess, CPQC/Doanh số, AOV, Tỉ lệ chốt hiện ngay, trước
khi nộp. Chỉ là xem trước: máy chủ vẫn tự tính và lưu cột tính sẵn khi nộp (ADR-006).
"""
import pytest

from forms_builder.meaning import FieldType
from forms_builder.models import ColumnDef, ComputeOp
from reports.services import daily_service
from reports.tests.test_aggregations import bang_mkt  # noqa: F401 — fixture của mkt_source
from reports.tests.test_mkt_derived_revenue import mkt_source  # noqa: F401

pytestmark = pytest.mark.django_db


@pytest.fixture
def du_chi_so(mkt_source):
    """Bảng MKT cấu hình thật (`configure_erp_reports`): CPO, Giá Mess, CPQC/Doanh số, AOV bốn số lẻ; Tỉ lệ
    chốt và Tích thử (phép nhân) có sẵn trong `bang_mkt`."""
    return mkt_source.table


def test_don_vi_cua_tung_chi_so(du_chi_so):
    """AC-43.6 — Đơn vị và số lẻ trên thẻ xem trước khai ở một chỗ, suy từ kiểu cột của công thức: tiền ÷ số đếm
    là tiền theo loại tiền của dòng (CPO, Giá Mess, AOV), hai số lẻ như Báo cáo tổng hợp dù cột lưu bốn; phần
    trăm là "%" hai số lẻ (Tỉ lệ chốt); tiền ÷ tiền không đơn vị, giữ bốn số lẻ của cột (CPQC/Doanh số); số
    đếm × số đếm không đơn vị"""
    the = {c.code: (unit, le) for c, unit, le in daily_service.preview_columns(du_chi_so)}
    assert the["cpo"] == the["gia_mess"] == the["aov"] == ("tien", 2)
    assert the["ti_le_chot"] == ("phan-tram", 2)
    assert the["cpqc_doanh_so"] == ("", 4) and the["tich_thu"] == ("", 0)


def test_form_co_khoi_xem_truoc(client, du_chi_so, mkt_source, nguoi_dung, django_assert_max_num_queries):
    """AC-43.6 — Form Nộp báo cáo có khối "Xem trước chỉ số": mỗi cột tính sẵn một thẻ mang công thức đọc thẳng
    từ cột (trái, phép, phải, số lẻ, đơn vị) và dòng công thức nhỏ; ô số mang mã cột đích (`data-cot`) để JS gom
    giá trị; không còn dòng chip tĩnh "Hệ thống tự tính khi nộp"; khối không thêm truy vấn theo số thẻ"""
    form = mkt_source.table.forms.get()
    client.force_login(nguoi_dung["staff_mkt"])
    url = f"/bao-cao/?bieu_mau={form.code}"
    client.get(url)
    with django_assert_max_num_queries(40) as dem:
        html = client.get(url).content.decode()
    assert "Xem trước chỉ số" in html and "Hệ thống tự tính khi nộp" not in html
    assert 'data-ma="cpo" data-trai="cpqc" data-phai="so_don" data-phep="divide" data-le="2" data-don-vi="tien"' in html
    assert 'data-trai="so_don" data-phai="so_mess" data-phep="percent" data-le="2" data-don-vi="phan-tram"' in html
    assert 'data-trai="cpqc" data-phai="doanh_so" data-phep="divide" data-le="4" data-don-vi=""' in html
    assert html.count('class="cs"') == mkt_source.table.computed_columns().count() == 6
    assert "cpqc ÷ so_don" in html
    for ma in ("so_mess", "cpqc", "so_don", "doanh_so"):
        assert f'data-cot="{ma}"' in html
    so_lenh = len(dem.captured_queries)
    # Thêm một cột tính nữa: số truy vấn không đổi
    ColumnDef.objects.create(table=du_chi_so, name="Thử", code="thu", field_type=FieldType.DECIMAL, order=99,
                             is_computed=True, compute_op=ComputeOp.DIVIDE, compute_left="so_don",
                             compute_right="so_mess", compute_decimals=2)
    with django_assert_max_num_queries(so_lenh):
        client.get(url)
