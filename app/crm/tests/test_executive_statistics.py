"""AC-22.1–AC-22.8 — Bàn điều hành KN CRM trên các bảng động."""
from datetime import date
from decimal import Decimal

import pytest

from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, DataRecord, TableDef


pytestmark = pytest.mark.django_db


def make_table(department, actor, code, name, columns):
    table = TableDef.objects.create(
        department=department, created_by=actor, code=code, name=name,
    )
    for order, definition in enumerate(columns):
        ColumnDef.objects.create(table=table, order=order, **definition)
    return table


def col(name, code, field_type=FieldType.INTEGER, meaning=""):
    return {"name": name, "code": code, "field_type": field_type, "meaning": meaning}


@pytest.fixture
def executive_tables(departments, nguoi_dung):
    actor = nguoi_dung["admin"]
    marketing = make_table(departments["mkt"], actor, "mkt_exec", "Marketing Canada", [
        col("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
        col("Marketer", "marketer", FieldType.TEXT, Meaning.SELLER),
        col("Sản phẩm", "san_pham", FieldType.TEXT, Meaning.PRODUCT),
        col("Số Mess", "so_mess"), col("CPQC", "cpqc", FieldType.MONEY),
        col("Số đơn", "so_don"),
        col("Doanh số", "doanh_so", FieldType.MONEY, Meaning.REVENUE),
    ])
    sale = make_table(departments["sale"], actor, "sale_exec", "Sale theo ngày", [
        col("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
        col("Người bán", "nguoi_ban", FieldType.TEXT, Meaning.SELLER),
        col("Số đơn", "so_don"),
        col("Doanh thu", "doanh_thu", FieldType.MONEY, Meaning.REVENUE),
        col("Sản phẩm", "san_pham", FieldType.TEXT, Meaning.PRODUCT),
        col("Loại tiền", "loai_tien", FieldType.CHOICE),
    ])
    generic = make_table(departments["sale"], actor, "ghi_chu_exec", "Ghi chú chung", [
        col("Nội dung", "noi_dung", FieldType.TEXT),
    ])
    return marketing, sale, generic


def add_row(table, actor, day, data, *, revenue=None, seller="", product=""):
    return DataRecord.objects.create(
        table=table, department=table.department, created_by=actor,
        team=getattr(actor.profile, "team", None),
        val_date=day, val_revenue=revenue, val_seller=seller, val_product=product,
        data={"ngay": day.isoformat(), **data},
    )


def test_all_visible_sources_and_missing_profile_are_explained(
        client, executive_tables, nguoi_dung):
    """AC-22.1 — Mọi bảng đang dùng đều chọn được, thiếu cột được nói rõ."""
    marketing, sale, generic = executive_tables
    client.force_login(nguoi_dung["admin"])
    response = client.get("/thong-ke/", {"nguon": generic.code, "tu": "2026-09-01", "den": "2026-09-11"})
    assert response.status_code == 200
    assert {source["code"] for source in response.context["sources"]} >= {
        marketing.code, sale.code, generic.code,
    }
    assert response.context["dashboard"]["profile"] == "generic"
    assert "Ngày" in response.context["dashboard"]["missing"]


def test_legacy_waybill_source_uses_generic_profile_with_history_note(
        client, departments, nguoi_dung):
    """AC-22.1 — `van_don` cũ vẫn chọn được nhưng không nhận profile mới."""
    legacy = make_table(
        departments["vd"], nguoi_dung["admin"], "van_don", "Vận đơn lịch sử",
        [col("Ngày", "ngay", FieldType.DATE, Meaning.DATE)],
    )
    client.force_login(nguoi_dung["admin"])
    response = client.get("/thong-ke/", {
        "nguon": legacy.code, "tu": "2026-09-01", "den": "2026-09-11",
    })
    dashboard = response.context["dashboard"]
    assert dashboard["profile"] == "generic"
    assert "Nguồn lịch sử" in dashboard["legacy_note"]


def test_marketing_uses_weighted_totals_and_previous_zero_language(
        client, executive_tables, nguoi_dung):
    """AC-22.2 — CPO/tỷ lệ tính từ tổng; kỳ trước 0 không sinh vô cực."""
    marketing, _, _ = executive_tables
    user = nguoi_dung["manager_mkt"]
    add_row(marketing, user, date(2026, 9, 10),
            {"marketer": "A", "so_mess": 10, "cpqc": "100", "so_don": 1,
             "doanh_so": "1000"}, revenue=1000, seller="A")
    add_row(marketing, user, date(2026, 9, 11),
            {"marketer": "B", "so_mess": 90, "cpqc": "900", "so_don": 9,
             "doanh_so": "9000"}, revenue=9000, seller="B")
    client.force_login(user)
    response = client.get("/thong-ke/", {
        "nguon": marketing.code, "tu": "2026-09-10", "den": "2026-09-11",
    })
    dashboard = response.context["dashboard"]
    metrics = {item["code"]: item["value"] for item in dashboard["metrics"]}
    assert dashboard["profile"] == "marketing"
    assert metrics["cpo"] == Decimal("100")
    assert metrics["close_rate"] == Decimal("10")
    assert any("mới xuất hiện" in insight["evidence"].lower()
               for insight in dashboard["insights"])


def test_marketing_and_generic_never_combine_configured_currencies(
        client, departments, nguoi_dung):
    """AC-22.3 — Có Loại tiền thì mọi giá trị tiền được tách theo loại."""
    actor = nguoi_dung["admin"]
    marketing = make_table(departments["mkt"], actor, "mkt_currency", "MKT đa tiền", [
        col("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
        col("Marketer", "marketer", FieldType.TEXT, Meaning.SELLER),
        col("Số Mess", "so_mess"), col("CPQC", "cpqc", FieldType.MONEY),
        col("Số đơn", "so_don"),
        col("Doanh số", "doanh_so", FieldType.MONEY, Meaning.REVENUE),
        col("Loại tiền", "loai_tien", FieldType.CHOICE),
    ])
    generic = make_table(departments["sale"], actor, "generic_currency", "Thu khác", [
        col("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
        col("Doanh thu", "doanh_thu", FieldType.MONEY, Meaning.REVENUE),
        col("Loại tiền", "loai_tien", FieldType.CHOICE),
    ])
    for currency, cost, revenue in (("USD", "100", 1_000), ("VND", "900", 9_000)):
        add_row(
            marketing, actor, date(2026, 9, 11),
            {"marketer": "A", "so_mess": 10, "cpqc": cost, "so_don": 1,
             "doanh_so": str(revenue), "loai_tien": currency},
            revenue=revenue, seller="A",
        )
        add_row(
            generic, actor, date(2026, 9, 11),
            {"doanh_thu": str(revenue), "loai_tien": currency}, revenue=revenue,
        )
    client.force_login(actor)
    marketing_dashboard = client.get("/thong-ke/", {
        "nguon": marketing.code, "tu": "2026-09-11", "den": "2026-09-11",
    }).context["dashboard"]
    assert {(item["currency"], item["value"]) for item in marketing_dashboard["money"]} == {
        ("USD", Decimal(1_000)), ("VND", Decimal(9_000)),
    }
    assert {(item["currency"], item["value"]) for item in marketing_dashboard["ratios"]} == {
        ("USD", Decimal(100)), ("VND", Decimal(900)),
    }
    generic_dashboard = client.get("/thong-ke/", {
        "nguon": generic.code, "tu": "2026-09-11", "den": "2026-09-11",
    }).context["dashboard"]
    assert {(item["currency"], item["value"]) for item in generic_dashboard["money"]} == {
        ("USD", Decimal(1_000)), ("VND", Decimal(9_000)),
    }


def test_sale_splits_currency_and_computes_aov_from_totals(
        client, executive_tables, nguoi_dung):
    """AC-22.3 — Sale tách tiền tệ và AOV = tổng doanh thu / tổng đơn."""
    _, sale, _ = executive_tables
    user = nguoi_dung["manager_sale"]
    add_row(sale, user, date(2026, 9, 11),
            {"nguoi_ban": "Lan", "so_don": 2, "doanh_thu": "200", "loai_tien": "USD"},
            revenue=200, seller="Lan")
    add_row(sale, user, date(2026, 9, 11),
            {"nguoi_ban": "Minh", "so_don": 3, "doanh_thu": "900", "loai_tien": "VND"},
            revenue=900, seller="Minh")
    client.force_login(user)
    response = client.get("/thong-ke/", {
        "nguon": sale.code, "tu": "2026-09-11", "den": "2026-09-11",
    })
    dashboard = response.context["dashboard"]
    assert dashboard["profile"] == "sale"
    assert {(m["currency"], m["value"]) for m in dashboard["money"]} == {
        ("USD", Decimal("200")), ("VND", Decimal("900")),
    }
    assert {(m["currency"], m["value"]) for m in dashboard["aov"]} == {
        ("USD", Decimal("100")), ("VND", Decimal("300")),
    }


def test_invalid_dates_do_not_aggregate(client, executive_tables, nguoi_dung, monkeypatch):
    """AC-22.4 — Ngày sai hiện lỗi biểu mẫu và không chạy tổng hợp."""
    from crm.services import statistics_service

    monkeypatch.setattr(statistics_service, "build_dashboard", lambda *a, **k: pytest.fail("aggregated"), raising=False)
    client.force_login(nguoi_dung["admin"])
    response = client.get("/thong-ke/", {"tu": "2026-09-12", "den": "2026-09-11"})
    assert response.status_code == 200
    assert response.context["date_errors"]
    assert response.context["dashboard"] is None


def test_foreign_or_inactive_source_is_403_and_audited(
        client, executive_tables, nguoi_dung):
    """AC-22.5 — Mã nguồn ngoài quyền/ngừng dùng bị từ chối và ghi nhật ký."""
    from core.constants import AuditAction
    from core.models import AuditLog

    _, sale, _ = executive_tables
    client.force_login(nguoi_dung["manager_mkt"])
    assert client.get("/thong-ke/", {"nguon": sale.code}).status_code == 403
    sale.is_active = False
    sale.save(update_fields=["is_active"])
    client.force_login(nguoi_dung["admin"])
    response = client.get("/thong-ke/", {"nguon": sale.code})
    assert response.status_code == 403
    assert AuditLog.objects.filter(action=AuditAction.DENIED,
                                   target_id__contains=sale.code).exists()


def test_owner_presentation_never_upgrades_non_admin(
        client, executive_tables, nguoi_dung, settings):
    """AC-22.6 — Danh sách owner chỉ đổi giao diện, không nâng quyền."""
    settings.EXECUTIVE_OWNER_USERNAMES = ["staff_sale_1", "quan_tri"]
    client.force_login(nguoi_dung["staff_sale_1"])
    response = client.get("/thong-ke/")
    assert not response.context["executive_owner"]
    client.force_login(nguoi_dung["admin"])
    response = client.get("/thong-ke/")
    assert response.context["executive_owner"]
    assert "Bàn điều hành chủ sở hữu" in response.content.decode()


def test_overview_runs_at_most_one_source_per_profile_and_keeps_source_names(
        client, executive_tables, nguoi_dung):
    """AC-22.7 — Tổng hợp chỉ chạy ba nguồn được chọn."""
    marketing, sale, _ = executive_tables
    client.force_login(nguoi_dung["admin"])
    response = client.get("/thong-ke/", {
        "mkt_nguon": marketing.code, "sale_nguon": sale.code,
        "tu": "2026-09-01", "den": "2026-09-11",
    })
    dashboard = response.context["dashboard"]
    assert dashboard["profile"] == "overview"
    assert dashboard["sections"]["marketing"]["source_name"] == marketing.name
    assert dashboard["sections"]["sale"]["source_name"] == sale.name


def test_statistics_navigation_exists_with_any_visible_table(
        executive_tables, nguoi_dung):
    """AC-22.8 — Sidebar không phụ thuộc riêng bảng Vận đơn mới."""
    from crm.navigation import build

    items = build(nguoi_dung["manager_mkt"])
    assert any(item.code == "statistics" for item in items)


def test_erp_summary_links_to_crm_dashboard_without_changing_export(
        client, nguoi_dung, settings):
    """AC-22.8 — ERP chỉ thêm lối sang CRM; endpoint xuất vẫn giữ nguyên."""
    settings.BANGTINH_URL = "http://localhost:8021/"
    settings.ROOT_URLCONF = "knjsc.urls"
    client.force_login(nguoi_dung["admin"])
    response = client.get("/bao-cao/tong-hop/")
    assert response.status_code == 200
    assert response.context["crm_dashboard_url"] == "http://localhost:8021/thong-ke/"
    assert "Mở Bàn điều hành KN CRM" in response.content.decode()


def test_sale_aggregate_obeys_staff_leader_manager_admin_scope(
        client, executive_tables, nguoi_dung):
    """AC-22.5 — Số tổng dùng đúng scope dòng của bốn cấp bậc."""
    _, sale, _ = executive_tables
    people = (
        nguoi_dung["staff_sale_1"],
        nguoi_dung["staff_sale_1b"],
        nguoi_dung["staff_sale_2"],
    )
    for person in people:
        add_row(
            sale, person, date(2026, 9, 11),
            {"nguoi_ban": person.username, "so_don": 1,
             "doanh_thu": "100", "loai_tien": "VND"},
            revenue=100, seller=person.username,
        )
    cases = (
        (nguoi_dung["staff_sale_1"], Decimal(1)),
        (nguoi_dung["leader_sale_1"], Decimal(2)),
        (nguoi_dung["manager_sale"], Decimal(3)),
        (nguoi_dung["admin"], Decimal(3)),
    )
    for user, expected in cases:
        client.force_login(user)
        response = client.get("/thong-ke/", {
            "nguon": sale.code, "tu": "2026-09-11", "den": "2026-09-11",
        })
        assert response.status_code == 200
        assert response.context["dashboard"]["orders"] == expected


def test_one_profile_failure_does_not_hide_other_overview_sections(
        client, executive_tables, nguoi_dung, monkeypatch):
    """AC-22.6 — Lỗi một profile được cô lập trong góc tổng hợp."""
    from crm.services import statistics_profiles

    marketing, sale, _ = executive_tables

    def broken(*args, **kwargs):
        raise RuntimeError("profile test failure")

    monkeypatch.setitem(statistics_profiles.BUILDERS, "marketing", broken)
    client.force_login(nguoi_dung["admin"])
    response = client.get("/thong-ke/", {
        "mkt_nguon": marketing.code, "sale_nguon": sale.code,
        "tu": "2026-09-01", "den": "2026-09-11",
    })
    sections = response.context["dashboard"]["sections"]
    assert sections["marketing"]["ok"] is False
    assert sections["sale"]["ok"] is True


def test_query_count_does_not_grow_with_sale_rows(
        executive_tables, nguoi_dung):
    """AC-22.9 — Aggregate Sale giữ số truy vấn cố định theo số dòng."""
    from django.db import connection
    from django.test.utils import CaptureQueriesContext
    from crm.services import statistics_service

    _, sale, _ = executive_tables
    admin = nguoi_dung["admin"]
    scoped_table = next(
        table for table in statistics_service.source_tables(admin)
        if table.pk == sale.pk
    )

    def query_count():
        with CaptureQueriesContext(connection) as captured:
            statistics_service.build_dashboard(
                admin, scoped_table, date(2026, 9, 1), date(2026, 9, 30),
            )
        return len(captured)

    small = query_count()
    DataRecord.objects.bulk_create([
        DataRecord(
            table=sale, department=sale.department, created_by=admin,
            val_date=date(2026, 9, 11), val_revenue=Decimal(100),
            val_seller=f"Sale {index}",
            data={"ngay": "2026-09-11", "nguoi_ban": f"Sale {index}",
                  "so_don": 1, "doanh_thu": "100", "loai_tien": "VND"},
        )
        for index in range(250)
    ])
    large = query_count()
    assert large == small
    assert large <= 8


def test_chart_geometry_and_period_thresholds_are_literal():
    """AC-22.7 — Mặt trước đúng tỷ lệ, chiều sâu 6px; mốc nhóm 45/180 ngày."""
    from crm.services import statistics_charts, statistics_profiles

    chart = statistics_charts.bar("Đơn", [
        {"label": "A", "value": 10}, {"label": "B", "value": 5},
    ])
    assert Decimal(chart["groups"][0]["width"]) == Decimal(520)
    assert Decimal(chart["groups"][1]["width"]) == Decimal(260)
    assert chart["groups"][0]["depth_points"].startswith("520.00,4 526.00,0")
    assert statistics_profiles.period_granularity(
        date(2026, 9, 1), date(2026, 10, 15),
    ) == "day"
    assert statistics_profiles.period_granularity(
        date(2026, 1, 1), date(2026, 6, 29),
    ) == "week"
    assert statistics_profiles.period_granularity(
        date(2026, 1, 1), date(2026, 6, 30),
    ) == "month"
