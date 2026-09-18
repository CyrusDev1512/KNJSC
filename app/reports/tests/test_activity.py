from datetime import date
from decimal import Decimal
import pytest
from forms_builder.models import DataRecord, TableDef
from reports.services import activity_service
from reports.models import ReportSource
from reports.tests.test_aggregations import bang_mkt, dong_mau
from reports.tests.test_mkt_excel import marketing_scope

pytestmark=pytest.mark.django_db


def test_sale_ratio_and_account_identity(bang_mkt,dong_mau,nguoi_dung):
    source=ReportSource.objects.create(table=bang_mkt,kind="sale",columns={"mess":"so_mess","orders":"so_don","sales":"doanh_so","market":"thi_truong"})
    result=activity_service.build(nguoi_dung["manager_mkt"],source,group="person",start=date(2026,8,1),end=date(2026,8,31))
    assert result.totals["so_dong"]==4
    assert result.totals["conversion"] == Decimal(24)/Decimal(270)
    assert len(list(result.rows))==1  # Account ID, not different handwritten names.


def test_market_missing_is_preserved(bang_mkt,dong_mau,nguoi_dung):
    source=ReportSource.objects.create(table=bang_mkt,kind="sale",columns={"mess":"so_mess","orders":"so_don","sales":"doanh_so","market":"thi_truong"})
    result=activity_service.build(nguoi_dung["manager_mkt"],source,group="market",start=date(2026,8,1),end=date(2026,8,31))
    assert list(result.rows)[0]["nhom"]=="Chưa xác định"


@pytest.mark.parametrize("role,count", [("staff_sale_1",1),("leader_sale_1",3),("manager_sale",4),("admin",4)])
def test_sale_scope_and_dashboard(client, marketing_scope, nguoi_dung, role, count):
    from io import BytesIO
    from openpyxl import load_workbook
    from reports import aggregations
    source=ReportSource.objects.create(table=marketing_scope.table,kind="sale",columns={"mess":"so_mess","orders":"so_don","sales":"doanh_so","market":"thi_truong"})
    client.force_login(nguoi_dung[role])
    query={"nguon":source.table.code,"tu":"2026-08-01","den":"2026-08-31"}
    r=client.get("/bao-cao/tong-hop/",query)
    assert r.status_code==200
    result=r.context["result"]
    assert result.totals["so_dong"]==count
    exported=client.get("/bao-cao/tong-hop/xuat/",query)
    rows=list(load_workbook(BytesIO(exported.content),data_only=True).active.values)
    tong=aggregations.total_values(result)   # dòng tổng: nhãn, ô trống cho Nhân sự/Leader, rồi số liệu (ADR-035)
    assert tuple(Decimal(str(v)) if v is not None else None for v in rows[-1][-len(tong):])==tuple(tong)
    d=client.get("/",{"sale_nguon":source.table.code,"tu":query["tu"],"den":query["den"]})
    block=next(b for b in d.context["activity"]["blocks"] if b["kind"]=="sale")
    assert block["ok"] and block["data"]["count"]==count


def test_foreign_activity_source(client, marketing_scope, nguoi_dung):
    ReportSource.objects.create(table=marketing_scope.table,kind="sale")
    client.force_login(nguoi_dung["staff_mkt"])
    for path in ("/bao-cao/tong-hop/", "/bao-cao/tong-hop/xuat/"):
        assert client.get(path,{"nguon":marketing_scope.table.code}).status_code==403


def test_zero_and_missing_inputs(bang_mkt, nguoi_dung):
    source=ReportSource.objects.create(table=bang_mkt,kind="sale",columns={"mess":"so_mess","orders":"so_don","sales":"doanh_so","market":"thi_truong"})
    user=nguoi_dung["staff_mkt"]
    DataRecord.objects.create(table=bang_mkt,created_by=user,department=bang_mkt.department,val_date=date(2026,8,1),data={"so_mess":0,"so_don":2})
    result=activity_service.build(user,source)
    assert result.totals["conversion"] is None
    assert result.totals["__missing_revenue"] is None


@pytest.fixture
def delivery_source(marketing_scope, nguoi_dung):
    from orders.models import WaybillAssignment, WaybillItem, Product
    source=ReportSource.objects.create(table=marketing_scope.table,kind="delivery",columns={"market":"quoc_gia"})
    product=Product.objects.create(code="a",name="A")
    other=Product.objects.create(code="b",name="B")
    records=list(DataRecord.objects.filter(table=source.table).order_by("pk"))
    for i, row in enumerate(records):
        # Người tạo khác người được giao; hai sản phẩm không nhân số đơn.
        owner=nguoi_dung["staff_sale_1"] if i < 2 else nguoi_dung["staff_sale_2"]
        if i < 3: WaybillAssignment.objects.create(record=row,delivery=owner)
        row.data={"quoc_gia":"Canada" if i < 2 else "Hoa Kỳ", "trang_thai_vc":"Đang giao" if i < 2 else "Đã giao"}
        row.save(update_fields=["data"])
        WaybillItem.objects.create(record=row,product=product,quantity=2,unit_price=999)
        WaybillItem.objects.create(record=row,product=other,quantity=3,unit_price=999)
    return source


@pytest.mark.parametrize("role,count",[("staff_sale_1",2),("leader_sale_1",2),("manager_sale",4),("admin",4)])
def test_delivery_distinct_and_assigned_scope(delivery_source,nguoi_dung,role,count):
    source=delivery_source
    result=activity_service.build(nguoi_dung[role],source,group="person")
    assert result.totals["c_orders"]==count
    assert result.totals["c_quantity"]==count*5
    assert [c.label for c in result.columns]==["Số đơn","Số lượng sản phẩm"]
    rows=list(result.rows)
    if count==4: assert any(r["nhom"]=="Chưa phân công" for r in rows)


def test_delivery_filters_match_status_and_export(delivery_source,nguoi_dung,client):
    from io import BytesIO
    from openpyxl import load_workbook
    source=delivery_source
    user=nguoi_dung["admin"]
    result=activity_service.build(user,source,group="product",product="a",market="Canada")
    assert result.totals["c_orders"]==2 and result.totals["c_quantity"]==4
    assert len(list(result.rows))==1
    assert activity_service.shipping_status(user,source,product="a",market="Canada")==[{"label":"Đang giao","count":2}]
    client.force_login(user)
    r=client.get("/bao-cao/tong-hop/xuat/",{"nguon":source.table.code,"sp":"a","thi_truong":"Canada","tu":"2026-08-01","den":"2026-08-31"})
    assert r.status_code==200
    book=load_workbook(BytesIO(r.content),data_only=True)
    assert list(book.active.values)[-1][-2:]==(2,4)   # sau nhãn còn hai ô trống Nhân sự/Leader (ADR-035)
    assert list(book.worksheets[1].values)[-1]==("Đang giao",2)


def test_configure_metadata_idempotent(departments):
    from django.core.management import call_command
    from forms_builder.models import FormDef, FormTableLink
    call_command("configure_erp_reports")
    call_command("configure_erp_reports")
    form=FormDef.objects.get(code="bc_sale_ngay")
    assert ReportSource.objects.filter(table=form.table).count()==1
    links=FormTableLink.objects.filter(form_field__form=form,column__code="thi_truong")
    assert links.count()==1 and links.get().form_field.required
    assert not DataRecord.objects.exists()


@pytest.mark.parametrize("market,day,valid",[("Canada","2026-08-01",True),("","2026-08-01",False),("Atlantis","2026-08-01",False),("Canada","2026-08-02",False)])
def test_submit_market_and_period(departments,nguoi_dung,market,day,valid):
    from django.core.management import call_command
    from forms_builder.models import FormDef
    from reports.services import daily_service
    from core.exceptions import BusinessError
    from orders.models import Product
    Product.objects.create(code="p",name="Sản phẩm P")
    call_command("configure_erp_reports")
    form=FormDef.objects.get(code="bc_sale_ngay")
    fields=list(form.ordered_fields())
    raw={"ngay":day,"san_pham":"Sản phẩm P","thi_truong":market,"so_mess":"10","so_don":"2","doanh_so":"100"}
    values={f.field.code:raw.get(f.link.column.code,"") for f in fields}
    if valid:
        report=daily_service.submit(form,values,report_date=date(2026,8,1),actor=nguoi_dung["staff_sale_1"],fields=fields)
        assert report.record.data["thi_truong"]==market
    else:
        with pytest.raises(BusinessError):
            daily_service.submit(form,values,report_date=date(2026,8,1),actor=nguoi_dung["staff_sale_1"],fields=fields)
        assert DataRecord.objects.count()==0


@pytest.mark.parametrize("path", ["/bao-cao/tong-hop/", "/bao-cao/lich-su/"])
def test_query_budget(client,marketing_scope,nguoi_dung,django_assert_max_num_queries,path):
    source=ReportSource.objects.create(table=marketing_scope.table,kind="sale",columns={"mess":"so_mess","orders":"so_don","sales":"doanh_so","market":"thi_truong"})
    client.force_login(nguoi_dung["leader_sale_1"])
    params={"nguon":source.table.code,"tu":"2026-08-01","den":"2026-08-31"}
    client.get(path,params)
    with django_assert_max_num_queries(10):
        assert client.get(path,params).status_code==200



def test_marketing_exact_excel_formula(bang_mkt,dong_mau,nguoi_dung):
    from reports import aggregations
    source=ReportSource.objects.create(table=bang_mkt,kind="mkt",columns={"mess":"so_mess","orders":"so_don","sales":"doanh_so","cost":"cpqc","market":"thi_truong"})
    result=activity_service.build(nguoi_dung["manager_mkt"],source,group="market")
    values=dict(zip([c.label for c in result.columns],aggregations.total_values(result)))
    assert values["CPQC"]==Decimal(500000)
    assert values["CPO"]==Decimal(500000)/24
    assert values["Giá Mess"]==Decimal(500000)/270
    assert values["Hóa đơn/Doanh thu"]==(Decimal(500000)/270)/(Decimal(500000)/24)
    assert values["Doanh thu"] is None and values["Hóa đơn"] is None


def test_dashboard_isolates_single_source_failure(client,marketing_scope,nguoi_dung,monkeypatch):
    from dashboard.services import dashboard_service
    ReportSource.objects.create(table=marketing_scope.table,kind="sale",columns={"mess":"so_mess","orders":"so_don","sales":"doanh_so","market":"thi_truong"})
    client.force_login(nguoi_dung["admin"])
    def broken(*args,**kwargs): raise RuntimeError("injected test failure")
    monkeypatch.setattr(activity_service,"build",broken)
    response=client.get("/")
    assert response.status_code==200
    blocks={b["kind"]:b for b in response.context["activity"]["blocks"]}
    assert not blocks["sale"]["ok"]
    assert blocks["delivery"]["ok"] and blocks["delivery"]["data"]["state"]=="no_source"
    assert response.context["nhan_su"]["ok"]



def test_delivery_query_budget(client,delivery_source,nguoi_dung,django_assert_max_num_queries):
    client.force_login(nguoi_dung["leader_sale_1"])
    params={"nguon":delivery_source.table.code,"tu":"2026-08-01","den":"2026-08-31"}
    client.get("/bao-cao/tong-hop/",params)
    with django_assert_max_num_queries(10):
        assert client.get("/bao-cao/tong-hop/",params).status_code==200


@pytest.mark.parametrize("export",[False,True])
def test_legacy_link_uses_configured_report(client,marketing_scope,nguoi_dung,export):
    from urllib.parse import urlsplit,parse_qs
    ReportSource.objects.create(table=marketing_scope.table,kind="sale",columns={"mess":"so_mess","orders":"so_don","sales":"doanh_so","market":"thi_truong"})
    client.force_login(nguoi_dung["manager_sale"])
    path="/bao-cao/hoat-dong/xuat/" if export else "/bao-cao/hoat-dong/"
    query={"nguon":marketing_scope.table.code,"nhom":"market","tu":"2026-08-01","den":"2026-08-31","sp":"SP1","thi_truong":"Canada","trang":"2"}
    response=client.get(path,query)
    assert response.status_code==302
    url=urlsplit(response.url)
    assert url.path==("/bao-cao/tong-hop/xuat/" if export else "/bao-cao/tong-hop/")
    assert parse_qs(url.query)=={k:[v] for k,v in query.items()}




def test_submission_does_not_fallback_from_foreign_form(client,marketing_scope,nguoi_dung):
    client.force_login(nguoi_dung["staff_mkt"])
    assert client.get("/bao-cao/",{"bieu_mau":marketing_scope.code}).status_code==403
    assert client.post("/bao-cao/",{"bieu_mau":marketing_scope.code,"ngay_bao_cao":"2026-08-01"}).status_code==403


def test_duplicate_names_remain_separate_accounts(marketing_scope,nguoi_dung):
    from org.models import UserProfile
    UserProfile.objects.filter(department=marketing_scope.department).update(full_name="Cùng tên")
    source=ReportSource.objects.create(table=marketing_scope.table,kind="sale",columns={"mess":"so_mess","orders":"so_don","sales":"doanh_so","market":"thi_truong"})
    result=activity_service.build(nguoi_dung["admin"],source,group="person")
    rows=list(result.rows)
    assert len(rows)==4
    assert all("Cùng tên" in row["nhom"] for row in rows)



def test_export_limit_before_workbook(client,bang_mkt,dong_mau,nguoi_dung,settings,monkeypatch):
    from reports import excel
    ReportSource.objects.create(table=bang_mkt,kind="sale",columns={"mess":"so_mess","orders":"so_don","sales":"doanh_so","market":"thi_truong"})
    settings.EXPORT_MAX_ROWS=1
    client.force_login(nguoi_dung["manager_mkt"])
    def unexpected(*args,**kwargs): raise AssertionError("Must reject before allocating workbook")
    monkeypatch.setattr(excel,"build_workbook",unexpected)
    response=client.get("/bao-cao/tong-hop/xuat/",{"nguon":bang_mkt.code,"tu":"2026-08-01","den":"2026-08-31"})
    assert response.status_code==400
    assert "Thu hẹp bộ lọc" in response.content.decode()


@pytest.mark.parametrize("query",[{"nhom":"unknown"},{"tu":"2026-08-31","den":"2026-08-01"}])
def test_invalid_filters_show_error(client,marketing_scope,nguoi_dung,query):
    ReportSource.objects.create(table=marketing_scope.table,kind="sale",columns={"market":"thi_truong"})
    client.force_login(nguoi_dung["manager_sale"])
    response=client.get("/bao-cao/tong-hop/",{"nguon":marketing_scope.table.code,**query})
    assert response.status_code==400 and response.context["error"]


@pytest.mark.parametrize("old,new",[("tong-hop","day"),("nhan-vien","person"),("san-pham","product"),("thi-truong","market")])
def test_summary_preserves_old_group_links(client, marketing_scope, nguoi_dung, old, new):
    ReportSource.objects.create(table=marketing_scope.table, kind="sale", columns={"market":"thi_truong"})
    client.force_login(nguoi_dung["manager_sale"])
    response = client.get("/bao-cao/tong-hop/", {"nguon":marketing_scope.table.code,"nhom":old})
    assert response.status_code == 200
    assert response.context["params"]["group"] == new
    assert 'href="/bao-cao/hoat-dong/"' not in response.content.decode()


@pytest.mark.parametrize("role,persons", [
    ("staff_sale_1", {"staff_sale_1"}),
    ("leader_sale_1", {"staff_sale_1", "staff_sale_1b", "leader_sale_1"}),
    ("manager_sale", {"staff_sale_1", "staff_sale_1b", "staff_sale_2", "leader_sale_1"}),
    ("admin", {"staff_sale_1", "staff_sale_1b", "staff_sale_2", "leader_sale_1"}),
])
def test_day_view_shows_person_and_leader_in_scope(client, marketing_scope, nguoi_dung, role, persons):
    """AC-22.10 — Cách xem Tổng hợp nhóm theo ngày × nhân sự: cột Nhân sự và Leader ngay sau Ngày, Leader tra từ
    Team.leader; Staff chỉ thấy dòng của mình, Leader team mình, Manager cả bộ phận; lọc nhân sự thu hẹp bảng;
    Excel cùng cột; lọc nhân sự ngoài phạm vi bị 403"""
    from io import BytesIO
    from openpyxl import load_workbook
    source=ReportSource.objects.create(table=marketing_scope.table,kind="sale",columns={"mess":"so_mess","orders":"so_don","sales":"doanh_so","market":"thi_truong"})
    client.force_login(nguoi_dung[role])
    query={"nguon":source.table.code,"tu":"2026-08-01","den":"2026-08-31"}
    r=client.get("/bao-cao/tong-hop/",query)
    assert r.status_code==200 and r.context["result"].show_person
    rows=r.context["rows"]
    assert [row["nhom"] for row in rows]==["01.08.2026"], "mỗi ngày vẫn một dòng — cấu trúc bảng không đổi"
    assert {p.split(" — ")[0] for p in rows[0]["person"].split(", ")}==persons
    leaders=set(rows[0]["leader"].split(", "))
    assert "Leader Sale 1" in leaders                        # Team.leader của Sale 1
    assert ("Leader Sale 2" in leaders) == ("staff_sale_2" in persons)
    assert r.context["label_span"]==3
    html=r.content.decode()
    assert "<th scope=\"col\">Nhân sự</th><th scope=\"col\">Leader</th>" in html
    # Lọc theo nhân sự: chỉ còn dòng của người đó; người ngoài phạm vi bị chặn
    me=nguoi_dung["staff_sale_1"].pk
    r2=client.get("/bao-cao/tong-hop/",{**query,"nhan_su":me})
    assert [row["person"].split(" — ")[0] for row in r2.context["rows"]]==["staff_sale_1"] and r2.context["rows"][0]["leader"]=="Leader Sale 1"
    outsider=nguoi_dung["staff_sale_2"].pk
    r3=client.get("/bao-cao/tong-hop/",{**query,"nhan_su":outsider})
    assert (r3.status_code==403) == ("staff_sale_2" not in persons)
    sheet=list(load_workbook(BytesIO(client.get("/bao-cao/tong-hop/xuat/",query).content),data_only=True).active.values)
    assert sheet[3][:3]==("Ngày","Nhân sự","Leader") and len(sheet[4:-1])==1
    assert {p.split(" — ")[0] for p in sheet[4][1].split(", ")}==persons and "Leader Sale 1" in sheet[4][2]


def test_day_view_pages_by_hundred(client, marketing_scope, nguoi_dung):
    """AC-22.11 — Báo cáo hoạt động phân trang mặc định 100 nhóm mỗi trang; dòng tổng trong bộ lọc vẫn tính trên
    toàn bộ kết quả, không theo trang"""
    source=ReportSource.objects.create(table=marketing_scope.table,kind="sale",columns={"mess":"so_mess","orders":"so_don","sales":"doanh_so","market":"thi_truong"})
    client.force_login(nguoi_dung["admin"])
    r=client.get("/bao-cao/tong-hop/",{"nguon":source.table.code,"tu":"2026-08-01","den":"2026-08-31"})
    assert r.context["trang"].paginator.per_page==100 and r.context["moi_trang"]==100
    assert r.context["result"].totals["so_dong"]==4
    r25=client.get("/bao-cao/tong-hop/",{"nguon":source.table.code,"tu":"2026-08-01","den":"2026-08-31","moi_trang":25})
    assert r25.context["moi_trang"]==25
