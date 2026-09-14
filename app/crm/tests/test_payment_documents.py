"""AC-26: trạng thái thủ công và chứng từ theo quyền dòng."""
import uuid

import pytest
from .test_waybill_feedback import feedback, assign_rows
from .test_master_grid import BASE, write
from orders.services import waybill_service

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def payment_storage(settings, tmp_path):
    settings.STORAGE_DIR = tmp_path


def image_upload():
    import base64
    from django.core.files.uploadedfile import SimpleUploadedFile
    return SimpleUploadedFile('test.png', base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII='), content_type='image/png')


def create_document(client, row, operation=None, reference='000123'):
    return client.post('/chung-tu-thanh-toan/tao/', {'record': row.pk, 'reference': reference,
        'operation': operation or str(uuid.uuid4()), 'images': image_upload()})


def test_document_create_replay_private_image_and_cas(client, feedback, nguoi_dung):
    from orders.models import PaymentDocument
    client.force_login(nguoi_dung['admin'])
    row = feedback[2][0]
    operation = str(uuid.uuid4())
    created = create_document(client, row, operation)
    assert created.status_code == 200, created.content
    pk = created.json()['id']
    assert create_document(client, row, operation).json()['id'] == pk
    assert PaymentDocument.objects.count() == 1
    assert create_document(client, row, reference=' 000123 ').status_code == 400
    detail = client.get(f'/chung-tu-thanh-toan/{pk}/').json()
    image = client.get(detail['images'][0]['url'])
    assert image.status_code == 200
    assert 'no-store' in image['Cache-Control']
    url = f'/chung-tu-thanh-toan/{pk}/sua/'
    assert client.post(url, {'version': 1, 'action': 'edit', 'reference': 'NEW'}).status_code == 200
    assert client.post(url, {'version': 1, 'action': 'delete'}).status_code == 409
    client.force_login(nguoi_dung['staff_vd'])
    assert client.get(detail['images'][0]['url']).status_code == 403
    assert create_document(client, row).status_code == 403


def test_delivery_add_only_and_accounting_read_not_edit(client, feedback, nguoi_dung, make_user):
    from core.constants import Rank
    from org.models import Department
    from forms_builder.services import grant_service
    row = feedback[2][0]
    delivery = nguoi_dung['staff_vd']
    assign_rows(nguoi_dung['admin'], [row], delivery=delivery.pk)
    client.force_login(delivery)
    response = create_document(client, row)
    assert response.status_code == 200, response.content
    pk = response.json()['id']
    assert client.post(f'/chung-tu-thanh-toan/{pk}/sua/', {'version': 1, 'action': 'delete'}).status_code == 403
    accountant = make_user('accountant_doc', Rank.STAFF, Department.objects.get(code='ke-toan'))
    client.force_login(accountant)
    assert client.get(BASE + 'du-lieu/').status_code == 200
    assert not grant_service.can_edit_record(accountant, row)
    assert client.post(f'/chung-tu-thanh-toan/{pk}/sua/', {'version': 1, 'action': 'delete'}).status_code == 200
    assert client.post(f'/chung-tu-thanh-toan/{pk}/sua/', {'version': 2, 'action': 'restore'}).status_code == 200


def test_manual_payment_status_preserves_money(client, feedback, nguoi_dung):
    client.force_login(nguoi_dung['admin'])
    row = feedback[2][0]
    before = dict(row.data)
    operation = str(uuid.uuid4())
    response = write(client, row, column='trang_thai_tt', old=before['trang_thai_tt'],
                     value='Đã thanh toán', operation=operation)
    assert response.status_code == 200
    row.refresh_from_db()
    assert row.data == {**before, 'trang_thai_tt': 'Đã thanh toán'}
    assert write(client, row, column='trang_thai_tt', old=before['trang_thai_tt'],
                 value='Đã thanh toán', operation=operation).json()['replayed']
    assert write(client, row, column='trang_thai_tt', old=before['trang_thai_tt'],
                 value='Thanh toán 1 phần').status_code == 409
    for value in ['Thanh toán 1 phần', 'Chưa thanh toán', 'Đã thanh toán']:
        old = row.data['trang_thai_tt']
        assert write(client, row, column='trang_thai_tt', old=old, value=value).status_code == 200
        row.refresh_from_db()
        assert row.data == {**before, 'trang_thai_tt': value}
        # Undo dùng cùng CAS, đảo đúng giá trị vừa xác nhận.
        assert write(client, row, column='trang_thai_tt', old=value, value=old).status_code == 200
        row.refresh_from_db()


def test_explicit_import_status_is_kept(feedback):
    import json
    from core.exceptions import BusinessError
    values = {'chi_tiet_sp': json.dumps([{'product': feedback[1][0].code, 'quantity': 1,
                'unit_price': '10', 'paid_amount': '10'}]), 'trang_thai_tt': 'Chưa thanh toán'}
    assert waybill_service.prepare_values(values)['trang_thai_tt'] == 'Chưa thanh toán'
    with pytest.raises(BusinessError):
        waybill_service.prepare_values({**values, 'trang_thai_tt': 'Tự đặt trạng thái'})


def test_items_do_not_overwrite_manual_status(feedback, nguoi_dung):
    row = feedback[2][0]
    row.data['trang_thai_tt'] = 'Thanh toán 1 phần'
    row.save()
    waybill_service.update_items(nguoi_dung['admin'], row.pk,
        [{'product': feedback[1][0].code, 'quantity': 1, 'unit_price': '10', 'paid_amount': '10'}],
        row.updated_at.isoformat())
    row.refresh_from_db()
    assert row.data['trang_thai_tt'] == 'Thanh toán 1 phần'


def test_document_library_entrypoint(client, feedback, nguoi_dung):
    client.force_login(nguoi_dung['admin'])
    response = client.get('/chung-tu-thanh-toan/')
    assert response.status_code == 200
    assert 'Kho ảnh' in response.content.decode()


def test_bill_metadata_filter_export_and_write_protection(client, feedback, nguoi_dung):
    from crm.services import grid_service
    from forms_builder.services.export_service import rows_of
    from forms_builder import query
    row = feedback[2][0]
    row.data['bill'] = 'Bill cũ'
    row.save()
    client.force_login(nguoi_dung['admin'])
    for ref in ['REF-A', 'REF-B', 'REF-C']:
        assert create_document(client, row, reference=ref).status_code == 200
    payload = client.get(BASE + 'du-lieu/').json()
    cell = next(r for r in payload['rows'] if r['id'] == row.pk)['cells']['bill']
    assert cell['value'] == 'Bill cũ'
    assert cell['payments']['count'] == 3
    assert len(cell['payments']['links']) == 2
    assert 'file_path' not in str(payload)
    assert write(client, row, column='bill', old='Bill cũ', value='URL').status_code == 400
    filtered = client.get(BASE + 'du-lieu/', {'f_bill__chua': 'REF-B'}).json()
    assert [r['id'] for r in filtered['rows']] == [row.pk]
    column = feedback[0].columns.get(code='bill')
    assert ('REF-B', 1) in grid_service.filter_options(nguoi_dung['admin'], feedback[0], column)
    from forms_builder.models import DataRecord
    records = DataRecord.objects.in_scope(nguoi_dung['admin']).filter(pk=row.pk)
    columns = list(feedback[0].columns.all())
    result = next(rows_of(records, columns))
    assert result[next(i for i, c in enumerate(columns) if c.code == 'bill')] == 'REF-A; REF-B; REF-C; Bill cũ'


def test_upload_validation_and_failed_save_cleanup(client, feedback, nguoi_dung, settings, monkeypatch):
    from pathlib import Path
    from orders.models import PaymentDocument
    from orders.services import payment_service
    from django.core.files.uploadedfile import SimpleUploadedFile
    client.force_login(nguoi_dung['admin'])
    payload = {'record': feedback[2][0].pk, 'reference': 'TEST', 'operation': str(uuid.uuid4())}
    assert client.post('/chung-tu-thanh-toan/tao/', {**payload, 'images': SimpleUploadedFile('fake.png', b'not-image')}).status_code == 400
    assert client.post('/chung-tu-thanh-toan/tao/', {**payload, 'images': [image_upload() for _ in range(6)]}).status_code == 400
    def fail(*args, **kwargs):
        raise RuntimeError('test rollback')
    monkeypatch.setattr(payment_service, 'changed', fail)
    with pytest.raises(RuntimeError):
        create_document(client, feedback[2][0])
    assert not PaymentDocument.objects.exists()
    assert not list((Path(settings.STORAGE_DIR) / payment_service.SUBDIR).glob('*'))


def test_metadata_queries_bounded(feedback, nguoi_dung, django_assert_num_queries):
    from orders.services.payment_service import metadata
    from orders.models import PaymentDocument
    row = feedback[2][0]
    PaymentDocument.objects.bulk_create([PaymentDocument(record=row, reference=f'REF-{i}',
        created_by=nguoi_dung['admin'], updated_by=nguoi_dung['admin'], operation=uuid.uuid4(), fingerprint='x') for i in range(100)])
    with django_assert_num_queries(1):
        result = metadata([r.pk for r in feedback[2]])
    assert result[row.pk]['count'] == 100
    assert len(result[row.pk]['links']) == 2


@pytest.mark.django_db(transaction=True)
def test_payment_migrations_preserve_legacy_rows(feedback):
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor
    row = feedback[2][0]
    row.data.update(bill='Chứng từ cũ giữ nguyên', trang_thai_tt='')
    row.save()
    original = dict(row.data)
    executor = MigrationExecutor(connection)
    targets = executor.loader.graph.leaf_nodes()
    try:
        executor.migrate([('orders', '0006_line_unit_snapshot'), ('org', '0003_userprofile_birthday')])
        assert 'orders_paymentdocument' not in connection.introspection.table_names()
        row.refresh_from_db()
        assert row.data == original
    finally:
        MigrationExecutor(connection).migrate(targets)
    row.refresh_from_db()
    assert row.data == original
    from org.models import Department
    assert Department.objects.filter(code='ke-toan').exists()


@pytest.mark.django_db(transaction=True)
def test_concurrent_document_edit_one_wins(feedback, nguoi_dung):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.contrib.auth import get_user_model
    from django.db import close_old_connections, connections
    from core.exceptions import BusinessError
    from orders.services import payment_service
    document = payment_service.create(nguoi_dung['admin'], feedback[2][0].pk, 'CONCURRENT', '', '',
                                      [image_upload()], uuid.uuid4())
    barrier = Barrier(2)
    def edit(reference):
        close_old_connections()
        try:
            user = get_user_model().objects.get(pk=nguoi_dung['admin'].pk)
            barrier.wait(timeout=10)
            payment_service.update(user, document.pk, 1, 'edit', reference=reference)
            return 'saved'
        except BusinessError as exc:
            return exc.code
        finally:
            connections.close_all()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(edit, ['LEFT', 'RIGHT']))
    assert sorted(results) == ['conflict', 'saved']
    document.refresh_from_db()
    assert document.version == 2
