"""ADR-042 — Báo cáo tổng hợp theo ảnh mẫu, đợt 1: cột đối soát (TT), hai lỗi phân trang và chip Kỳ.
Quy ₫ của đợt 1 đã thay bằng ADR-046 (28.09.2026): không quy đổi, mỗi dòng một loại tiền — AC-46.1, 46.2."""
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


def _theo_tien(result):
    return {tien: dict(zip([c.label for c in result.columns], raw)) for tien, raw in aggregations.total_rows(result)}


def test_tien_giu_nguyen_moi_dong_mot_loai_tien(client, bang_mkt, mkt_source, nguoi_dung):
    """AC-46.1 — Không quy đổi (ADR-046 thay quyết định 1 của ADR-042): hai báo cáo USD và EUR cùng ngày cùng
    người là hai dòng, mỗi dòng một loại tiền với đúng số đã nhập (CPQC 10 USD, 10 EUR); CPO, Giá Mess tính
    trong từng loại tiền; TỔNG CỘNG tách theo loại tiền; tổng chung chỉ giữ số đếm (tiền để trống); ô không
    hậu tố ₫, cột Loại tiền đứng cạnh; chú thích nói rõ không quy đổi; Excel cùng số; nguồn không ánh xạ Loại
    tiền thì không tách, cộng như cũ"""
    A = nguoi_dung["staff_mkt"]
    for thi_truong, tien, cpqc in (("Hoa Kỳ", "USD", "10"), ("Châu Âu", "EUR", "13250000")):
        ban_ghi = _bao_cao(bang_mkt, A, "2026-08-01", "SP1", mess=10, cpqc=cpqc, don=2, doanh_so="100")
        ban_ghi.data |= {"thi_truong": thi_truong, "loai_tien": tien}
        ban_ghi.save()
    ky = dict(start=date(2026, 8, 1), end=date(2026, 8, 1))
    result = activity_service.build(nguoi_dung["manager_mkt"], mkt_source, group="day", **ky)
    assert result.currency_key == "loai_tien" and not result.currency_warning
    assert "không quy đổi" in result.currency_label
    rows = {(item["person_name"], item["loai_tien"]): dict(zip([c.label for c in result.columns],
                                                              aggregations.row_values(item, result)[1]))
            for item in result.rows}
    usd, eur = rows[(employee_code(A), "USD")], rows[(employee_code(A), "EUR")]
    assert usd["CPQC"] == Decimal("10") and eur["CPQC"] == Decimal("13250000")
    assert usd["CPO"] == Decimal("5") and usd["Giá Mess"] == Decimal("1") and usd["DS Chốt"] == 100
    assert usd["Tỉ lệ chốt"] == Decimal(2) / Decimal(10) * 100
    theo_tien = _theo_tien(result)
    assert list(theo_tien) == ["USD", "EUR"]
    assert theo_tien["USD"]["CPQC"] == 10 and theo_tien["EUR"]["CPQC"] == 13250000 and theo_tien["EUR"]["Số Mess"] == 10
    tong = _tong(result)
    assert tong["CPQC"] is None and tong["CPO"] is None and tong["Số Mess"] == 20 and tong["Tỉ lệ chốt"] == 20
    # Chuỗi hiển thị: số đúng như nhập có dấu chấm, không ₫; tỉ lệ có %
    cot = [c.label for c in result.columns]
    client.force_login(nguoi_dung["manager_mkt"])
    query = {"nguon": bang_mkt.code, "tu": "2026-08-01", "den": "2026-08-01"}
    trang = client.get("/bao-cao/tong-hop/", query)
    o = {row["currency"]: dict(zip(cot, row["cells"])) for row in trang.context["rows"] if row["kind"] == "row"}
    assert o["EUR"]["CPQC"] == "13.250.000" and o["USD"]["CPQC"] == "10" and o["USD"]["Tỉ lệ chốt"] == "20%"
    assert all("₫" not in str(v) for dong in o.values() for v in dong.values())
    html = trang.content.decode()
    # Khối toàn kỳ: mỗi loại tiền một dòng TỔNG CỘNG, mã tiền ở ô Loại tiền (vị trí 5) — nhãn dài chỉ còn ở Excel
    tong_ky = [f'class="report-identity id-tien report-identity-edge" data-pos="5">{tien}</td>' for tien in ("USD", "EUR")]
    assert all(o in html for o in tong_ky) and html.index(tong_ky[0]) < html.index(tong_ky[1])
    assert "quy đổi theo tỉ giá" not in html
    # Excel: khối toàn kỳ có hai dòng TỔNG CỘNG, ô Loại tiền riêng, số thô đúng như nhập
    sheet = list(load_workbook(BytesIO(client.get("/bao-cao/tong-hop/xuat/", query).content), data_only=True).active.values)
    tong_xls = [d for d in sheet if d and str(d[0]).startswith("TỔNG CỘNG")]
    assert [d[4] for d in tong_xls] == ["USD", "EUR"]
    assert Decimal(str(tong_xls[1][5 + cot.index("CPQC")])) == Decimal("13250000")
    assert "không quy đổi" in sheet[1][0]
    # Nguồn không ánh xạ Loại tiền: không tách loại tiền, một dòng tổng, không hậu tố ₫
    mkt_source.columns = {k: v for k, v in mkt_source.columns.items() if k != "currency"}
    mkt_source.save()
    result = activity_service.build(nguoi_dung["manager_mkt"], mkt_source, group="day", **ky)
    assert not result.currency_key and _tong(result)["CPQC"] == Decimal("13250010") and not result.currency_label
    assert all(c.suffix != " ₫" for c in result.columns)


def test_dong_chua_co_loai_tien_cong_rieng_va_krw_hien_binh_thuong(bang_mkt, mkt_source, nguoi_dung):
    """AC-46.2 — Dòng trống loại tiền (báo cáo cũ) thành nhóm riêng "Chưa rõ", không cộng vào loại tiền nào,
    có cảnh báo nêu số dòng và cách sửa; KRW (chưa có tỉ giá) hiện như mọi loại tiền khác, không còn cảnh báo
    "chưa quy đổi"; cột đếm vẫn đủ ở từng dòng"""
    A = nguoi_dung["staff_mkt"]
    _bao_cao(bang_mkt, A, "2026-08-01", "SP1", mess=10, cpqc="10", don=2)          # VND (báo cáo MKT, ADR-047)
    _bao_cao(bang_mkt, A, "2026-08-02", "SP1", mess=10, cpqc="7", don=2)
    krw = DataRecord.objects.filter(table=bang_mkt, val_date=date(2026, 8, 2)).get()
    krw.data |= {"thi_truong": "Hàn Quốc", "loai_tien": "KRW"}
    krw.save()
    _bao_cao(bang_mkt, A, "2026-08-03", "SP1", mess=10, cpqc="5", don=2)
    trong = DataRecord.objects.filter(table=bang_mkt, val_date=date(2026, 8, 3)).get()
    trong.data.pop("loai_tien")
    trong.save()
    result = activity_service.build(nguoi_dung["manager_mkt"], mkt_source, group="day", start=date(2026, 8, 1), end=date(2026, 8, 3))
    assert "1 dòng chưa có loại tiền" in result.currency_warning and "Chưa rõ" in result.currency_warning
    assert "quy đổi" not in result.currency_warning
    theo_tien = _theo_tien(result)
    assert list(theo_tien) == ["VND", "KRW", ""]                     # trống đứng cuối
    assert theo_tien["VND"]["CPQC"] == 10 and theo_tien["KRW"]["CPQC"] == 7 and theo_tien[""]["CPQC"] == 5
    assert _tong(result)["Số Mess"] == 30 and _tong(result)["Số đơn"] == 6 and _tong(result)["CPQC"] is None
    dong = _dong(result)
    assert dong[("02.08.2026", employee_code(A))]["CPQC"] == 7 and dong[("03.08.2026", employee_code(A))]["CPQC"] == 5


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
    # Báo cáo MKT bằng tiền Việt, vận đơn bằng CAD (ADR-047): DS Chốt (TT) trống, không quy đổi
    assert a1["Số đơn (TT)"] == 3 and a1["DS Chốt (TT)"] is None and a1["Tỉ lệ chốt (TT)"] == 30
    assert b1["Số đơn (TT)"] == 1 and b1["Tỉ lệ chốt (TT)"] == 5
    assert a2["Số đơn (TT)"] == 1
    tong = _tong(activity_service.build(B, mkt_source, group="day", **ky))
    assert tong["Số đơn (TT)"] == 5 and tong["Tỉ lệ chốt (TT)"] == Decimal(5) / Decimal(40) * 100
    # Lọc sản phẩm SP1: đơn không chi tiết và w2 (SP2) rời khỏi đếm của A
    dong = _dong(activity_service.build(B, mkt_source, group="day", product="SP1", **ky))
    assert dong[("01.08.2026", employee_code(A))]["Số đơn (TT)"] == 1
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
