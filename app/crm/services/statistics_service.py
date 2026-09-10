"""Số liệu theo tập dòng được phép xem; SVG chỉ biểu diễn số đếm/số lượng."""
from decimal import Decimal
from django.db.models import Count, Sum, Value, TextField
from django.db.models.functions import NullIf
from django.db.models.fields.json import KeyTextTransform
from orders.models import WaybillItem
from core.pagination import paginate
from orders.services import waybill_service

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
    totals, _ = waybill_service.statistics(records, 'total')
    totals = list(totals)
    items = WaybillItem.objects.for_records(records)
    orders = records.count()
    missing = records.exclude(pk__in=items.values('record_id')).count()
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
