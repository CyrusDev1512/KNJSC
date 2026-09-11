"""AC-6.3/6.5 — cấp mã liên tiến trình, giao dịch đơn–Vận đơn nguyên tử."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone as utc_timezone
from decimal import Decimal
from threading import Barrier, Event
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection, connections, transaction
from django.test import Client
from django.utils import timezone

from core.exceptions import BusinessError
from orders.constants import Market, PaymentMethod
from orders.models import Customer, Order, OrderLine, WaybillItem
from orders.services import dispatch_service, order_service
from .test_len_don import bang_van_don, san_pham, _len_don

pytestmark = pytest.mark.django_db(transaction=True)


def _worker(actor_id, products, phone, *, barrier=None, pause=None, reached=None, lines=None):
    close_old_connections()
    try:
        actor = get_user_model().objects.get(pk=actor_id)
        if barrier:
            barrier.wait(timeout=10)

        def intercept(execute, sql, params, many, context):
            if pause is not None and sql.startswith('INSERT INTO "orders_order" '):
                reached.set()
                assert pause.wait(timeout=5), "Test chưa giải phóng giao dịch đầu"
            return execute(sql, params, many, context)

        with connection.execute_wrapper(intercept):
            saved = _len_don(actor, products, phone=phone, **({'lines': lines} if lines else {}))
        return saved.pk
    finally:
        connections.close_all()


def test_overlapping_orders_get_distinct_codes(bang_van_don, san_pham, nguoi_dung):
    """Giao dịch đầu dừng trước INSERT; giao dịch sau có cơ hội cấp mã cùng lúc.

    Không đặt barrier sau khóa. Bản cũ cho giao dịch sau ghi cùng mã; bản sửa
    buộc nó đợi đến khi giao dịch đầu đã commit.
    """
    reached, release = Event(), Event()
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(_worker, nguoi_dung['staff_sale_1'].pk, san_pham,
                            'TEST-CONCURRENT-1', pause=release, reached=reached)
        try:
            assert reached.wait(timeout=5)
            second = pool.submit(_worker, nguoi_dung['staff_sale_2'].pk, san_pham,
                                 'TEST-CONCURRENT-2')
            finished = Event()
            second.add_done_callback(lambda _: finished.set())
            finished.wait(timeout=.6)
        finally:
            release.set()
        ids = [first.result(timeout=10), second.result(timeout=10)]
    assert len(set(Order.objects.filter(pk__in=ids).values_list('code', flat=True))) == 2
    assert all(o.record_id for o in Order.objects.filter(pk__in=ids))


def test_numeric_suffix_continues_past_9999(bang_van_don, san_pham, nguoi_dung):
    actor = nguoi_dung['staff_sale_1']
    instant = datetime(2026, 9, 11, 3, tzinfo=utc_timezone.utc)
    with patch('django.utils.timezone.now', return_value=instant):
        first = _len_don(actor, san_pham)
        Order.all_objects.filter(pk=first.pk).update(code='DH-1109-9999')
        second = _len_don(actor, san_pham)
        third = _len_don(actor, san_pham)
    assert [second.code, third.code] == ['DH-1109-10000', 'DH-1109-10001']


@pytest.mark.parametrize('same_customer', [False, True])
def test_thirty_sales_keep_orders_and_snapshots_complete(
        bang_van_don, san_pham, departments, make_user, same_customer):
    """AC-6.3/6.5 — 30 kết nối riêng, có cả tranh chấp cùng khách hàng."""
    actors = [make_user(f'parallel_sale_{i}', department=departments['sale']) for i in range(30)]
    lines = [{'product': san_pham['massage'], 'quantity': 2, 'unit_price': '10.10'},
             {'product': san_pham['den'], 'quantity': 1, 'unit_price': '20.20'}]
    barrier = Barrier(30)
    with ThreadPoolExecutor(max_workers=30) as pool:
        futures = [pool.submit(_worker, actor.pk, san_pham,
                               'TEST-SHARED' if same_customer else f'TEST-SALE-{i}',
                               barrier=barrier, lines=lines) for i, actor in enumerate(actors)]
        ids = [f.result(timeout=15) for f in futures]
    orders = list(Order.objects.filter(pk__in=ids).select_related('record'))
    assert len(orders) == len({o.code for o in orders}) == 30
    assert {o.seller_id for o in orders} == {u.pk for u in actors}
    by_id = {o.pk: o for o in orders}
    assert all(by_id[pk].seller_id == actor.pk for pk, actor in zip(ids, actors))
    assert len({o.record_id for o in orders}) == 30
    assert all(o.total == Decimal('40.40') and o.record.data['gia_tien'] == '40.40'
               and o.record.data['ma_don'] == o.code for o in orders)
    assert all(o.lines.count() == 2 and WaybillItem.objects.filter(record=o.record).count() == 2
               for o in orders)
    assert Customer.objects.count() == (1 if same_customer else 30)


def test_deleted_and_previous_year_codes_stay_reserved(bang_van_don, san_pham, nguoi_dung):
    actor = nguoi_dung['staff_sale_1']
    with patch('django.utils.timezone.now', return_value=datetime(2026, 9, 11, 3, tzinfo=utc_timezone.utc)):
        first = _len_don(actor, san_pham)
        order_service.cancel_order(first, actor=actor)
        second = _len_don(actor, san_pham)
        assert first.code == 'DH-1109-0001' and second.code == 'DH-1109-0002'
    with patch('django.utils.timezone.now', return_value=datetime(2026, 9, 12, 3, tzinfo=utc_timezone.utc)):
        assert _len_don(actor, san_pham).code == 'DH-1209-0001'
    with patch('django.utils.timezone.now', return_value=datetime(2027, 9, 11, 3, tzinfo=utc_timezone.utc)):
        assert _len_don(actor, san_pham).code == 'DH-1109-0003'


def test_vietnam_date_and_non_numeric_legacy_suffix(bang_van_don, san_pham, nguoi_dung):
    actor = nguoi_dung['staff_sale_1']
    with patch('django.utils.timezone.now', return_value=datetime(2026, 9, 10, 18, tzinfo=utc_timezone.utc)):
        old = _len_don(actor, san_pham)
        Order.all_objects.filter(pk=old.pk).update(code='DH-1109-legacy')
        assert _len_don(actor, san_pham).code == 'DH-1109-0001'


def test_dispatch_failure_releases_lock_for_another_connection(bang_van_don, san_pham, nguoi_dung):
    actor = nguoi_dung['staff_sale_1']
    with patch.object(dispatch_service, 'push', side_effect=BusinessError('TEST rollback')):
        with pytest.raises(BusinessError, match='TEST rollback'):
            _len_don(actor, san_pham)
    assert not Order.all_objects.exists()
    assert not OrderLine.objects.exists()
    assert not Customer.objects.exists()
    with ThreadPoolExecutor(max_workers=1) as pool:
        pk = pool.submit(_worker, actor.pk, san_pham, 'TEST-AFTER-ROLLBACK').result(timeout=10)
    assert Order.objects.get(pk=pk).record_id


def _hold_code_lock(reached, release):
    close_old_connections()
    try:
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute('SELECT pg_advisory_xact_lock(%s, %s)',
                           [order_service.ORDER_CODE_LOCK_NAMESPACE, int(timezone.localdate().strftime('%d%m'))])
            reached.set()
            assert release.wait(timeout=15)
    finally:
        connections.close_all()


def test_lock_timeout_preserves_form_and_restores_connection_setting(
        bang_van_don, san_pham, nguoi_dung, settings):
    """Đợi 5s thật, rollback trước khi view đọc lại form; gửi lại được khi hết khóa."""
    settings.ROOT_URLCONF = 'knjsc.urls_bangtinh'
    client = Client()
    client.force_login(nguoi_dung['staff_sale_1'])
    payload = {'customer_name': 'Khach TEST timeout', 'phone': 'TEST-LOCK-TIMEOUT',
               'market': Market.US, 'currency': 'USD', 'payment_method': PaymentMethod.CARD,
               'product': san_pham['massage'].code, 'quantity': '2',
               'unit_price': '10.10', 'unit': 'hộp', 'note': 'TEST keep form'}
    reached, release = Event(), Event()
    with ThreadPoolExecutor(max_workers=1) as pool:
        holder = pool.submit(_hold_code_lock, reached, release)
        try:
            assert reached.wait(timeout=5)
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute("SET LOCAL lock_timeout = '17s'")
                response = client.post('/van-don/len-don/', payload)
                assert response.status_code == 400
                assert 'Hệ thống đang bận cấp mã đơn. Vui lòng thử lại.' in response.content.decode()
                assert response.context['form'].data['phone'] == payload['phone']
                assert response.context['items'][0]['product'] == payload['product']
                cursor.execute("SELECT current_setting('lock_timeout')")
                assert cursor.fetchone()[0] == '17s'
                assert not Order.objects.exists() and not Customer.objects.exists()
        finally:
            release.set()
        holder.result(timeout=5)
    response = client.post('/van-don/len-don/', payload)
    assert response.status_code == 200
    assert Order.objects.get().record_id


def test_success_restores_custom_lock_timeout(bang_van_don, san_pham, nguoi_dung):
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("SET LOCAL lock_timeout = '17s'")
        _len_don(nguoi_dung['staff_sale_1'], san_pham)
        cursor.execute("SELECT current_setting('lock_timeout')")
        assert cursor.fetchone()[0] == '17s'
