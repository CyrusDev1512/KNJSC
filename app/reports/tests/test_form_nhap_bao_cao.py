"""ADR-043 — Form Nộp báo cáo ngày: dropdown Team, bốn trường bắt buộc, bỏ Hóa đơn, bố cục ngang."""
import re
from datetime import date
from pathlib import Path

import pytest
from django.core.management import call_command
from django.urls import reverse

from core.constants import Rank
from forms_builder.models import ColumnDef, DataRecord, FieldDef, FormDef, FormField, FormTableLink
from org.models import Team
from orders.models import Product
from reports.management.commands.configure_erp_reports import REQUIRED_INPUTS, configure_source
from reports.models import DailyReport, ReportSource
from reports.services import activity_service
from reports.tests.test_aggregations import bang_mkt  # noqa: F401
from reports.tests.test_mkt_derived_revenue import mkt_source  # noqa: F401

pytestmark = pytest.mark.django_db
GOC = Path(__file__).resolve().parent.parent.parent


def _payload(form, **theo_cot):
    """Dữ liệu POST theo mã trường của form, cho theo mã cột đích (mã trường do configure sinh ra)."""
    out = {"bieu_mau": form.code}
    for f in form.ordered_fields():
        cot = getattr(getattr(f, "link", None), "column", None)
        if cot is not None and cot.code in theo_cot:
            out[f.field.code] = theo_cot[cot.code]
    return out


def _du(form, **doi):
    Product.objects.get_or_create(code="sp1", defaults={"name": "SP1"})
    gia_tri = dict(so_mess="10", cpqc="3", so_don="2", doanh_so="100", san_pham="SP1", thi_truong="Canada")
    gia_tri.update(doi)
    return _payload(form, **gia_tri)


def test_chon_team_tren_form_nhap(client, bang_mkt, mkt_source, departments, teams, nguoi_dung, make_user):
    """AC-43.1 — Form nộp báo cáo có dropdown các team đang hoạt động của bộ phận sở hữu biểu mẫu (không lẫn
    team bộ phận khác), chọn sẵn team trong hồ sơ; nộp với team khác trong bộ phận thì dòng dữ liệu và báo cáo
    mang team đó — Leader team ấy xem và sửa được, Leader team khác không thấy; team của bộ phận khác hay id lạ
    bị từ chối, không lưu; để trống thì theo hồ sơ; bộ phận không có team đang hoạt động thì không có ô Team"""
    form = mkt_source.table.forms.get()
    A = nguoi_dung["staff_mkt"]
    leader_a = make_user("leader_mkt_a", Rank.LEADER, departments["mkt"])
    leader_b = make_user("leader_mkt_b", Rank.LEADER, departments["mkt"])
    team_a = Team.objects.create(name="MKT A", department=departments["mkt"], leader=leader_a)
    team_b = Team.objects.create(name="MKT B", department=departments["mkt"], leader=leader_b)
    for nguoi, team in ((leader_a, team_a), (leader_b, team_b), (A, team_a)):
        nguoi.profile.team = team
        nguoi.profile.save(update_fields=["team"])
    client.force_login(A)
    html = client.get("/bao-cao/", {"bieu_mau": form.code}).content.decode()
    assert 'id="o-team"' in html and f'<option value="{team_a.pk}" selected>MKT A</option>' in html
    assert re.search(rf'<option value="{team_b.pk}"\s*>MKT B</option>', html) and "Sale 1" not in html
    assert "— Chưa chọn —" not in html                     # đã có team hồ sơ thì không có mục trống
    # Nộp cho team B (khác team hồ sơ) → cả dòng dữ liệu lẫn DailyReport mang team B
    r = client.post("/bao-cao/", {**_du(form), "team": str(team_b.pk)})
    assert r.status_code == 302, r.content[:300]
    bao_cao = DailyReport.objects.get()
    assert bao_cao.team_id == team_b.pk and bao_cao.record.team_id == team_b.pk
    # Leader team B thấy và sửa được; Leader team A không thấy (phạm vi theo team đã chọn)
    client.force_login(leader_b)
    assert client.get(f"/bao-cao/{bao_cao.pk}/").status_code == 200
    assert client.get(f"/bao-cao/{bao_cao.pk}/sua/").status_code == 200
    client.force_login(leader_a)
    assert client.get(f"/bao-cao/{bao_cao.pk}/").status_code in (403, 404)
    assert client.get(f"/bao-cao/{bao_cao.pk}/sua/").status_code in (403, 404)
    # Team bộ phận khác, id lạ: từ chối rõ, không lưu
    client.force_login(A)
    for xau in (str(teams["sale1"].pk), "abc", "999999"):
        r = client.post("/bao-cao/", {**_du(form), "team": xau})
        assert r.status_code == 200 and "Team không thuộc bộ phận của biểu mẫu" in r.content.decode()
    assert DailyReport.objects.count() == 1
    # Để trống → theo hồ sơ (team A)
    r = client.post("/bao-cao/", {**_du(form), "team": ""})
    assert r.status_code == 302
    assert DailyReport.objects.order_by("-pk").first().team_id == team_a.pk
    # Bộ phận không còn team đang hoạt động → không có ô Team, vẫn nộp được theo hồ sơ
    Team.objects.filter(department=departments["mkt"]).update(is_active=False)
    html = client.get("/bao-cao/", {"bieu_mau": form.code}).content.decode()
    assert 'id="o-team"' not in html
    assert client.post("/bao-cao/", _du(form)).status_code == 302
    assert DailyReport.objects.order_by("-pk").first().team_id == team_a.pk


def test_bon_truong_bat_buoc(client, bang_mkt, mkt_source, nguoi_dung):
    """AC-43.2 — Sau `configure_erp_reports`, form MKT bắt buộc Số Mess, CPQC, Số đơn, Doanh số (cùng Ngày,
    Sản phẩm, Thị trường) và form Sale bắt buộc Số Mess, Số đơn, Doanh số; nộp thiếu CPQC bị từ chối nêu tên
    trường và không tạo dòng; "0" là giá trị hợp lệ; các ô đó mang thuộc tính `required`, ô hệ thống và ô
    không bắt buộc thì không"""
    form = mkt_source.table.forms.get()
    bat_buoc = {f.link.column.code for f in form.ordered_fields() if f.required and getattr(f, "link", None)}
    assert {"so_mess", "cpqc", "so_don", "doanh_so", "ngay", "san_pham", "thi_truong"} <= bat_buoc
    assert "tep_khach_hang" not in bat_buoc and "cpqc" in REQUIRED_INPUTS
    # Form Sale do lệnh dựng: ba trường số (không có CPQC)
    call_command("configure_erp_reports")
    sale = FormDef.objects.get(code="bc_sale_ngay")
    bat_buoc_sale = {f.link.column.code for f in sale.ordered_fields() if f.required and getattr(f, "link", None)}
    assert {"so_mess", "so_don", "doanh_so"} <= bat_buoc_sale and "ngay_ra_don" not in bat_buoc_sale
    # Trường đã có từ trước với required=False cũng bị ép bắt buộc khi chạy lại
    FormField.objects.filter(form=form, link__column__code="so_don").update(required=False)
    configure_source(bang_mkt, "mkt")
    assert FormField.objects.get(form=form, link__column__code="so_don").required
    client.force_login(nguoi_dung["staff_mkt"])
    html = client.get("/bao-cao/", {"bieu_mau": form.code}).content.decode()
    for ma in ("so_mess", "cpqc", "so_don", "doanh_so"):
        assert re.search(rf'name="[a-z0-9_]*{ma}"[^>]*\srequired', html), ma
    # Sản phẩm: ô chọn hay ô chữ tuỳ kiểu cột của bảng, đều mang required; Thị trường luôn là ô chọn chặt
    assert re.search(r'name="[a-z0-9_]*san_pham"[^>]*\srequired', html)
    assert re.search(r'<select class="o-nhap" name="[a-z0-9_]*thi_truong"[^>]*\srequired', html)
    assert not re.search(r'name="[a-z0-9_]*tep_khach_hang"[^>]*\srequired', html)
    assert 'name="marketer"' not in html and not re.search(r'readonly[^>]*\srequired', html)
    # Thiếu CPQC → từ chối, nêu tên trường, không tạo dòng
    thieu = _du(form)
    thieu = {k: ("" if k.endswith("cpqc") else v) for k, v in thieu.items()}
    r = client.post("/bao-cao/", thieu)
    assert r.status_code == 200 and "Chưa điền các trường bắt buộc: CPQC" in r.content.decode()
    assert DailyReport.objects.count() == 0 and DataRecord.objects.filter(table=bang_mkt).count() == 0
    # "0" hợp lệ
    assert client.post("/bao-cao/", _du(form, cpqc="0", so_don="0", doanh_so="0")).status_code == 302
    assert DailyReport.objects.count() == 1


def test_hoa_don_khong_con_tren_form_nhap(client, bang_mkt, nguoi_dung):
    """AC-43.3 — Form MKT đang có trường Hóa đơn thì `configure_erp_reports` gỡ nó và không tạo lại khi chạy
    lại; cột `hoa_don`, ánh xạ `invoice`, hai cột báo cáo "Hóa đơn" và "Hóa đơn/DS Chốt (TT)" vẫn còn cho dữ
    liệu cũ; form nộp không còn ô Hóa đơn và giá trị `hoa_don` gửi thẳng lên bị bỏ qua"""
    form = FormDef.objects.create(table=bang_mkt, department=bang_mkt.department, code="bc_mkt_hd", name="BC MKT")
    hoa_don, _ = ColumnDef.objects.get_or_create(table=bang_mkt, code="hoa_don", defaults={"name": "Hóa đơn", "field_type": "money"})
    truong = FieldDef.objects.create(name="Hóa đơn", code="hd_cu", field_type="money", department=bang_mkt.department)
    FormTableLink.objects.create(form_field=FormField.objects.create(form=form, field=truong, order=6), column=hoa_don)
    assert FormField.objects.filter(form=form, link__column__code="hoa_don").exists()
    for _ in range(2):   # chạy lại không tạo lại
        configure_source(bang_mkt, "mkt")
        assert not FormField.objects.filter(form=form, link__column__code="hoa_don").exists()
    assert ColumnDef.objects.filter(table=bang_mkt, code="hoa_don").exists()
    source = ReportSource.objects.get(table=bang_mkt)
    assert source.columns["invoice"] == "hoa_don"
    client.force_login(nguoi_dung["staff_mkt"])
    html = client.get("/bao-cao/", {"bieu_mau": form.code}).content.decode()
    assert not re.search(r'name="[a-z0-9_]*hoa_don"', html)
    r = client.post("/bao-cao/", {**_du(form), "hoa_don": "5", "hd_cu": "5"})
    assert r.status_code == 302, r.content[:300]
    assert "hoa_don" not in DailyReport.objects.get().record.data
    # Báo cáo tổng hợp vẫn có hai cột Hóa đơn cho dữ liệu cũ
    result = activity_service.build(nguoi_dung["manager_mkt"], source, group="day", start=date.today(), end=date.today())
    nhan = [c.label for c in result.columns]
    assert "Hóa đơn" in nhan and "Hóa đơn/DS Chốt (TT)" in nhan


def test_bo_cuc_ngang_form_nhap(client, bang_mkt, mkt_source, nguoi_dung):
    """AC-43.4 — Form nộp báo cáo là một thẻ trải hết chiều rộng: hàng điều khiển Biểu mẫu · Team · Ngày, lưới
    ô nhập ngang (`bm-ngang`, ô cao ≤ 36 px), cột tính sẵn hiện dạng chip thay cho ô nhập giả; không còn
    `max-width:860px`; màn Sửa báo cáo cùng lưới; phần đo bằng mắt ở biên bản"""
    mau = (GOC / "templates" / "reports" / "bao_cao_ngay.html").read_text(encoding="utf-8")
    assert "max-width:860px" not in mau and 'class="the-than bm bm-ngang"' in mau and 'class="bm-tinh"' in mau
    assert "o-tinh" not in mau and mau.count('<div class="the">') == 1
    sua = (GOC / "templates" / "reports" / "bao_cao_sua.html").read_text(encoding="utf-8")
    assert "max-width:860px" not in sua and "bm-ngang" in sua
    css = (GOC / "static" / "css" / "solarpunk.css").read_text(encoding="utf-8")
    cao = re.search(r"\.bm-ngang \.o-nhap \{[^}]*min-height:(\d+)px", css)
    assert cao and int(cao.group(1)) <= 36
    assert re.search(r"\.bm-ngang \{[^}]*grid-template-columns:repeat\(auto-fill", css)
    form = mkt_source.table.forms.get()
    client.force_login(nguoi_dung["staff_mkt"])
    html = client.get("/bao-cao/", {"bieu_mau": form.code}).content.decode()
    assert 'class="the-than bm bm-ngang"' in html and '<span class="chip">CPO' in html
    assert 'value="hệ thống tự tính"' not in html and 'form="bm-bao-cao">Nộp báo cáo</button>' in html
