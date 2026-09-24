"""ADR-042 — Báo cáo tổng hợp theo ảnh mẫu, đợt 1: quy ₫ ngay trong truy vấn, cột đối soát (TT),
hai lỗi phân trang và chip Kỳ."""
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

import pytest
from openpyxl import load_workbook

from core.identity import employee_code
from forms_builder.models import DataRecord
from orders.models import WaybillAssignment
from reports import aggregations
from reports.models import ReportSource
from reports.services import activity_service, summary_service
from reports.tests.test_aggregations import bang_mkt  # noqa: F401
from reports.tests.test_mkt_derived_revenue import _bao_cao, mkt_source, van_don  # noqa: F401

pytestmark = pytest.mark.django_db

USD, EUR, CAD = Decimal("25500"), Decimal("28500"), Decimal("17500")


def _tong(result):
    return dict(zip([c.label for c in result.columns], aggregations.total_values(result)))


def _dong(result):
    out = {}
    for item in result.rows:
        nhom, raw = aggregations.row_values(item, result)
        khoa = aggregations.format_group(nhom, result)
        if "person_name" in item:
            khoa = (khoa, item["person_name"])
        out[khoa] = dict(zip([c.label for c in result.columns], raw))
    return out


def test_tien_quy_ve_vnd_truoc_khi_cong(client, bang_mkt, mkt_source, nguoi_dung):
    """AC-42.1 — Mọi cột tiền quy về ₫ theo tỉ giá cố định ngay trong truy vấn rồi mới cộng: hai báo cáo
    USD và EUR cùng ngày cùng người thành một dòng CPQC = 10×25.500 + 10×28.500 ₫; CPO, Giá Mess tính
    trên ₫; dòng Tổng bằng tổng dòng; ô hiện "540.000 ₫", tỉ lệ chốt hiện %; nhãn đơn vị nêu tỉ giá; Excel
    cùng số; nguồn không ánh xạ Loại tiền vẫn cộng thô, không hậu tố"""
    A = nguoi_dung["staff_mkt"]
    # `_bao_cao` ghi thị trường Canada (CAD); đổi hai dòng sang USD và EUR để cộng phải qua tỉ giá
    for thi_truong, tien in (("Hoa Kỳ", "USD"), ("Châu Âu", "EUR")):
        ban_ghi = _bao_cao(bang_mkt, A, "2026-08-01", "SP1", mess=10, cpqc="10", don=2, doanh_so="100")
        ban_ghi.data |= {"thi_truong": thi_truong, "loai_tien": tien}
        ban_ghi.save()
    ky = dict(start=date(2026, 8, 1), end=date(2026, 8, 1))
    result = activity_service.build(nguoi_dung["manager_mkt"], mkt_source, group="day", **ky)
    assert result.converted and result.unconverted == 0
    assert result.currency_label.startswith("VND") and "USD 25500" in result.currency_label and not result.currency_warning
    dong = _dong(result)[("01.08.2026", employee_code(A))]
    assert dong["CPQC"] == 10 * USD + 10 * EUR == Decimal("540000")
    assert dong["Số Mess"] == 20 and dong["CPO"] == Decimal("540000") / 4 and dong["Giá Mess"] == Decimal("540000") / 20
    assert dong["DS Chốt"] == 100 * USD + 100 * EUR and dong["Tỉ lệ chốt"] == Decimal(4) / Decimal(20) * 100
    tong = _tong(result)
    assert tong["CPQC"] == dong["CPQC"] and tong["CPO"] == dong["CPO"]
    # Chuỗi hiển thị: ₫ không lẻ, tỉ lệ có %; cột đếm không hậu tố
    rows = aggregations.finish_rows(list(result.rows), result)
    cot = [c.label for c in result.columns]
    o = dict(zip(cot, rows[0]["cells"]))
    assert o["CPQC"] == "540.000 ₫" and o["CPO"] == "135.000 ₫" and o["Tỉ lệ chốt"] == "20%" and o["Số Mess"] == "20"
    # Excel ghi đúng số ₫ như màn hình
    client.force_login(nguoi_dung["manager_mkt"])
    query = {"nguon": bang_mkt.code, "tu": "2026-08-01", "den": "2026-08-01"}
    sheet = list(load_workbook(BytesIO(client.get("/bao-cao/tong-hop/xuat/", query).content), data_only=True).active.values)
    assert Decimal(str(sheet[-1][cot.index("CPQC") + 4])) == Decimal("540000")
    assert "VND" in sheet[1][0]
    # Nguồn không ánh xạ Loại tiền: cộng thô như trước, không hậu tố ₫
    mkt_source.columns = {k: v for k, v in mkt_source.columns.items() if k != "currency"}
    mkt_source.save()
    result = activity_service.build(nguoi_dung["manager_mkt"], mkt_source, group="day", **ky)
    assert not result.converted and _tong(result)["CPQC"] == Decimal("20") and not result.currency_label
    assert all(c.suffix != " ₫" for c in result.columns)


def test_dong_thieu_ti_gia_khong_vao_tong_va_co_canh_bao(bang_mkt, mkt_source, nguoi_dung):
    """AC-42.2 — Dòng có loại tiền chưa có tỉ giá (KRW) hoặc trống loại tiền: tiền không vào tổng, các
    cột đếm vẫn tính đủ, cảnh báo nêu số dòng và loại tiền thiếu; dòng còn lại vẫn ra số ₫"""
    A = nguoi_dung["staff_mkt"]
    _bao_cao(bang_mkt, A, "2026-08-01", "SP1", mess=10, cpqc="10", don=2)          # CAD
    _bao_cao(bang_mkt, A, "2026-08-02", "SP1", mess=10, cpqc="10", don=2)
    krw = DataRecord.objects.filter(table=bang_mkt, val_date=date(2026, 8, 2)).get()
    krw.data |= {"thi_truong": "Hàn Quốc", "loai_tien": "KRW"}
    krw.save()
    _bao_cao(bang_mkt, A, "2026-08-03", "SP1", mess=10, cpqc="10", don=2)
    trong = DataRecord.objects.filter(table=bang_mkt, val_date=date(2026, 8, 3)).get()
    trong.data.pop("loai_tien")
    trong.save()
    result = activity_service.build(nguoi_dung["manager_mkt"], mkt_source, group="day", start=date(2026, 8, 1), end=date(2026, 8, 3))
    assert result.unconverted == 2
    assert "2 dòng" in result.currency_warning and "KRW" in result.currency_warning and "trống" in result.currency_warning
    assert result.currency_label.startswith("VND")
    tong = _tong(result)
    assert tong["CPQC"] == 10 * CAD and tong["Số Mess"] == 30 and tong["Số đơn"] == 6
    dong = _dong(result)
    assert dong[("01.08.2026", employee_code(A))]["CPQC"] == 10 * CAD
    assert dong[("02.08.2026", employee_code(A))]["CPQC"] is None and dong[("02.08.2026", employee_code(A))]["Số Mess"] == 10
    assert dong[("03.08.2026", employee_code(A))]["CPQC"] is None


def test_so_don_tt_va_ti_le_chot_tt_theo_marketer_va_ngay(bang_mkt, mkt_source, van_don, nguoi_dung):
    """AC-42.3 — Số đơn (TT) = số vận đơn marketer phụ trách theo ngày lên đơn, kể cả đơn không có chi tiết
    sản phẩm (đơn đó không góp DS Chốt (TT)); Tỉ lệ chốt (TT) = Số đơn (TT) ÷ Số Mess; lọc sản phẩm chỉ
    đếm đơn có sản phẩm đó; đơn chưa phân công không vào; theo nhân viên cộng cả kỳ; Staff chỉ thấy của mình,
    không có đơn thì 0 chứ không trống"""
    A, B = van_don["A"], van_don["B"]
    _bao_cao(bang_mkt, A, "2026-08-01", "SP1", mess=10)
    _bao_cao(bang_mkt, B, "2026-08-01", "SP2", mess=20)
    _bao_cao(bang_mkt, A, "2026-08-02", "SP1", mess=10)
    # Đơn không có chi tiết (ADR-036) của A ngày 01.08: đếm vào Số đơn (TT), không có tiền
    khong_chi_tiet = DataRecord.objects.create(
        table=van_don["table"], department=van_don["table"].department, created_by=nguoi_dung["admin"],
        val_date=date(2026, 8, 1), data={"ngay": "2026-08-01", "quoc_gia": "Canada", "loai_tien": "CAD", "so_tien_tt": "50"})
    WaybillAssignment.objects.create(record=khong_chi_tiet, marketing=A)
    ky = dict(start=date(2026, 8, 1), end=date(2026, 8, 2))
    dong = _dong(activity_service.build(B, mkt_source, group="day", **ky))
    a1, b1, a2 = dong[("01.08.2026", employee_code(A))], dong[("01.08.2026", employee_code(B))], dong[("02.08.2026", employee_code(A))]
    assert a1["Số đơn (TT)"] == 3 and a1["DS Chốt (TT)"] == 100 * CAD and a1["Tỉ lệ chốt (TT)"] == 30
    assert b1["Số đơn (TT)"] == 1 and b1["DS Chốt (TT)"] == 200 * CAD and b1["Tỉ lệ chốt (TT)"] == 5
    assert a2["Số đơn (TT)"] == 1 and a2["DS Chốt (TT)"] == 25 * CAD
    tong = _tong(activity_service.build(B, mkt_source, group="day", **ky))
    assert tong["Số đơn (TT)"] == 5 and tong["Tỉ lệ chốt (TT)"] == Decimal(5) / Decimal(40) * 100
    # Lọc sản phẩm SP1: đơn không chi tiết và w2 (SP2) rời khỏi đếm của A
    dong = _dong(activity_service.build(B, mkt_source, group="day", product="SP1", **ky))
    assert dong[("01.08.2026", employee_code(A))]["Số đơn (TT)"] == 1 and dong[("01.08.2026", employee_code(A))]["DS Chốt (TT)"] == 60 * CAD
    # Theo nhân viên: cả kỳ
    dong = _dong(activity_service.build(B, mkt_source, group="person", **ky))
    assert dong[employee_code(A)]["Số đơn (TT)"] == 4 and dong[employee_code(B)]["Số đơn (TT)"] == 1
    # Staff chỉ thấy của mình; ngày không có đơn hiện 0 chứ không trống
    _bao_cao(bang_mkt, A, "2026-08-03", "SP1", mess=10)
    dong = _dong(activity_service.build(A, mkt_source, group="day", start=date(2026, 8, 1), end=date(2026, 8, 3)))
    assert set(dong) == {("01.08.2026", employee_code(A)), ("02.08.2026", employee_code(A)), ("03.08.2026", employee_code(A))}
    assert dong[("03.08.2026", employee_code(A))]["Số đơn (TT)"] == 0 and dong[("03.08.2026", employee_code(A))]["DS Chốt (TT)"] is None


def test_ngan_sach_truy_van_nguon_mkt_that(client, bang_mkt, mkt_source, van_don, nguoi_dung, django_assert_max_num_queries):
    """AC-42.4 — Nguồn Marketing cấu hình thật (quy ₫ + đối soát vận đơn) vẫn trong ngân sách 10 truy vấn
    ở cách xem Tổng hợp và Theo nhân viên"""
    A = van_don["A"]
    _bao_cao(bang_mkt, A, "2026-08-01", "SP1")
    client.force_login(nguoi_dung["manager_mkt"])
    for nhom in ("day", "person"):
        params = {"nguon": bang_mkt.code, "nhom": nhom, "tu": "2026-08-01", "den": "2026-08-02"}
        client.get("/bao-cao/tong-hop/", params)
        with django_assert_max_num_queries(10):
            assert client.get("/bao-cao/tong-hop/", params).status_code == 200


def test_sang_trang_va_chip_ky(client, bang_mkt, mkt_source, nguoi_dung):
    """AC-42.5 — Liên kết phân trang không mang `trang`/`moi_trang` cũ nên từ trang 2 sang trang khác đi
    đúng; chip Kỳ chỉ có dấu × khi kỳ khác mặc định, còn gửi đúng kỳ mặc định thì không có × và không tính
    là đang lọc"""
    A = nguoi_dung["staff_mkt"]
    for i in range(30):
        _bao_cao(bang_mkt, A, (date(2026, 8, 1) + timedelta(days=i)).isoformat(), "SP1")
    client.force_login(nguoi_dung["manager_mkt"])
    query = {"nguon": bang_mkt.code, "tu": "2026-08-01", "den": "2026-08-30", "trang": "2", "moi_trang": "25"}
    r = client.get("/bao-cao/tong-hop/", query)
    assert r.status_code == 200 and r.context["page_obj"].number == 2
    assert "trang=" not in r.context["qs_loc"] and "moi_trang=" not in r.context["qs_loc"]
    html = r.content.decode()
    assert '?trang=1&moi_trang=25&amp;nguon=' in html      # link trang 1 không kéo theo trang=2 cũ
    assert r.context["chips"][0]["url"] and r.context["filters_active"] == 1     # kỳ tháng 8 khác mặc định
    tu, den = summary_service.default_range()
    r0 = client.get("/bao-cao/tong-hop/", {"nguon": bang_mkt.code, "tu": tu.isoformat(), "den": den.isoformat()})
    assert r0.context["chips"][0]["url"] == "" and r0.context["filters_active"] == 0
    assert 'class="chip-clear"' not in r0.content.decode()
