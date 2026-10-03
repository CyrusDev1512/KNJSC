"""ADR-042 đợt 2 — bố cục khối như ảnh mẫu: khối toàn kỳ theo nhân sự, mỗi ngày một bảng, Gộp."""
from datetime import date, timedelta
from io import BytesIO
from urllib.parse import parse_qs

import pytest
from openpyxl import load_workbook

from django.conf import settings

from core.identity import employee_code
from reports import aggregations, layout
from reports.tests.test_activity import delivery_source  # noqa: F401
from reports.tests.test_aggregations import bang_mkt  # noqa: F401
from reports.tests.test_che_do_so_lieu import _nop
from reports.tests.test_mkt_derived_revenue import _bao_cao, mkt_source, van_don  # noqa: F401
from reports.tests.test_mkt_excel import marketing_scope  # noqa: F401

pytestmark = pytest.mark.django_db


def _o(row, cot, nhan):
    return row["cells"][cot.index(nhan)]


def test_bang_toan_ky_va_moi_ngay_mot_bang(client, bang_mkt, mkt_source, van_don, nguoi_dung):
    """AC-42.6 — Báo cáo tổng hợp: khối toàn kỳ theo nhân sự đứng đầu (mỗi người một dòng cộng cả
    kỳ, STT, Team, Leader, TỔNG CỘNG toàn kỳ ngay dưới tiêu đề cột), rồi mỗi ngày một bảng riêng mới
    nhất trước không có cột Ngày, mỗi lần nộp một dòng (01.10.2026), TỔNG CỘNG ngày bằng tổng dòng con,
    STT đếm lại; khối toàn kỳ không thêm truy vấn; ngày tách trang ghi "(tiếp)" và lặp TỔNG CỘNG; Excel
    hai sheet cùng khối"""
    A, B = van_don["A"], van_don["B"]
    _bao_cao(bang_mkt, A, "2026-08-01", "SP1", mess=10, don=2)
    _bao_cao(bang_mkt, B, "2026-08-01", "SP2", mess=30, don=3)
    _bao_cao(bang_mkt, A, "2026-08-02", "SP1", mess=10, don=1)
    client.force_login(B)
    query = {"nguon": bang_mkt.code, "tu": "2026-08-01", "den": "2026-08-02"}
    r = client.get("/bao-cao/tong-hop/", query)
    assert r.status_code == 200
    blocks = r.context["blocks"]
    cot = [c.label for c in r.context["result"].columns]
    assert [b["kind"] for b in blocks] == ["period", "day", "day"]
    ky, ngay2, ngay1 = blocks
    # Khối toàn kỳ: hai người, sắp theo mã, cộng cả kỳ; cột định danh STT · Team · Nhân sự · Leader
    assert ky["title"].startswith("Toàn kỳ 01/08 – 02/08/2026") and ky["count"] == 2
    # Báo cáo MKT toàn VND (ADR-048): không còn cột Loại tiền (đơn vị ghi một lần ở hàng tiêu đề); Excel trải nhãn
    # TỔNG CỘNG qua bốn cột định danh, màn hình in mỗi cột định danh một ô (02.10.2026)
    assert [c["code"] for c in ky["identity_columns"]] == ["stt", "team", "person", "leader"]
    assert ky["label_span"] == 4 and ky["total_span"] == 4 and ky["tien_column"] is None
    assert {row["currency"] for row in ky["rows"]} == {"VND"}
    nguoi = {row["person"]: row for row in ky["rows"]}
    assert [row["stt"] for row in ky["rows"]] == [1, 2] and set(nguoi) == {employee_code(A), employee_code(B)}
    assert _o(nguoi[employee_code(A)], cot, "Số Mess") == "20" and _o(nguoi[employee_code(B)], cot, "Số Mess") == "30"
    assert _o(nguoi[employee_code(A)], cot, "Số đơn") == "3"
    assert nguoi[employee_code(A)]["team"] == (A.profile.team.name if A.profile.team_id else "Chưa có team")
    assert [t["label"] for t in ky["total_rows"]] == ["TỔNG CỘNG · toàn kỳ · VND"]
    assert ky["total_rows"][0]["cells"] == aggregations.total_cells(r.context["result"])
    # Khối ngày: mới nhất trước, không cột Ngày, TỔNG CỘNG ngày = tổng dòng con, STT từ 1
    assert ngay2["title"] == "02.08.2026" and ngay1["title"] == "01.08.2026"
    assert all("nhom" not in [c["code"] for c in b["identity_columns"]] for b in (ngay1, ngay2))
    assert [row["stt"] for row in ngay1["rows"]] == [1, 2] and [row["stt"] for row in ngay2["rows"]] == [1]
    tong1 = dict(zip(cot, ngay1["total_rows"][0]["cells"]))
    assert tong1["Số Mess"] == "40" and tong1["Số đơn"] == "5"
    assert [t["label"] for t in ngay1["total_rows"]] == ["TỔNG CỘNG · VND"]
    html = r.content.decode()
    assert html.count('<table class="bang report-table"') == 3 and html.count('class="report-block-title"') == 3
    assert '<h3>02.08.2026</h3>' in html
    assert '<th scope="row" class="report-identity id-nhan-su report-identity-edge" data-pos="3">TỔNG CỘNG</th>' in html
    assert "id-tien" not in html
    # Excel: sheet toàn kỳ và sheet theo ngày, cùng số
    book = load_workbook(BytesIO(client.get("/bao-cao/tong-hop/xuat/", query).content), data_only=True)
    ky_xls = list(book["Toan ky theo nhan su"].values)
    assert ky_xls[4][:4] == ("STT", "Team", "Nhân sự", "Leader") and "Loại tiền" not in ky_xls[4]
    assert ky_xls[5][0] == "TỔNG CỘNG · toàn kỳ · VND"
    assert {d[2] for d in ky_xls[6:8]} == {employee_code(A), employee_code(B)}
    dong_a = next(d for d in ky_xls[6:8] if d[2] == employee_code(A))
    assert dong_a[4 + cot.index("Số Mess")] == 20
    ngay_xls = [d[0] for d in book["Theo ngay"].values if d and d[0] is not None]
    assert ngay_xls == ["Ngày 02.08.2026", "STT", "TỔNG CỘNG · VND", 1, "Ngày 01.08.2026", "STT", "TỔNG CỘNG · VND", 1, 2]
    # Ngày bị tách trang: 13 ngày × 2 lần nộp = 26 dòng, trang 25 dòng → trang 2 còn một người của ngày 01.08
    _bao_cao(bang_mkt, B, "2026-08-02", "SP2", mess=30)
    for i in range(2, 13):
        ngay = (date(2026, 8, 1) + timedelta(days=i)).isoformat()
        _bao_cao(bang_mkt, A, ngay, "SP1", mess=10)
        _bao_cao(bang_mkt, B, ngay, "SP2", mess=30)
    query = {"nguon": bang_mkt.code, "tu": "2026-08-01", "den": "2026-08-13", "moi_trang": "25", "trang": "2"}
    r2 = client.get("/bao-cao/tong-hop/", query)
    khoi = r2.context["blocks"]
    assert khoi[0]["kind"] == "period" and khoi[0]["count"] == 2      # khối toàn kỳ vẫn đủ cả kỳ trên trang 2
    assert [b["title"] for b in khoi[1:]] == ["01.08.2026 (tiếp)"]
    assert len(khoi[1]["rows"]) == 1 and khoi[1]["rows"][0]["stt"] == 2
    assert dict(zip(cot, khoi[1]["total_rows"][0]["cells"]))["Số Mess"] == "40"   # TỔNG CỘNG đủ cả ngày, không chỉ trang


def test_gop_chi_con_dong_tong_ngay(client, bang_mkt, mkt_source, van_don, nguoi_dung):
    """AC-42.7 — Gộp (`gop=1`) nguồn Sale/MKT: một bảng mọi lần nộp trong kỳ (Ngày · Nhân sự · Lần nộp, 01.10.2026;
    thêm Loại tiền khi nguồn tách loại tiền — báo cáo MKT toàn VND thì không, ADR-048), khối toàn kỳ vẫn đứng đầu;
    chip Gộp có × về Không gộp; Excel sheet Theo ngay cùng khối, cùng số"""
    A, B = van_don["A"], van_don["B"]
    _bao_cao(bang_mkt, A, "2026-08-01", "SP1", mess=10)
    _bao_cao(bang_mkt, B, "2026-08-01", "SP2", mess=30)
    _bao_cao(bang_mkt, A, "2026-08-02", "SP1", mess=10)
    client.force_login(B)
    query = {"nguon": bang_mkt.code, "tu": "2026-08-01", "den": "2026-08-02", "gop": "1"}
    r = client.get("/bao-cao/tong-hop/", query)
    blocks = r.context["blocks"]
    cot = [c.label for c in r.context["result"].columns]
    assert [b["kind"] for b in blocks] == ["period", "submissions"] and blocks[0]["count"] == 2
    moi_lan = blocks[1]
    assert [row["nhom"] for row in moi_lan["rows"]] == ["02.08.2026", "01.08.2026", "01.08.2026"]
    assert sorted(_o(row, cot, "Số Mess") for row in moi_lan["rows"]) == ["10", "10", "30"]
    assert [c["code"] for c in moi_lan["identity_columns"]] == ["nhom", "person", "lan"]
    assert dict(zip(cot, moi_lan["total_rows"][0]["cells"]))["Số Mess"] == "50"
    chips = {c["label"]: c for c in r.context["chips"]}
    assert chips["Gộp"]["value"] == "mọi lần nộp một bảng" and chips["Gộp"]["url"] and "gop=" not in chips["Gộp"]["url"]
    html = r.content.decode()
    assert 'aria-pressed="true">Gộp</a>' in html and html.count('<table class="bang report-table"') == 2
    # Không gộp là mặc định: không có chip, hai khối ngày
    r0 = client.get("/bao-cao/tong-hop/", {k: v for k, v in query.items() if k != "gop"})
    assert "Gộp" not in {c["label"] for c in r0.context["chips"]} and [b["kind"] for b in r0.context["blocks"]] == ["period", "day", "day"]
    # Excel khi Gộp: sheet Theo ngay = tiêu đề khối, hàng cột (Ngày, …), TỔNG CỘNG toàn kỳ, rồi mỗi lần nộp một dòng
    ngay_xls = list(load_workbook(BytesIO(client.get("/bao-cao/tong-hop/xuat/", query).content), data_only=True)["Theo ngay"].values)
    assert ngay_xls[0][0] == "Mọi lần nộp trong kỳ" and ngay_xls[1][0] == "Ngày" and str(ngay_xls[2][0]).startswith("TỔNG CỘNG")
    assert [d[0] for d in ngay_xls[3:6]] == ["02.08.2026", "01.08.2026", "01.08.2026"]
    assert ngay_xls[2][3 + cot.index("Số Mess")] == 50


def _ghim(kinds):
    """(mã cột đứng yên, mã cột mang bóng mép, chuỗi biến `left`) của một bộ cột định danh."""
    cot, kieu = layout.identity(kinds)
    return [c["code"] for c in cot if c["sticky"]], [c["code"] for c in cot if c["edge"]], kieu


def _vung_bang(html):
    """Phần khung bảng số liệu của trang — từ khung cuộn tới hết bảng cuối."""
    dau = html.index('report-table-scroll')
    return html[dau:html.rindex("</table>")]


def test_chi_ghim_cot_dau_nhan_su_loai_tien(client, bang_mkt, mkt_source, van_don, nguoi_dung):
    """AC-22.25 — Kéo ngang không còn cột số bị che (chủ dự án duyệt mockup 02.10.2026): chỉ cột đầu (STT, hay Ngày
    ở khối Gộp), Nhân sự và Loại tiền đứng yên; Team, Leader, Lần nộp giữ chỗ nhưng trôi theo (lớp `report-troi`);
    `left` của cột đứng yên chỉ cộng các cột đứng yên trước nó; bóng mép ở cột đứng yên cuối; dòng TỔNG CỘNG
    không còn ô nhãn trải ngang (`colspan`) mà mỗi cột định danh một ô, nhãn ngắn ở ô Nhân sự, mã tiền ở ô Loại
    tiền; Bảng dữ liệu dạng báo cáo cùng cách; tệp Excel giữ nguyên nhãn dài và thứ tự cột. Báo cáo MKT toàn VND
    không có cột Loại tiền (ADR-048) nên Nhân sự là cột đứng yên cuối, mang bóng mép"""
    tien, lan = layout.TIEN_KIND, layout.LAN_KIND
    assert _ghim(layout.PERSON_KINDS + (tien,)) == (
        ["stt", "person", "tien"], ["tien"], "--id-left-3:calc(var(--w-stt));--id-left-5:calc(var(--w-stt) + var(--w-nhan-su))")
    assert _ghim(layout.PERSON_KINDS) == (["stt", "person"], ["person"], "--id-left-3:calc(var(--w-stt))")
    assert _ghim(layout.PERSON_KINDS + (lan, tien)) == (
        ["stt", "person", "tien"], ["tien"], "--id-left-3:calc(var(--w-stt));--id-left-6:calc(var(--w-stt) + var(--w-nhan-su))")
    assert _ghim(layout.SUBMISSION_KINDS + (lan, tien)) == (
        ["nhom", "person", "tien"], ["tien"], "--id-left-2:calc(var(--w-ngay));--id-left-4:calc(var(--w-ngay) + var(--w-nhan-su))")
    assert _ghim(layout.DAY_KINDS + (tien,)) == (["nhom", "tien"], ["tien"], "--id-left-2:calc(var(--w-ngay))")
    # Cách xem khác (Tổng quan): Team đứng đầu thì Team và cột nhóm cùng đứng yên, Leader trôi
    assert _ghim((("team", "Team", "team"), ("nhom", "Ngày", "ngay"), ("leader", "Leader", "leader"))) == (
        ["team", "nhom"], ["nhom"], "--id-left-2:calc(var(--w-team))")

    A, B = van_don["A"], van_don["B"]
    _bao_cao(bang_mkt, A, "2026-08-01", "SP1", mess=10, don=2)
    _bao_cao(bang_mkt, B, "2026-08-01", "SP2", mess=30, don=3)
    client.force_login(B)
    query = {"nguon": bang_mkt.code, "tu": "2026-08-01", "den": "2026-08-01"}
    r = client.get("/bao-cao/tong-hop/", query)
    ky = r.context["blocks"][0]
    assert ky["total_at"] == "person" and ky["total_short"] == "TỔNG CỘNG"
    assert ky["label_span"] == 4 and ky["total_span"] == 4 and ky["tien_column"] is None   # Excel đọc
    for html, noi in ((r.content.decode(), "Báo cáo tổng hợp"),
                      (client.get(f"/bang/{bang_mkt.code}/", {"tu": "2026-08-01", "den": "2026-08-01"}).content.decode(),
                       "Bảng dữ liệu")):
        vung = _vung_bang(html)
        assert "colspan" not in vung, f"{noi}: dòng TỔNG CỘNG còn ô nhãn trải ngang"
        assert 'class="report-identity report-troi id-team" data-pos="2">Team</th>' in vung, noi
        assert 'class="report-identity report-troi id-leader" data-pos="4">Leader</th>' in vung, noi
        assert 'class="report-identity report-troi id-lan" data-pos="5">Lần nộp</th>' in vung, noi
        assert 'class="report-identity id-stt" data-pos="1">STT</th>' in vung, noi
        assert ('<th scope="row" class="report-identity id-nhan-su report-identity-edge" data-pos="3">TỔNG CỘNG</th>'
                in vung), noi
        assert "id-tien" not in vung, f"{noi}: báo cáo MKT toàn VND không còn cột Loại tiền"
        assert "TỔNG CỘNG · toàn kỳ" not in vung, f"{noi}: nhãn dài chỉ còn trong Excel"
    # Lớp trôi có quy tắc CSS (bài kiểm lớp CSS không bắt được lớp dính liền thẻ template)
    css = (settings.BASE_DIR / "static" / "css" / "solarpunk.css").read_text(encoding="utf-8")
    assert ".report-troi" in css
    # Excel giữ nhãn dài và thứ tự cột định danh
    book = load_workbook(BytesIO(client.get("/bao-cao/tong-hop/xuat/", query).content), data_only=True)
    ky_xls = list(book["Toan ky theo nhan su"].values)
    assert ky_xls[4][:4] == ("STT", "Team", "Nhân sự", "Leader") and ky_xls[5][0] == "TỔNG CỘNG · toàn kỳ · VND"


def test_gop_giu_trang_va_moc_ngay(client, bang_mkt, mkt_source, van_don, nguoi_dung):
    """AC-22.26 — Bấm Gộp / Không gộp không mất chỗ đang xem (chủ dự án duyệt mockup 02.10.2026): ở chế độ Từng lần
    nộp hai link giữ `trang` và `moi_trang` (hai chế độ chia trang theo cùng các lần nộp) và bỏ `nguong`; trang 2 của
    Gộp và của Không gộp là cùng một tập lần nộp; khối ngày và từng dòng của khối Gộp mang `data-ngay` để trình duyệt
    tìm lại đúng ngày; nguồn Vận đơn (Gộp chia trang theo ngày) vẫn về trang 1"""
    A, B = van_don["A"], van_don["B"]
    for i in range(13):
        ngay = (date(2026, 8, 1) + timedelta(days=i)).isoformat()
        _bao_cao(bang_mkt, A, ngay, "SP1", mess=10)
        _bao_cao(bang_mkt, B, ngay, "SP2", mess=30)
    client.force_login(B)
    query = {"nguon": bang_mkt.code, "tu": "2026-08-01", "den": "2026-08-13", "moi_trang": "25", "trang": "2",
             "nguong": "1"}
    r = client.get("/bao-cao/tong-hop/", query)
    gop_url, khong = r.context["gop_url"], r.context["khong_gop_url"]
    for url in (gop_url, khong):
        tham_so = parse_qs(url.lstrip("?"))
        assert tham_so["trang"] == ["2"] and tham_so["moi_trang"] == ["25"] and "nguong" not in tham_so, url
    assert parse_qs(gop_url.lstrip("?"))["gop"] == ["1"] and "gop" not in parse_qs(khong.lstrip("?"))

    def lan_nop(blocks):
        return sorted((row["nhom"], row["person"], next(v for c, v in row["identity"] if c["code"] == "lan"))
                      for b in blocks[1:] for row in b["rows"])
    r_gop = client.get("/bao-cao/tong-hop/" + gop_url)
    assert [b["kind"] for b in r_gop.context["blocks"]] == ["period", "submissions"]
    assert lan_nop(r.context["blocks"]) == lan_nop(r_gop.context["blocks"]) and len(lan_nop(r.context["blocks"])) == 1
    # Mốc ngày: mỗi khối ngày và mỗi dòng khối Gộp
    html = client.get("/bao-cao/tong-hop/", {**query, "trang": "1"}).content.decode()
    assert '<section class="report-block report-block-day" data-ngay="2026-08-13">' in html
    gop = client.get("/bao-cao/tong-hop/", {**query, "trang": "1", "gop": "1"}).content.decode()
    # Trang 1: 13.08 → 02.08 đủ hai lần nộp, 01.08 còn một lần (lần kia sang trang 2)
    assert gop.count('<tr data-ngay="2026-08-13">') == 2 and gop.count('<tr data-ngay="2026-08-01">') == 1


def test_gop_van_don_van_ve_trang_dau(client, delivery_source, nguoi_dung):
    """AC-22.26 — Nguồn Vận đơn: Gộp là mỗi ngày một dòng, chia trang theo ngày chứ không theo lần nộp, nên link
    Gộp / Không gộp vẫn bỏ `trang` (về trang 1) như trước"""
    client.force_login(nguoi_dung["admin"])
    rv = client.get("/bao-cao/tong-hop/", {"nguon": delivery_source.table.code, "trang": "2", "moi_trang": "25"})
    assert rv.status_code == 200
    for url in (rv.context["gop_url"], rv.context["khong_gop_url"]):
        tham_so = parse_qs(url.lstrip("?"))
        assert "trang" not in tham_so and tham_so["moi_trang"] == ["25"], url
