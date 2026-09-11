"""Bộ điều phối Bàn điều hành và lớp tương thích thống kê Vận đơn cũ."""
import logging
from decimal import Decimal
from django.db.models import Count, Max, Sum, Value, TextField
from django.db.models.functions import NullIf
from django.db.models.fields.json import KeyTextTransform
from django.conf import settings

from core.audit import record_denied
from core.constants import Rank
from core.exceptions import OutOfScopeError
from forms_builder.models import DataRecord, TableDef
from orders.models import WaybillItem
from core.pagination import paginate
from orders.services import waybill_service
from orders.constants import ACTIVE_WAYBILL_TABLE_CODE

from . import statistics_charts, statistics_insights, statistics_profiles


logger = logging.getLogger(__name__)

COLORS = ['#3a37a3', '#0b8576', '#b58112', '#ce5246', '#6380b5', '#9b669e', '#787882']


def chart(title, groups, kind, note=''):
    total = sum((g['value'] or 0 for g in groups), 0)
    offset = Decimal(0)
    maximum = max([g['value'] or 0 for g in groups] + [1])
    for i, g in enumerate(groups):
        g['value'] = g['value'] or 0
        pct = Decimal(g['value']) * 100 / Decimal(total) if total else Decimal(0)
        g.update(color=COLORS[i % len(COLORS)], percent=f'{pct:.1f}', dash=f'{pct:.5f} {100-pct:.5f}',
                 offset=f'{-offset:.5f}', width=f'{Decimal(g["value"])*480/Decimal(maximum):.3f}', y=18+i*36)
        offset += pct
    return {'title': title, 'groups': groups, 'kind': kind, 'total': total, 'note': note,
            'height': max(70, len(groups)*36+10)}


def status_groups(records, field):
    return [{'label': row['label'] or 'Chưa có trạng thái', 'value': row['value']}
            for row in records.order_by().annotate(label=NullIf(KeyTextTransform(field, 'data'), Value('', output_field=TextField())))
            .values('label').annotate(value=Count('pk')).order_by('-value', 'label')]


def build(records, request=None):
    totals = waybill_service.statistics_totals(records)
    items = WaybillItem.objects.for_records(records)
    orders = records.count()
    missing = waybill_service.missing_item_count(records)
    market_query = records.order_by().annotate(label=NullIf(KeyTextTransform('quoc_gia', 'data'), Value('', output_field=TextField()))).values('label').annotate(value=Count('pk')).order_by('-value', 'label')
    product_query = items.order_by().values('product__code', 'product__name').annotate(value=Sum('quantity')).order_by('-value', 'product__code')
    market_label = lambda r: {'label': r['label'] or 'Chưa có thị trường', 'value': r['value']}
    product_label = lambda r: {'label': f'{r["product__name"]} ({r["product__code"]})', 'value': r['value']}
    markets = [market_label(r) for r in market_query[:10]]
    products = [product_label(r) for r in product_query[:10]]
    charts = [
        chart('Trạng thái giao hàng', status_groups(records, 'trang_thai_vc'), 'donut', 'Tỷ trọng theo số đơn'),
        chart('Trạng thái thanh toán', status_groups(records, 'trang_thai_tt'), 'donut', 'Tỷ trọng số đơn, không phải tỷ lệ thu tiền'),
        chart('Đơn theo thị trường', markets, 'bar', '10 thị trường có nhiều đơn nhất'),
        chart('Số lượng theo sản phẩm', products, 'bar', '10 sản phẩm có số lượng lớn nhất'),
    ]

    for item in charts:
        item['table_groups'] = item['groups']
    if request is not None:
        for item, query, label, key in ((charts[2], market_query, market_label, 'chart_market'), (charts[3], product_query, product_label, 'chart_product')):
            page = paginate(request, query, param=key)
            item['table_groups'] = [label(r) for r in page.object_list]
            item['page'] = page
            params = request.GET.copy(); params.pop(key, None)
            item['page_url'] = '?' + params.urlencode() + '&' + key + '='
    return {'orders': orders, 'missing': missing, 'totals': totals,
            'quantity': sum((r['quantity_total'] or 0 for r in totals), 0)}, charts


def source_tables(user):
    """Mọi bảng đang hoạt động trong phạm vi, kể cả bảng chưa đủ cấu hình thống kê."""
    return list(
        TableDef.objects.in_scope(user)
        .filter(is_active=True)
        .select_related("department")
        .prefetch_related("columns")
        .order_by("name", "id")
    )


def describe_sources(tables):
    labels = {
        "marketing": "Marketing",
        "sale": "Sale",
        "waybill": "Vận đơn",
        "generic": "Chung",
    }
    sources = []
    for table in tables:
        profile = statistics_profiles.profile_of(table, list(table.columns.all()))
        sources.append({
            "code": table.code,
            "name": table.name,
            "department": table.department.name,
            "profile": profile,
            "profile_label": labels[profile],
        })
    return sources


def resolve_source(user, code, tables, request=None):
    """Mã không nằm trong danh sách đang hoạt động/được xem luôn trả 403."""
    by_code = {table.code: table for table in tables}
    table = by_code.get(code)
    if table is not None:
        return table
    record_denied(user, f"thong-ke/?nguon={code}", request)
    raise OutOfScopeError()


def _latest_by_table(user, tables):
    table_ids = [table.pk for table in tables]
    if not table_ids:
        return {}
    return {
        row["table_id"]: row["latest"]
        for row in (
            DataRecord.objects.in_scope(user)
            .filter(table_id__in=table_ids)
            .order_by()
            .values("table_id")
            .annotate(latest=Max("updated_at"))
        )
    }


def default_sources(user, tables):
    """Chọn một bảng mới cập nhật nhất cho mỗi profile; Vận đơn ưu tiên bảng mới."""
    latest = _latest_by_table(user, tables)
    candidates = {"marketing": [], "sale": [], "waybill": []}
    for table in tables:
        profile = statistics_profiles.profile_of(table, list(table.columns.all()))
        if profile in candidates:
            candidates[profile].append(table)
    selected = {}
    for profile, profile_tables in candidates.items():
        if not profile_tables:
            selected[profile] = None
            continue
        if profile == "waybill":
            preferred = next(
                (table for table in profile_tables
                 if table.code == ACTIVE_WAYBILL_TABLE_CODE),
                None,
            )
            if preferred is not None:
                selected[profile] = preferred
                continue
        selected[profile] = max(
            profile_tables,
            key=lambda table: (latest.get(table.pk) is not None,
                               latest.get(table.pk), -table.pk),
        )
    return selected


def _unavailable(table, profile):
    logger.exception(
        "Không dựng được thống kê profile %s cho bảng %s", profile, table.code,
    )
    return {
        "ok": False,
        "profile": profile,
        "title": {
            "marketing": "Marketing", "sale": "Sale", "waybill": "Vận đơn",
            "generic": table.name,
        }[profile],
        "source_name": table.name,
        "source_code": table.code,
        "missing": [],
        "metrics": [],
        "money": [],
        "ratios": [],
        "aov": [],
        "charts": [],
        "insights": [],
        "open_url": f"/bang-tinh/{table.code}/",
        "message": "Phần số liệu này tạm chưa khả dụng. Các nguồn còn lại vẫn được hiển thị.",
        "orders": None,
        "time_rows": [],
    }


def build_dashboard(user, table, date_from, date_to, *, records=None, summary=False):
    records = records if records is not None else DataRecord.objects.in_scope(user, table=table)
    profile = statistics_profiles.profile_of(table, list(table.columns.all()))
    try:
        return statistics_profiles.BUILDERS[profile](
            table, records, list(table.columns.all()), date_from, date_to,
            summary=summary,
        )
    except Exception:  # Một profile lỗi không làm mất cả bàn điều hành.
        return _unavailable(table, profile)


def _picked_overview_sources(user, tables, params, request=None):
    picked = default_sources(user, tables)
    keys = {
        "marketing": "mkt_nguon",
        "sale": "sale_nguon",
        "waybill": "vd_nguon",
    }
    for profile, key in keys.items():
        code = (params.get(key) or "").strip()
        if not code:
            continue
        table = resolve_source(user, code, tables, request)
        if statistics_profiles.profile_of(table, list(table.columns.all())) != profile:
            # Đây là mã có thật trong phạm vi, nhưng không đúng loại ô chọn.
            picked[profile] = None
        else:
            picked[profile] = table
    return picked


def _overview_chart(sections):
    sale = sections.get("sale")
    waybill = sections.get("waybill")
    charts = []
    if sale and waybill and sale.get("ok") and waybill.get("ok"):
        sale_points = {row["label"]: row["value"] for row in sale["time_rows"]}
        waybill_points = {row["label"]: row["value"] for row in waybill["time_rows"]}
        labels = list(dict.fromkeys([*sale_points, *waybill_points]))
        charts.append(statistics_charts.line(
            "Nhịp đơn Sale – Vận đơn",
            labels,
            [
                {"label": "Sale", "values": [sale_points.get(label, 0) for label in labels]},
                {"label": "Vận đơn", "values": [waybill_points.get(label, 0) for label in labels]},
            ],
            "Hai tổng chỉ được đối chiếu cùng kỳ; chưa nối từng đơn.",
            value_label="Số đơn",
        ))
        difference = Decimal(sale["orders"] or 0) - Decimal(waybill["orders"] or 0)
        charts.append(statistics_charts.bar(
            "Tổng đơn cần đối chiếu",
            [
                {"label": "Sale", "value": sale["orders"] or 0},
                {"label": "Vận đơn", "value": waybill["orders"] or 0},
            ],
            f"Chênh lệch {abs(difference)} đơn; không kết luận đơn thất lạc.",
            value_label="Số đơn",
        ))
    if waybill and waybill.get("ok"):
        attention = [
            row for row in waybill.get("delivery_groups", [])
            if row["label"] in statistics_profiles.ATTENTION_DELIVERY
        ]
        if attention:
            charts.append(statistics_charts.bar(
                "Trạng thái Vận đơn cần kiểm tra",
                attention,
                "Hủy, Hoàn, Khách vắng hoặc Hẹn lại trong kỳ.",
                value_label="Số đơn",
            ))
    return charts


def build_overview(user, tables, params, date_from, date_to, request=None):
    picked = _picked_overview_sources(user, tables, params, request)
    sections = {}
    for profile in ("marketing", "sale", "waybill"):
        table = picked.get(profile)
        if table is not None:
            sections[profile] = build_dashboard(
                user, table, date_from, date_to, summary=True,
            )

    combined_insights = []
    sale = sections.get("sale")
    waybill = sections.get("waybill")
    if sale and waybill and sale.get("ok") and waybill.get("ok"):
        difference = Decimal(sale["orders"] or 0) - Decimal(waybill["orders"] or 0)
        if difference:
            combined_insights.append(statistics_insights.item(
                1,
                "Tổng đơn Sale và Vận đơn chưa khớp",
                f"Sale ghi nhận {sale['orders']} đơn, Vận đơn ghi nhận {waybill['orders']} đơn; chênh {abs(difference)} đơn cần đối chiếu.",
                f"{sale['source_name']} · {waybill['source_name']}",
                waybill["open_url"],
                "warning",
            ))
    for profile in ("marketing", "sale", "waybill"):
        section = sections.get(profile)
        if section:
            combined_insights.extend(section.get("insights", []))
    return {
        "ok": True,
        "profile": "overview",
        "title": "Tổng hợp Marketing – Sale – Vận đơn",
        "sections": sections,
        "selected_sources": {
            profile: table.code if table is not None else ""
            for profile, table in picked.items()
        },
        "metrics": [],
        "money": [],
        "ratios": [],
        "aov": [],
        "missing": [],
        "charts": _overview_chart(sections),
        "insights": statistics_insights.top(combined_insights),
    }


def is_executive_owner(user):
    configured = set(getattr(settings, "EXECUTIVE_OWNER_USERNAMES", []))
    return (
        user.is_active
        and user.username in configured
        and getattr(getattr(user, "profile", None), "rank", None) == Rank.ADMIN
    )
