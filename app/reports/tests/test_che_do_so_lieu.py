"""ADR-046 — Chế độ số liệu: không quy đổi, mỗi dòng một loại tiền, Cộng theo ngày / Từng lần nộp trong bộ lọc.

Chủ dự án 28.09.2026: "nhân viên báo cáo số tiền là 8000 thì hiển thị là 8000, kể cả báo cáo 2 lần trong 1 ngày
thì lần 1 8000 lần 2 7000 thì cứ hiển thị ra như thế" — duyệt mockup "Chế độ xem số liệu" cùng ngày.
"""
from datetime import date, datetime, time
from decimal import Decimal
from io import BytesIO

import pytest
from django.utils import timezone
from openpyxl import load_workbook

from core.identity import employee_code
from core.money import parse_money
from forms_builder.models import DataRecord
from orders.models import WaybillAssignment, WaybillItem
from reports import aggregations, screen
from reports.services import activity_service, summary_service, threshold_service
from reports.tests.test_activity import delivery_source  # noqa: F401
from reports.tests.test_aggregations import bang_mkt  # noqa: F401
from reports.tests.test_mkt_derived_revenue import _bao_cao, mkt_source, van_don  # noqa: F401
from reports.tests.test_mkt_excel import marketing_scope  # noqa: F401

pytestmark = pytest.mark.django_db

NGAY = date(2026, 8, 1)


def _luc(gio, phut, ngay=NGAY):
    """Giờ Việt Nam của ngày báo cáo → thời điểm có múi giờ để ghi `created_at`."""
    return timezone.make_aware(datetime.combine(ngay, time(gio, phut)))


def _nop(bang, nguoi, gio, phut, *, cpqc, mess=10, don=2, thi_truong="Canada", tien="CAD", ngay=NGAY):
    """Một lần nộp báo cáo lúc `gio:phut` (giờ Việt Nam) — đặt lại `created_at` để thứ tự lần nộp xác định."""
    ban_ghi = _bao_cao(bang, nguoi, ngay.isoformat(), "SP1", mess=mess, cpqc=cpqc, don=don)
    ban_ghi.data |= {"thi_truong": thi_truong, "loai_tien": tien}
    ban_ghi.save()
    DataRecord.objects.filter(pk=ban_ghi.pk).update(created_at=_luc(gio, phut, ngay))
    return ban_ghi


@pytest.fixture
def bon_lan_nop(bang_mkt, van_don):
    """A nộp ba lần ngày 01.08 (09:12 CAD 8.000, 10:00 USD 500, 16:40 CAD 7.000); B một lần (CAD 3.000)."""
    A, B = van_don["A"], van_don["B"]
    return {
        "A": A, "B": B,
        "a1": _nop(bang_mkt, A, 9, 12, cpqc="8000"),
        "a2": _nop(bang_mkt, A, 10, 0, cpqc="500", thi_truong="Hoa Kỳ", tien="USD"),
        "a3": _nop(bang_mkt, A, 16, 40, cpqc="7000"),
        "b1": _nop(bang_mkt, B, 11, 5, cpqc="3000"),
    }


def _o(row, cot, nhan):
    return str(row["cells"][cot.index(nhan)])


def _dinh_danh(row):
    return {c["code"]: v for c, v in row["identity"]}


def test_che_do_cong_theo_ngay_va_tung_lan_nop(client, bang_mkt, mkt_source, bon_lan_nop, nguoi_dung):
    """AC-46.3 — Màn hình luôn Từng lần nộp (không còn ô Chế độ, 01.10.2026): mỗi lần nộp một dòng, số đúng như
    nhập (8.000 và 7.000), cột Lần nộp "Lần N · giờ" đếm theo giờ nộp trong ngày của từng người, khối toàn kỳ
    vẫn đứng đầu và cộng theo người cùng loại tiền, TỔNG CỘNG ngày theo loại tiền; Gộp là một khối mọi lần nộp.
    Tầng service vẫn có Cộng theo ngày (Tổng quan dùng): mỗi người mỗi ngày một dòng cho mỗi loại tiền, nộp
    nhiều lần thì cộng cùng loại tiền (8.000 + 7.000 = 15.000 CAD, USD dòng riêng)"""
    A, B = bon_lan_nop["A"], bon_lan_nop["B"]
    ma_a, ma_b = employee_code(A), employee_code(B)
    client.force_login(B)                                 # manager_mkt thấy cả bộ phận
    ky = {"nguon": bang_mkt.code, "tu": "2026-08-01", "den": "2026-08-01"}

    # Tầng service, Cộng theo ngày
    cong = activity_service.build(B, mkt_source, start=NGAY, end=NGAY)
    cot = [c.label for c in cong.columns]
    assert cong.mode == "cong"
    dong = {(i["person_name"], i["loai_tien"]): dict(zip(cot, aggregations.row_values(i, cong)[1])) for i in cong.rows}
    assert set(dong) == {(ma_a, "CAD"), (ma_a, "USD"), (ma_b, "CAD")}
    assert dong[(ma_a, "CAD")]["CPQC"] == 15000 and dong[(ma_a, "USD")]["CPQC"] == 500

    # Màn hình: Từng lần nộp
    r = client.get("/bao-cao/tong-hop/", ky)
    result = r.context["result"]
    assert r.status_code == 200 and result.mode == "tung-lan" and r.context["params"]["mode"] == "tung-lan"
    ky_khoi, ngay = r.context["blocks"]
    assert ky_khoi["kind"] == "period" and ngay["kind"] == "day"
    assert [c["code"] for c in ngay["identity_columns"]] == ["stt", "team", "person", "leader", "lan", "tien"]
    hang = [(row["person"], _dinh_danh(row)["lan"], row["currency"], _o(row, cot, "CPQC")) for row in ngay["rows"]]
    mong = sorted([(ma_a, "Lần 1 · 09:12", "CAD", "8.000"), (ma_a, "Lần 2 · 10:00", "USD", "500"),
                   (ma_a, "Lần 3 · 16:40", "CAD", "7.000"), (ma_b, "Lần 1 · 11:05", "CAD", "3.000")],
                  key=lambda h: (h[0], h[1]))
    assert hang == mong
    assert [row["stt"] for row in ngay["rows"]] == [1, 2, 3, 4]
    # TỔNG CỘNG của ngày vẫn tách theo loại tiền (câu hỏi 3 của mockup: giữ)
    assert [(t["label"], _o(t, cot, "CPQC")) for t in ngay["total_rows"]] == [
        ("TỔNG CỘNG · USD", "500"), ("TỔNG CỘNG · CAD", "18.000")]
    # Khối toàn kỳ vẫn cộng theo người và loại tiền
    assert {(row["person"], row["currency"]): _o(row, cot, "CPQC") for row in ky_khoi["rows"]}[(ma_a, "CAD")] == "15.000"
    # (TT): hai lần nộp CAD của A dùng chung khoá (ngày, A, CAD) → "—"; lần USD và của B có số riêng
    assert result.derived_shared == frozenset({(NGAY, ma_a, "CAD")})
    tt = {(_dinh_danh(row)["lan"], row["person"]): _o(row, cot, "Số đơn (TT)") for row in ngay["rows"]}
    assert tt[("Lần 1 · 09:12", ma_a)] == "—" and tt[("Lần 2 · 10:00", ma_a)] == "0" and tt[("Lần 1 · 11:05", ma_b)] == "1"
    # Huy hiệu chỉ đếm chip Kỳ (kỳ 01.08 khác mặc định); không còn chip Chế độ
    assert "Chế độ" not in {c["label"] for c in r.context["chips"]} and r.context["filters_active"] == 1
    html = r.content.decode()
    assert 'name="che_do"' not in html and "Lần 3 · 16:40" in html and ">8.000</td>" in html

    # Gộp: một khối mọi lần nộp — Ngày · Nhân sự · Lần nộp · Loại tiền
    r = client.get("/bao-cao/tong-hop/", {**ky, "gop": "1"})
    assert [b["kind"] for b in r.context["blocks"]] == ["period", "submissions"]
    moi_lan = r.context["blocks"][1]
    assert [c["code"] for c in moi_lan["identity_columns"]] == ["nhom", "person", "lan", "tien"]
    assert len(moi_lan["rows"]) == 4 and moi_lan["count"] == 4
    assert [t["label"] for t in moi_lan["total_rows"]] == ["TỔNG CỘNG · toàn kỳ · USD", "TỔNG CỘNG · toàn kỳ · CAD"]


def test_nguon_van_don_khong_co_che_do(client, delivery_source, nguoi_dung):
    """AC-46.3 — Nguồn Vận đơn không có lần nộp: mỗi ngày như cũ, không ô hay chip Chế độ, `che_do` bị bỏ qua"""
    client.force_login(nguoi_dung["manager_sale"])
    r = client.get("/bao-cao/tong-hop/", {"nguon": delivery_source.table.code, "che_do": "tung-lan"})
    assert r.status_code == 200
    assert 'id="report-che-do"' not in r.content.decode() and "Chế độ" not in {c["label"] for c in r.context["chips"]}
    assert r.context["result"].mode == "cong"


def test_excel_theo_che_do(client, bang_mkt, mkt_source, bon_lan_nop, nguoi_dung):
    """AC-46.4 — Tệp Excel đúng như màn hình (Từng lần nộp): phụ đề không còn "Chế độ:"; sheet Theo ngay có cột
    Lần nộp và Loại tiền, mỗi lần nộp một dòng với số thô đúng như nhập (8000, 7000), TỔNG CỘNG theo loại
    tiền; Gộp thì một khối mọi lần nộp"""
    A = bon_lan_nop["A"]
    client.force_login(bon_lan_nop["B"])
    ky = {"nguon": bang_mkt.code, "tu": "2026-08-01", "den": "2026-08-01"}
    cot = [c.label for c in activity_service.build(bon_lan_nop["B"], mkt_source, start=NGAY, end=NGAY).columns]

    def sach(query):
        return load_workbook(BytesIO(client.get("/bao-cao/tong-hop/xuat/", query).content), data_only=True)

    book = sach(ky)
    assert "Chế độ" not in book["Toan ky theo nhan su"]["A2"].value
    ngay = list(book["Theo ngay"].values)
    dau = ngay[1]
    assert dau[:6] == ("STT", "Team", "Nhân sự", "Leader", "Lần nộp", "Loại tiền")
    dong_a = [d for d in ngay if d and d[2] == employee_code(A)]
    assert [(d[4][:5], d[5], d[6 + cot.index("CPQC")]) for d in dong_a] == [
        ("Lần 1", "CAD", 8000), ("Lần 2", "USD", 500), ("Lần 3", "CAD", 7000)]
    tong = [d for d in ngay if d and str(d[0]).startswith("TỔNG CỘNG")]
    assert [(d[0], d[5], d[6 + cot.index("CPQC")]) for d in tong] == [("TỔNG CỘNG · USD", "USD", 500), ("TỔNG CỘNG · CAD", "CAD", 18000)]

    book = sach({**ky, "gop": "1"})
    moi_lan = list(book["Theo ngay"].values)
    assert moi_lan[0][0] == "Mọi lần nộp trong kỳ" and moi_lan[1][:4] == ("Ngày", "Nhân sự", "Lần nộp", "Loại tiền")
    assert len([d for d in moi_lan[2:] if d and d[0] and not str(d[0]).startswith("TỔNG")]) == 4


def test_doi_soat_tt_theo_loai_tien_cua_don(bang_mkt, mkt_source, van_don, nguoi_dung):
    """AC-46.5 — (TT) đối soát theo loại tiền của vận đơn, không quy đổi: đơn USD của marketer vào dòng USD của
    marketer đó, đơn CAD vào dòng CAD; marketer không có báo cáo USD trong ngày thì đơn USD không vào đâu;
    TỔNG CỘNG theo loại tiền cộng đúng phần đối soát của loại tiền đó"""
    A = van_don["A"]
    _nop(bang_mkt, A, 9, 0, cpqc="10")                                          # CAD
    don_usd = DataRecord.objects.create(table=van_don["table"], department=van_don["table"].department,
                                        created_by=nguoi_dung["admin"], val_date=NGAY,
                                        data={"ngay": "2026-08-01", "quoc_gia": "Hoa Kỳ", "loai_tien": "USD"})
    WaybillAssignment.objects.create(record=don_usd, marketing=A)
    WaybillItem.objects.create(record=don_usd, product=van_don["sp1"], quantity=1, unit_price="10.00", paid_amount="7.00")
    result = activity_service.build(nguoi_dung["manager_mkt"], mkt_source, start=NGAY, end=NGAY)
    cot = [c.label for c in result.columns]
    dong = {(i["person_name"], i["loai_tien"]): dict(zip(cot, aggregations.row_values(i, result)[1])) for i in result.rows}
    assert set(dong) == {(employee_code(A), "CAD")}
    assert dong[(employee_code(A), "CAD")]["DS Chốt (TT)"] == 100 and dong[(employee_code(A), "CAD")]["Số đơn (TT)"] == 2
    _nop(bang_mkt, A, 15, 0, cpqc="4", thi_truong="Hoa Kỳ", tien="USD")
    result = activity_service.build(nguoi_dung["manager_mkt"], mkt_source, start=NGAY, end=NGAY)
    dong = {(i["person_name"], i["loai_tien"]): dict(zip(cot, aggregations.row_values(i, result)[1])) for i in result.rows}
    assert dong[(employee_code(A), "USD")]["DS Chốt (TT)"] == 7 and dong[(employee_code(A), "USD")]["Số đơn (TT)"] == 1
    assert dong[(employee_code(A), "CAD")]["DS Chốt (TT)"] == 100
    theo_tien = {t: dict(zip(cot, raw)) for t, raw in aggregations.total_rows(result)}
    assert theo_tien["USD"]["DS Chốt (TT)"] == 7 and theo_tien["CAD"]["DS Chốt (TT)"] == 325 - 25 - 200
    assert theo_tien["USD"]["Tỉ lệ chốt (TT)"] == Decimal(1) / Decimal(10) * 100


def test_mau_so_voi_tong_cung_loai_tien_va_nguong_tien_chi_vnd(client, bang_mkt, mkt_source, van_don, nguoi_dung):
    """AC-46.6 — Màu tương đối (±10 %) so với dòng TỔNG CỘNG **cùng loại tiền**, không so USD với CAD; ngưỡng
    tuyệt đối của chỉ tiêu tiền (CPO, Giá Mess, AOV) đặt theo ₫ nên chỉ tô dòng VND, ngưỡng tỉ lệ tô mọi loại
    tiền; form Ngưỡng màu nói rõ điều đó"""
    A, B = van_don["A"], van_don["B"]
    # CAD: A CPO 5, B CPO 20 → tổng CAD CPO 12,5; USD: một dòng A CPO 1.000 — so với tổng USD chính nó
    _nop(bang_mkt, A, 9, 0, cpqc="10", don=2)
    _nop(bang_mkt, B, 9, 5, cpqc="40", don=2)
    _nop(bang_mkt, A, 10, 0, cpqc="2000", don=2, thi_truong="Hoa Kỳ", tien="USD")
    result = activity_service.build(nguoi_dung["manager_mkt"], mkt_source, start=NGAY, end=NGAY)
    cot = [c.label for c in result.columns]
    rows = {(i["person_name"], i["loai_tien"]): cells for i, cells in
            zip(result.rows, [r["cells"] for r in aggregations.finish_rows(list(result.rows), result)])}
    lop = {k: v[cot.index("CPO")].lop for k, v in rows.items()}
    assert "o-tot" in lop[(employee_code(A), "CAD")] and "o-canh-bao" in lop[(employee_code(B), "CAD")]
    assert lop[(employee_code(A), "USD")] == "o-chi-so"                # bằng tổng USD của chính nó: không tô
    # Ngưỡng CPO theo ₫: dòng CAD/USD không tô theo ngưỡng; ngưỡng Tỉ lệ chốt tô mọi dòng
    mkt_source.thresholds = {"cpo": {"tot": "1", "kem": "2"}, "conversion": {"tot": "30", "kem": "15"}}
    mkt_source.save()
    result = activity_service.build(nguoi_dung["manager_mkt"], mkt_source, start=NGAY, end=NGAY)
    o = [dict(zip(cot, r["cells"])) for r in aggregations.finish_rows(list(result.rows), result)]
    assert all(d["CPO"].lop == "o-chi-so" for d in o)
    assert all("o-canh-bao" in d["Tỉ lệ chốt"].lop for d in o)            # 20 %: giữa 15 và 30
    hang = {r["code"]: r for r in threshold_service.rows(mkt_source)}
    assert hang["cpo"]["unit"] == "₫" and hang["conversion"]["unit"] == "%"
    client.force_login(nguoi_dung["manager_mkt"])
    html = client.get("/bao-cao/tong-hop/", {"nguon": bang_mkt.code, "tu": "2026-08-01", "den": "2026-08-01"}).content.decode()
    assert "chỉ tô dòng VND" in html


def test_the_tong_quan_moi_loai_tien_mot_cot(client, bang_mkt, mkt_source, bon_lan_nop, nguoi_dung):
    """AC-46.7 — Thẻ Báo cáo tổng hợp trên Tổng quan: mỗi chỉ tiêu một hàng (TL-60), mỗi loại tiền một cột có
    tiêu đề mã tiền; số đúng như nhập, không quy đổi, không cộng hai loại tiền; số không bẻ giữa chữ số (thẻ
    hẹp thì bảng cuộn ngang)"""
    client.force_login(bon_lan_nop["B"])
    r = client.get("/", {"mkt_nguon": bang_mkt.code, "tu": "2026-08-01", "den": "2026-08-01"})
    khoi = next(b for b in r.context["activity"]["blocks"] if b["kind"] == "mkt")["data"]
    assert khoi["currencies"] == ["USD", "CAD"]
    chi_tieu = dict(khoi["metrics"])
    assert [str(v) for v in chi_tieu["CPQC"]] == ["500", "18.000"] and [str(v) for v in chi_tieu["Số Mess"]] == ["10", "30"]
    html = r.content.decode()
    assert '<thead><tr><th scope="col">Chỉ tiêu</th><th scope="col">USD</th><th scope="col">CAD</th></tr></thead>' in html
    assert "<tr><th scope=\"row\">CPQC</th><td>500</td><td>18.000</td></tr>" in html
    assert "₫" not in "".join(str(v) for vals in chi_tieu.values() for v in vals)
    css = open("static/css/dashboard.css", encoding="utf-8").read()
    assert ".dashboard-metrics-bang td { text-align: right; font-weight: 600; white-space: nowrap; }" in css


def test_bang_du_lieu_tho_so_co_dau_cham(client, bang_mkt, mkt_source, van_don, nguoi_dung):
    """AC-46.8 — Bảng dữ liệu xem thô (`?dang=tho`) in số theo cách Việt Nam: 13250000 → 13.250.000, số lẻ đã
    lưu giữ nguyên (8000.5 → 8.000,5); không ký hiệu tiền; ô chữ giữ nguyên"""
    _nop(bang_mkt, van_don["A"], 9, 0, cpqc="13250000")
    _nop(bang_mkt, van_don["A"], 10, 0, cpqc="8000.5", thi_truong="Hoa Kỳ", tien="USD")
    client.force_login(nguoi_dung["manager_mkt"])
    r = client.get(f"/bang/{bang_mkt.code}/", {"dang": "tho"})
    o = [gia_tri for _, cac_o in r.context["cac_dong"] for cot, gia_tri, _ in cac_o if cot.code == "cpqc"]
    assert sorted(o) == ["13.250.000", "8.000,5"]
    thi_truong = {gia_tri for _, cac_o in r.context["cac_dong"] for cot, gia_tri, _ in cac_o if cot.code == "thi_truong"}
    assert thi_truong == {"Canada", "Hoa Kỳ"}
    assert ">13.250.000</td>" in r.content.decode()


def test_ngan_sach_truy_van_va_duong_qua_tran(client, bang_mkt, mkt_source, van_don, nguoi_dung, monkeypatch,
                                             django_assert_max_num_queries):
    """AC-46.9 — Tách loại tiền và chế độ Từng lần nộp không thêm truy vấn ở đường trong bộ nhớ (≤ 10 như
    AC-42.4); khi dòng quá trần phải phân trang bằng truy vấn: tổng theo loại tiền vẫn đúng (một lệnh nhóm
    theo loại tiền) và "Lần N" đếm đúng qua ranh giới trang (hàm cửa sổ trong SQL)"""
    A, B = van_don["A"], van_don["B"]
    for i, gio in enumerate((8, 9, 10, 11)):
        _nop(bang_mkt, A, gio, 0, cpqc=str(1000 * (i + 1)), tien="USD" if i == 2 else "CAD",
             thi_truong="Hoa Kỳ" if i == 2 else "Canada")
    _nop(bang_mkt, B, 12, 0, cpqc="50")
    client.force_login(B)
    ky = {"nguon": bang_mkt.code, "tu": "2026-08-01", "den": "2026-08-01"}
    client.get("/bao-cao/tong-hop/", ky)
    with django_assert_max_num_queries(10):
        assert client.get("/bao-cao/tong-hop/", ky).status_code == 200
    # Ép đường quá trần: MAX_GROUPS = 2 → dòng là queryset, phân trang bằng truy vấn
    monkeypatch.setattr(activity_service, "MAX_GROUPS", 2)
    monkeypatch.setattr(summary_service, "MAX_GROUPS", 2)
    result = activity_service.build(B, mkt_source, start=NGAY, end=NGAY, mode="tung-lan")
    assert not isinstance(result.rows, list)
    # Khoá (TT) dùng chung vẫn được đánh dấu bằng một lệnh đếm: A ba lần CAD trong ngày → (ngày, A, CAD)
    assert result.derived_shared == frozenset({(NGAY, employee_code(A), "CAD")})
    theo_tien = {t: dict(zip([c.label for c in result.columns], raw)) for t, raw in aggregations.total_rows(result)}
    assert theo_tien["CAD"]["CPQC"] == 1000 + 2000 + 4000 + 50 and theo_tien["USD"]["CPQC"] == 3000
    # A nộp thêm 23 lần (tổng 27) → trang 2 (25 dòng một trang) bắt đầu ở lần 26 của A: số lần đếm trên
    # toàn bộ ngày của A, không đếm lại từ 1 ở đầu trang
    for phut in range(23):
        _nop(bang_mkt, A, 13, phut, cpqc="1")
    trang2 = client.get("/bao-cao/tong-hop/", {**ky, "moi_trang": "25", "trang": "2"})
    assert trang2.status_code == 200 and trang2.context["page_obj"].number == 2
    lan = [(row["person"], dict((c["code"], v) for c, v in row["identity"])["lan"])
           for b in trang2.context["blocks"][1:] for row in b["rows"]]
    lan_a = [x[1].split(" · ")[0] for x in lan if x[0] == employee_code(A)]
    lan_b = [x[1].split(" · ")[0] for x in lan if x[0] == employee_code(B)]
    # 28 dòng (A 27, B 1), trang 1 lấy 25: trang 2 là đuôi dãy lần nộp của A, nối tiếp đúng trang 1
    assert len(lan_a) >= 2 and lan_a == [f"Lần {i}" for i in range(28 - len(lan_a), 28)]
    assert lan_b in ([], ["Lần 1"]) and len(lan_a) + len(lan_b) == 3
    assert trang2.context["blocks"][0]["kind"] == "period"                  # khối toàn kỳ vẫn đủ ở trang 2


def test_mode_parameter_defaults(rf):
    """AC-46.3 — `screen.parameters` luôn trả Từng lần nộp cho cả hai màn hình, bỏ qua `che_do` trên URL cũ
    (01.10.2026); tầng service vẫn giữ hai chế độ"""
    for query in ({}, {"che_do": "cong"}, {"che_do": "tung-lan"}, {"che_do": "xyz"}):
        assert screen.parameters(rf.get("/", query))["mode"] == "tung-lan"
    assert dict(activity_service.MODES) == {"cong": "Cộng theo ngày", "tung-lan": "Từng lần nộp"}


def test_chuoi_o_so_may_chu_doc_lai_dung():
    """AC-46.10 — Mọi chuỗi ô số tự viết ra đều được `parse_money` đọc lại đúng số (chấm ngăn nghìn, phẩy thập phân)"""
    for chuoi, so in (("13.250.000", "13250000"), ("8.000,5", "8000.5"), ("1.234", "1234"), ("0,5", "0.5"),
                      ("150", "150"), ("-2.500", "-2500"), ("1.000.000,25", "1000000.25")):
        assert parse_money(chuoi) == Decimal(so), chuoi
