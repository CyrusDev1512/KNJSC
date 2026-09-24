"""ADR-042 đợt 3 — ngưỡng màu ba bậc do Manager đặt, lọc nhiều sản phẩm."""
import re
from datetime import date
from decimal import Decimal
from io import BytesIO

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from openpyxl import load_workbook

from core.constants import AuditAction
from core.identity import employee_code
from core.models import AuditLog
from reports import aggregations
from reports.models import ReportSource
from reports.services import activity_service, threshold_service
from reports.tests.test_aggregations import bang_mkt  # noqa: F401
from reports.tests.test_mkt_derived_revenue import _bao_cao, mkt_source, van_don  # noqa: F401

pytestmark = pytest.mark.django_db

CAD = Decimal("17500")


def _lop(row, cot, nhan):
    return row["cells"][cot.index(nhan)].lop


def test_ba_bac_mau_theo_nguong_tuyet_doi(client, bang_mkt, mkt_source, van_don, nguoi_dung):
    """AC-42.8 — Chỉ tiêu có ngưỡng tô xanh khi đạt mốc Tốt, đỏ khi qua mốc Kém, vàng ở giữa, đúng
    chiều tốt (Tỉ lệ chốt cao, CPO thấp); dòng TỔNG CỘNG cũng tô; chỉ tiêu chưa có ngưỡng giữ cách
    so với dòng Tổng ±10 %; lớp `o-xau` có trong CSS"""
    A, B = van_don["A"], van_don["B"]
    # A: 20 mess, 8 đơn, CPQC 100 CAD → CPO 218.750 ₫, Tỉ lệ chốt 40 %
    # B: 20 mess, 2 đơn, CPQC 100 CAD → CPO 875.000 ₫, Tỉ lệ chốt 10 %
    # Tổng: 40 mess, 10 đơn, CPQC 200 CAD → CPO 350.000 ₫, Tỉ lệ chốt 25 %
    _bao_cao(bang_mkt, A, "2026-08-01", "SP1", mess=20, don=8, cpqc="100")
    _bao_cao(bang_mkt, B, "2026-08-01", "SP2", mess=20, don=2, cpqc="100")
    mkt_source.thresholds = {"cpo": {"tot": "300000", "kem": "800000"}, "conversion": {"tot": "30", "kem": "15"}}
    mkt_source.save()
    client.force_login(B)
    query = {"nguon": bang_mkt.code, "tu": "2026-08-01", "den": "2026-08-01"}
    r = client.get("/bao-cao/tong-hop/", query)
    result = r.context["result"]
    cot = [c.label for c in result.columns]
    dong = {row["person"]: row for row in r.context["rows"] if row["kind"] == "row"}
    a, b = dong[employee_code(A)], dong[employee_code(B)]
    assert a["cells"][cot.index("CPO")] == "218.750 ₫" and b["cells"][cot.index("CPO")] == "875.000 ₫"
    # CPO càng thấp càng tốt: A ≤ 300.000 → xanh; B > 800.000 → đỏ
    assert "o-tot" in _lop(a, cot, "CPO") and "o-xau" in _lop(b, cot, "CPO")
    # Tỉ lệ chốt càng cao càng tốt: A 40 % ≥ 30 → xanh; B 10 % < 15 → đỏ
    assert "o-tot" in _lop(a, cot, "Tỉ lệ chốt") and "o-xau" in _lop(b, cot, "Tỉ lệ chốt")
    # Giữa hai mốc là vàng: dòng TỔNG CỘNG (CPO 350.000, Tỉ lệ chốt 25 %) cũng tô khi có ngưỡng tuyệt đối
    tong = aggregations.total_cells(result)
    assert "o-canh-bao" in tong[cot.index("CPO")].lop and "o-canh-bao" in tong[cot.index("Tỉ lệ chốt")].lop
    # Giá Mess chưa có ngưỡng → cách tương đối: cả hai bằng mốc → chỉ nền cột
    assert _lop(a, cot, "Giá Mess") == "o-chi-so" and tong[cot.index("Giá Mess")].lop == "o-chi-so"
    html = r.content.decode()
    assert 'class="o-chi-so o-xau"' in html and 'class="o-chi-so o-tot"' in html
    css = open("static/css/solarpunk.css", encoding="utf-8").read()
    assert "td.o-xau" in css and "--critical-soft" in css
    # Không ngưỡng → cách cũ (AC-22.16): A dưới mốc tổng → xanh, B trên → vàng, không có đỏ
    mkt_source.thresholds = {}
    mkt_source.save()
    r0 = client.get("/bao-cao/tong-hop/", query)
    dong0 = {row["person"]: row for row in r0.context["rows"] if row["kind"] == "row"}
    assert "o-tot" in _lop(dong0[employee_code(A)], cot, "CPO") and "o-canh-bao" in _lop(dong0[employee_code(B)], cot, "CPO")
    assert 'class="o-chi-so o-xau"' not in r0.content.decode()


def test_form_nguong_ba_cap_bac(client, bang_mkt, mkt_source, nguoi_dung):
    """AC-42.9 — Admin và quản lý bộ phận sở hữu nguồn (Manager, Leader) thấy form Ngưỡng màu và lưu
    được (302 + nhật ký Sửa); Staff và quản lý bộ phận khác bị 403 có nhật ký từ chối, không thấy form;
    mốc sai thứ tự / thiếu một mốc / không phải số → báo lỗi tiếng Việt, không lưu; để trống cả hai
    mốc thì bỏ ngưỡng của chỉ tiêu đó"""
    _bao_cao(bang_mkt, nguoi_dung["staff_mkt"], "2026-08-01", "SP1")
    url = "/bao-cao/tong-hop/nguong/"
    trang = f"/bao-cao/tong-hop/?nguon={bang_mkt.code}&tu=2026-08-01&den=2026-08-01"
    tot = {"nguon": bang_mkt.code, "next": trang, "tot_cpo": "300.000", "kem_cpo": "800.000", "tot_conversion": "30", "kem_conversion": "15"}
    # Leader bộ phận sở hữu cũng được (cùng luật `can_manage_columns`, ADR-015 — fixture không có leader MKT)
    for vai in ("admin", "manager_mkt"):
        client.force_login(nguoi_dung[vai])
        assert 'id="report-nguong"' in client.get(trang).content.decode()
        r = client.post(url, tot)
        assert r.status_code == 302 and r["Location"] == trang
        mkt_source.refresh_from_db()
        assert mkt_source.thresholds == {"cpo": {"tot": "300000", "kem": "800000"}, "conversion": {"tot": "30", "kem": "15"}}
        assert AuditLog.objects.filter(action=AuditAction.UPDATE, detail__contains="Đặt ngưỡng màu").exists()
    # Form hiện mốc đang lưu
    html = client.get(trang).content.decode()
    assert 'name="tot_cpo" value="300.000"' in html and 'name="kem_conversion" value="15"' in html
    # Bị từ chối: Staff cùng bộ phận, quản lý bộ phận khác (nguồn ngoài phạm vi)
    truoc = AuditLog.objects.filter(action=AuditAction.DENIED).count()
    for vai in ("staff_mkt", "manager_sale"):
        client.force_login(nguoi_dung[vai])
        r = client.post(url, {**tot, "tot_cpo": "1", "kem_cpo": "2"})
        assert r.status_code == 403
    assert AuditLog.objects.filter(action=AuditAction.DENIED).count() >= truoc + 1
    client.force_login(nguoi_dung["staff_mkt"])
    assert 'id="report-nguong"' not in client.get(trang).content.decode()
    mkt_source.refresh_from_db()
    assert mkt_source.thresholds["cpo"] == {"tot": "300000", "kem": "800000"}      # không đổi
    # Sai thứ tự theo chiều tốt (CPO càng thấp càng tốt: Tốt phải nhỏ hơn Kém) → lỗi, không lưu, form mở lại
    client.force_login(nguoi_dung["manager_mkt"])
    r = client.post(url, {**tot, "tot_cpo": "900000", "kem_cpo": "800000"}, follow=True)
    assert "mốc Tốt phải nhỏ hơn mốc Kém" in r.content.decode() and r.request["QUERY_STRING"].endswith("nguong=1")
    mkt_source.refresh_from_db()
    assert mkt_source.thresholds["cpo"] == {"tot": "300000", "kem": "800000"}
    # Lưu hụt lần hai từ trang đã mang `nguong=1`: không nối đuôi thành `&nguong=1&nguong=1`
    r = client.post(url, {**tot, "next": trang + "&nguong=1", "tot_cpo": "900000", "kem_cpo": "800000"})
    assert r.status_code == 302 and r["Location"].count("nguong=1") == 1 and r["Location"].startswith(trang)
    for xau in ({"tot_cpo": "300000", "kem_cpo": ""}, {"tot_cpo": "abc", "kem_cpo": "1"}, {"tot_conversion": "10", "kem_conversion": "20"}):
        r = client.post(url, {**tot, **xau}, follow=True)
        assert 'class="bao bao-xau"' in r.content.decode() or "bao-xau" in r.content.decode()
    mkt_source.refresh_from_db()
    assert mkt_source.thresholds["conversion"] == {"tot": "30", "kem": "15"}
    # Trống cả hai mốc → bỏ ngưỡng chỉ tiêu đó, chỉ tiêu khác giữ
    r = client.post(url, {**tot, "tot_cpo": "", "kem_cpo": ""})
    assert r.status_code == 302
    mkt_source.refresh_from_db()
    assert mkt_source.thresholds == {"conversion": {"tot": "30", "kem": "15"}}
    # Form hiện lại mốc đã lưu theo cách người Việt gõ (`0,345`, `300.000`) và gửi lại y nguyên thì mốc
    # không đổi — chuỗi máy `0.345` sẽ bị `parse_money` đọc thành 345
    r = client.post(url, {**tot, "tot_conversion": "7,32", "kem_conversion": "5,98", "tot_cost_sales": "0,345", "kem_cost_sales": "0,5"})
    assert r.status_code == 302
    html = client.get(trang + "&nguong=1").content.decode()
    hien = dict(re.findall(r'name="((?:tot|kem)_[a-z_]+)" value="([^"]*)"', html))
    assert {k: v for k, v in hien.items() if v} == {"tot_conversion": "7,32", "kem_conversion": "5,98", "tot_cost_sales": "0,345",
                                                    "kem_cost_sales": "0,5", "tot_cpo": "300.000", "kem_cpo": "800.000"}
    assert client.post(url, {"nguon": bang_mkt.code, "next": trang, **hien}).status_code == 302
    mkt_source.refresh_from_db()
    assert mkt_source.thresholds == {"cpo": {"tot": "300000", "kem": "800000"}, "conversion": {"tot": "7.32", "kem": "5.98"},
                                     "cost_sales": {"tot": "0.345", "kem": "0.5"}}
    # Thiếu nguồn → 400; khoá lạ bị bỏ qua
    assert client.post(url, {"next": trang}).status_code == 400
    assert threshold_service.parse({"tot_bia": "1", "kem_bia": "2"}) == {}


@pytest.mark.django_db(transaction=True)
def test_migration_0005_xuoi_nguoc():
    """AC-42.10 — Migration `reports/0005` (cột `thresholds`) chạy ngược bỏ cột và chạy xuôi thêm lại,
    không đụng dữ liệu khác"""
    def cot():
        with connection.cursor() as c:
            c.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'reports_reportsource'")
            return {row[0] for row in c.fetchall()}
    assert "thresholds" in cot()
    executor = MigrationExecutor(connection)
    executor.migrate([("reports", "0004_remove_report_unique_per_person_per_day")])
    assert "thresholds" not in cot()
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()
    executor.migrate([("reports", "0005_reportsource_thresholds")])
    assert "thresholds" in cot()


def test_loc_nhieu_san_pham_va_url_cu(client, bang_mkt, mkt_source, van_don, nguoi_dung):
    """AC-42.11 — `sp` lặp lại lọc nhiều sản phẩm: tổng và phần đối soát (TT) theo đúng các sản phẩm
    đã chọn; URL cũ một sản phẩm vẫn đúng; danh sách tick chỉ có sản phẩm trong phạm vi quyền; chip
    "N sản phẩm"; phụ đề Excel ghi danh sách; nguồn không có sản phẩm nào thì báo"""
    A, B = van_don["A"], van_don["B"]
    _bao_cao(bang_mkt, A, "2026-08-01", "SP1", mess=10)
    _bao_cao(bang_mkt, A, "2026-08-01", "SP2", mess=20)
    _bao_cao(bang_mkt, B, "2026-08-01", "SP3", mess=40)
    client.force_login(B)
    query = {"nguon": bang_mkt.code, "tu": "2026-08-01", "den": "2026-08-01"}
    r = client.get("/bao-cao/tong-hop/", {**query, "sp": ["SP1", "SP2"]})
    assert r.status_code == 200 and r.context["result"].totals["c_so_mess"] == 30
    cot = [c.label for c in r.context["result"].columns]
    a = next(row for row in r.context["rows"] if row["kind"] == "row" and row["person"] == employee_code(A))
    assert a["cells"][cot.index("DS Chốt (TT)")] == aggregations.format_number(100 * CAD, 0) + " ₫"   # w1 SP1 60 + w2 SP2 40
    assert {c["label"]: c["value"] for c in r.context["chips"]}["Sản phẩm"] == "SP1, SP2"
    assert [p["value"] for p in r.context["products"]] == ["SP1", "SP2", "SP3"]
    html = r.content.decode()
    assert 'id="report-multi-sp"' in html and html.count('name="sp" value="SP1" checked') == 1 and html.count(' checked') == 2
    # URL cũ một sản phẩm
    r1 = client.get("/bao-cao/tong-hop/", {**query, "sp": "SP1"})
    assert r1.context["result"].totals["c_so_mess"] == 10
    a1 = next(row for row in r1.context["rows"] if row["kind"] == "row")
    assert a1["cells"][cot.index("DS Chốt (TT)")] == aggregations.format_number(60 * CAD, 0) + " ₫"
    assert {c["label"]: c["value"] for c in r1.context["chips"]}["Sản phẩm"] == "SP1"
    # Ba sản phẩm → chip đếm; phụ đề Excel ghi danh sách
    r3 = client.get("/bao-cao/tong-hop/", {**query, "sp": ["SP1", "SP2", "SP3"]})
    assert {c["label"]: c["value"] for c in r3.context["chips"]}["Sản phẩm"] == "3 sản phẩm"
    sheet = list(load_workbook(BytesIO(client.get("/bao-cao/tong-hop/xuat/", {**query, "sp": ["SP1", "SP2"]}).content), data_only=True).active.values)
    assert "Sản phẩm: SP1, SP2" in sheet[1][0]
    # Staff A chỉ thấy sản phẩm của mình trong danh sách tick
    client.force_login(A)
    assert [p["value"] for p in client.get("/bao-cao/tong-hop/", query).context["products"]] == ["SP1", "SP2"]
    # Cách xem theo sản phẩm với hai mục
    rows = activity_service.build(B, mkt_source, group="product", product=["SP1", "SP3"], start=date(2026, 8, 1), end=date(2026, 8, 1)).rows
    assert {row["nhom"] for row in rows} == {"SP1", "SP3"}
