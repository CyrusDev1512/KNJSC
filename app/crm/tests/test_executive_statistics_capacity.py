"""AC-22.9 — phép đo chủ động, chỉ chạy trên database test riêng."""
import os
import statistics
import time
import tracemalloc
from datetime import date
from decimal import Decimal

import pytest
from django.db import connection
from django.test import Client

from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, DataRecord, TableDef
from orders.models import WaybillItem

from .test_waybill_feedback import feedback


def _percentile(values, percentile):
    ordered = sorted(values)
    return ordered[max(0, min(len(ordered) - 1, int(len(ordered) * percentile) - 1))]


def _measure(client, url, label, requests=20):
    for _ in range(3):
        assert client.get(url).status_code == 200
    query_count = [0]
    query_timings = []

    def count_query(execute, sql, params, many, context):
        query_count[0] += 1
        started = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            query_timings.append(((time.perf_counter() - started) * 1_000, sql))

    with connection.execute_wrapper(count_query):
        assert client.get(url).status_code == 200
    elapsed = []
    for _ in range(requests):
        started = time.perf_counter()
        assert client.get(url).status_code == 200
        elapsed.append((time.perf_counter() - started) * 1_000)
    tracemalloc.start()
    assert client.get(url).status_code == 200
    _, python_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    result = {
        "label": label,
        "requests": requests,
        "queries": query_count[0],
        "p50_ms": round(statistics.median(elapsed), 2),
        "p95_ms": round(_percentile(elapsed, .95), 2),
        "max_ms": round(max(elapsed), 2),
        "python_peak_mib": round(python_peak / 1024 / 1024, 2),
        "slow_queries": [
            {"ms": round(milliseconds, 2), "sql": " ".join(sql.split())[:180]}
            for milliseconds, sql in sorted(query_timings, reverse=True)[:5]
        ],
    }
    print(result, flush=True)
    return result


def _expand(source, table, target, *, sale=False):
    current = DataRecord.objects.filter(table=table).count()
    if current >= target:
        return
    fields = [field for field in DataRecord._meta.concrete_fields if field.name != "id"]
    columns = ", ".join(f'"{field.column}"' for field in fields)
    values = []
    for field in fields:
        quoted = f's."{field.column}"'
        if field.name == "data":
            if sale:
                values.append(
                    "s.data || jsonb_build_object('nguoi_ban','Sale '||mod(g,25),"
                    "'san_pham','Sản phẩm '||mod(g,10),'so_don',1,'doanh_thu',100,"
                    "'loai_tien',(ARRAY['VND','USD','CAD','PHP'])[1+mod(g,4)])"
                )
            else:
                values.append(
                    "s.data || jsonb_build_object('ma_don','EXEC-'||g,"
                    "'quoc_gia',(ARRAY['Canada','USA','Philippines'])[1+mod(g,3)])"
                )
        elif sale and field.name == "val_seller":
            values.append("'Sale '||mod(g,25)")
        elif sale and field.name == "val_product":
            values.append("'Sản phẩm '||mod(g,10)")
        else:
            values.append(quoted)
    with connection.cursor() as cursor:
        cursor.execute(
            f"INSERT INTO forms_builder_datarecord ({columns}) "
            f"SELECT {', '.join(values)} FROM forms_builder_datarecord s "
            "CROSS JOIN generate_series(%s,%s) g WHERE s.id=%s",
            [current, target - 1, source.pk],
        )
        cursor.execute("ANALYZE forms_builder_datarecord")


def _sale_table(department, actor):
    table = TableDef.objects.create(
        department=department, created_by=actor,
        code="sale_exec_capacity", name="Sale capacity",
    )
    definitions = (
        ("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
        ("Người bán", "nguoi_ban", FieldType.TEXT, Meaning.SELLER),
        ("Số đơn", "so_don", FieldType.INTEGER, ""),
        ("Doanh thu", "doanh_thu", FieldType.MONEY, Meaning.REVENUE),
        ("Sản phẩm", "san_pham", FieldType.TEXT, Meaning.PRODUCT),
        ("Loại tiền", "loai_tien", FieldType.CHOICE, ""),
    )
    for order, (name, code, field_type, meaning) in enumerate(definitions):
        ColumnDef.objects.create(
            table=table, order=order, name=name, code=code,
            field_type=field_type, meaning=meaning,
        )
    seed = DataRecord.objects.create(
        table=table, department=department, created_by=actor,
        val_date=date(2026, 9, 11), val_revenue=Decimal(100),
        val_seller="Sale 0", val_product="Sản phẩm 0",
        data={"ngay": "2026-09-11", "nguoi_ban": "Sale 0", "so_don": 1,
              "doanh_thu": 100, "san_pham": "Sản phẩm 0", "loai_tien": "VND"},
    )
    _expand(seed, table, 20_000, sale=True)
    return table


@pytest.mark.cham
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(
    os.environ.get("KN_EXECUTIVE_CAPACITY") != "1",
    reason="Kiểm tải chủ động trên DB test riêng",
)
def test_executive_capacity(feedback, departments, nguoi_dung):
    database = connection.settings_dict["NAME"]
    assert database.startswith("test_")
    table, products, source = feedback
    admin = nguoi_dung["admin"]
    sale = _sale_table(departments["sale"], admin)
    client = Client(HTTP_HOST="localhost:8021")
    client.force_login(admin)
    sale_url = "/thong-ke/?nguon=sale_exec_capacity&tu=2026-09-01&den=2026-09-11"
    sale_result = _measure(client, sale_url, "sale-20000")

    waybill_url = "/thong-ke/?nguon=van_don_moi&tu=2026-09-01&den=2026-09-11"
    counts = []
    for count in (100_000, 300_000):
        _expand(source[0], table, count)
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO orders_waybillitem "
                "(created_at,updated_at,record_id,product_id,quantity,unit_price,paid_amount) "
                "SELECT r.created_at,r.updated_at,r.id,%s,1,10,0 "
                "FROM forms_builder_datarecord r WHERE r.table_id=%s "
                "AND NOT EXISTS (SELECT 1 FROM orders_waybillitem i WHERE i.record_id=r.id)",
                [products[0].pk, table.pk],
            )
            cursor.execute("ANALYZE orders_waybillitem")
        counts.append(_measure(client, waybill_url, f"waybill-{count}"))
    assert counts[0]["queries"] == counts[1]["queries"]
    assert counts[1]["python_peak_mib"] <= counts[0]["python_peak_mib"] * 1.5 + 5
    overview = _measure(
        client,
        "/thong-ke/?sale_nguon=sale_exec_capacity&vd_nguon=van_don_moi"
        "&tu=2026-09-01&den=2026-09-11",
        "overview-20000-300000",
    )
    assert overview["queries"] < sale_result["queries"] + counts[-1]["queries"] + 10
    assert max(item["p95_ms"] for item in [sale_result, *counts, overview]) <= 1_000
