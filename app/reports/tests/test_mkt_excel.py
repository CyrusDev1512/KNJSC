"""BC MKT: công thức Excel và cùng kết quả trên màn hình/xuất."""
from datetime import date
from decimal import Decimal

import pytest
from reports import aggregations
from reports.services import summary_service
from reports.tests.test_aggregations import bang_mkt, dong_mau

pytestmark = pytest.mark.django_db


def test_excel_metrics_from_totals(bang_mkt, dong_mau, nguoi_dung):
    ctx = summary_service.build_context(nguoi_dung["manager_mkt"], bang_mkt,
        tab="tong-hop", date_from=date(2026,8,1), date_to=date(2026,8,31), product="")
    result = ctx["kq"]
    values = dict(zip([c.label for c in result.columns], aggregations.total_values(result)))
    assert list(values) == ["Số Mess", "CPQC", "Số đơn", "Doanh số", "Doanh thu", "Hóa đơn",
                            "CPO", "Giá Mess", "CPQC/Doanh số", "Hóa đơn/Doanh thu", "AOV"]
    assert values["Doanh thu"] is None and values["Hóa đơn"] is None
    assert values["CPQC/Doanh số"] == Decimal(500000) / Decimal(3280000)
    assert abs(values["Hóa đơn/Doanh thu"] - Decimal(24)/Decimal(270)) < Decimal("1e-25")
    assert values["CPO"] == Decimal(500000) / Decimal(24)
    exported = summary_service.build_export(nguoi_dung["manager_mkt"], bang_mkt,
        tab="tong-hop", date_from=date(2026,8,1), date_to=date(2026,8,31), product="")
    assert aggregations.total_values(exported) == aggregations.total_values(result)


def test_dashboard_has_scoped_marketing(bang_mkt, dong_mau, nguoi_dung):
    from dashboard.services.dashboard_service import tong_quan
    ctx = tong_quan(nguoi_dung["manager_mkt"])
    assert "marketing" in ctx
    assert ctx["marketing"]["ok"]


@pytest.mark.parametrize("cpqc,mess,orders", [(0,10,2),(10,0,2),(10,5,0),(None,5,2)])
def test_undefined_ratio_is_not_zero(cpqc,mess,orders):
    from reports.marketing import Metric
    m = Metric("m", ("cpqc","mess","orders"), "k_over_j")
    assert m.compute({"cpqc":cpqc,"mess":mess,"orders":orders}) is None


def test_exact_optional_fields_and_empty(bang_mkt, nguoi_dung):
    from forms_builder.models import ColumnDef, DataRecord
    from forms_builder.meaning import FieldType
    ColumnDef.objects.create(table=bang_mkt, name="Doanh thu", code="received", field_type=FieldType.MONEY)
    ColumnDef.objects.create(table=bang_mkt, name="Hóa đơn", code="invoice", field_type=FieldType.DECIMAL)
    user = nguoi_dung["staff_mkt"]
    record = DataRecord.objects.create(table=bang_mkt, department=bang_mkt.department,
        created_by=user, val_date=date(2026,8,1), val_revenue=100,
        data={"ngay":"2026-08-01","marketer":"Test","doanh_so":"100","received":"70", "invoice":"8", "so_mess":10, "so_don":2, "cpqc":"3"})
    def values(start):
        result = summary_service.build_context(user,bang_mkt,tab="tong-hop",
            date_from=start,date_to=start,product="")["kq"]
        return dict(zip([c.label for c in result.columns],aggregations.total_values(result)))
    actual = values(date(2026,8,1))
    assert actual["Doanh thu"] == 70 and actual["Hóa đơn"] == 8
    assert actual["Hóa đơn/Doanh thu"] == Decimal("0.2")
    empty = values(date(2026,8,2))
    assert all(v is None for v in empty.values())


@pytest.fixture
def marketing_scope(bang_mkt, nguoi_dung, teams, departments):
    from forms_builder.models import DataRecord, FormDef
    from reports.models import DailyReport
    # Cùng schema Marketing ở phòng Sale để dùng fixture hai team đã có.
    bang_mkt.department = departments["sale"]
    bang_mkt.save(update_fields=["department"])
    form = FormDef.objects.create(name="Báo cáo scope",code="scope_mkt",table=bang_mkt,department=departments["sale"])
    for key in ("staff_sale_1","staff_sale_1b","staff_sale_2","leader_sale_1"):
        user=nguoi_dung[key]
        row=DataRecord.objects.create(table=bang_mkt,created_by=user,department=departments["sale"],
            team=user.profile.team,val_date=date(2026,8,1),val_seller=key,val_product="SP1",
            val_revenue=100,data={"ngay":"2026-08-01","marketer":key,"san_pham":"SP1","doanh_so":"100","so_mess":10,"so_don":2,"cpqc":"3"})
        DailyReport.objects.create(form=form,record=row,created_by=user,department=departments["sale"],
            team=user.profile.team,report_date=date(2026,8,1))
    return form


@pytest.mark.parametrize("role,count",[("staff_sale_1",1),("leader_sale_1",3),("manager_sale",4),("admin",4)])
def test_all_surfaces_respect_scope(client,marketing_scope,nguoi_dung,role,count):
    from io import BytesIO
    from openpyxl import load_workbook
    client.force_login(nguoi_dung[role])
    query={"nguon":marketing_scope.table.code,"tu":"2026-08-01","den":"2026-08-31"}
    response=client.get("/bao-cao/tong-hop/",query)
    assert response.status_code==200
    result=response.context["kq"]
    assert result.totals["so_dong"]==count
    history=client.get("/bao-cao/lich-su/",{"bieu_mau":marketing_scope.code,"tu":query["tu"],"den":query["den"]})
    assert history.status_code==200 and history.context["trang"].paginator.count==count
    assert "Thống kê Marketing" in history.content.decode()
    dashboard=client.get("/",{"mkt_nguon":query["nguon"],"mkt_tu":query["tu"],"mkt_den":query["den"]})
    m=dashboard.context["marketing"]
    assert m["ok"] and m["data"]["state"]=="ready"
    assert dict(m["data"]["metrics"])["Số đơn"]==str(2*count)
    export=client.get("/bao-cao/tong-hop/xuat/",query)
    assert export.status_code==200
    rows=list(load_workbook(BytesIO(export.content),data_only=True).active.values)
    assert rows[3][1:]==tuple(c.label for c in result.columns)
    assert rows[-1][3]==2*count
    assert "Đánh giá nhân sự" in response.content.decode()


def test_foreign_source_and_filters(client,marketing_scope,nguoi_dung):
    client.force_login(nguoi_dung["staff_mkt"])
    for path in ("/bao-cao/tong-hop/","/bao-cao/tong-hop/xuat/"):
        assert client.get(path,{"nguon":marketing_scope.table.code}).status_code==403
    for params in ({"bieu_mau":marketing_scope.code},{"bo_phan":"sale"}):
        assert client.get("/bao-cao/lich-su/",params).status_code==404
    d=client.get("/",{"mkt_nguon":marketing_scope.table.code})
    assert d.context["marketing"]["data"]["state"]=="invalid_source"


def test_filters_empty_and_failure_isolation(client,marketing_scope,nguoi_dung,monkeypatch):
    client.force_login(nguoi_dung["manager_sale"])
    query={"nguon":marketing_scope.table.code,"tu":"2026-08-01","den":"2026-08-01","sp":"missing"}
    r=client.get("/bao-cao/tong-hop/",query)
    assert r.context["kq"].totals["so_dong"]==0
    d=client.get("/",{"mkt_nguon":query["nguon"],"mkt_tu":"2026-08-02","mkt_den":"2026-08-02"})
    assert d.context["marketing"]["data"]["state"]=="empty"
    def fail(*args,**kwargs): raise RuntimeError("test failure")
    monkeypatch.setattr(summary_service,"build_context",fail)
    d=client.get("/")
    assert d.status_code==200 and not d.context["marketing"]["ok"]
    assert d.context["nhan_su"]["ok"]
