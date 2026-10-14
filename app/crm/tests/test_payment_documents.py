"""AC-26: trạng thái thủ công và chứng từ theo quyền dòng (ADR-025).

Cờ `PAYMENT_DOCUMENTS_ENABLED` tắt trên VPS: mọi đường chứng từ ra 404. Các bài khoá P0-10 (cuối tệp) giữ đúng các
nhánh từ chối, lượt lặp, đường dẫn tệp — điều kiện bắt buộc trước khi bật lại cờ.
"""
import uuid

import pytest
from .test_waybill_feedback import feedback, assign_rows, cskh_staff, delivery_leader  # noqa: F401
from .test_master_grid import BASE, write
from orders.services import waybill_service

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def payment_storage(settings, tmp_path):
    settings.STORAGE_DIR = tmp_path
    settings.PAYMENT_DOCUMENTS_ENABLED = True


def image_upload(name='test.png'):
    import base64
    from django.core.files.uploadedfile import SimpleUploadedFile
    return SimpleUploadedFile(name, base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII='), content_type='image/png')


def create_document(client, row, operation=None, reference='000123'):
    return client.post('/chung-tu-thanh-toan/tao/', {'record': row.pk, 'reference': reference,
        'operation': operation or str(uuid.uuid4()), 'images': image_upload()})


def test_document_create_replay_private_image_and_cas(client, feedback, nguoi_dung):
    """AC-26.3 — Tạo chứng từ: gửi lại cùng mã lượt không nhân bản, Ref giữ số 0 đầu, trùng Ref bị từ chối, ảnh riêng tư không lưu đệm, sửa có so phiên bản; ngoài phạm vi 403"""
    from orders.models import PaymentDocument
    client.force_login(nguoi_dung['admin'])
    row = feedback[2][0]
    operation = str(uuid.uuid4())
    created = create_document(client, row, operation)
    assert created.status_code == 200, created.content
    assert created.json()['reference'] == '000123'
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
    client.force_login(nguoi_dung['staff_mkt'])   # ngoài phạm vi: Vận đơn nay thấy toàn bảng (ADR-033)
    assert client.get(detail['images'][0]['url']).status_code == 403
    assert create_document(client, row).status_code == 403


def test_delivery_add_only_and_accounting_read_not_edit(client, feedback, nguoi_dung, make_user):
    """AC-26.2 — Vận đơn chỉ thêm chứng từ, không xoá; Kế toán xem toàn bảng, không sửa ô, không phân công, xoá, khôi phục và sửa được chứng từ"""
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
    accountant = make_user('accountant_doc', Rank.STAFF, Department.objects.get_or_create(code='ke-toan', defaults={'name':'Kế toán'})[0])
    client.force_login(accountant)
    assert client.get(BASE + 'du-lieu/').status_code == 200
    assert not grant_service.can_edit_record(accountant, row)
    from orders.services import assignment_service
    assert not assignment_service.can_assign(accountant)
    assert client.post(f'/chung-tu-thanh-toan/{pk}/sua/', {'version': 1, 'action': 'delete'}).status_code == 200
    assert client.post(f'/chung-tu-thanh-toan/{pk}/sua/', {'version': 2, 'action': 'restore'}).status_code == 200
    sua = client.post(f'/chung-tu-thanh-toan/{pk}/sua/', {'version': 3, 'action': 'edit', 'reference': 'KT-SUA',
                                                          'images': image_upload('moi.png')})
    assert sua.status_code == 200 and sua.json()['version'] == 4


def test_manual_payment_status_preserves_money(client, feedback, nguoi_dung):
    """AC-26.1 — Trạng thái thanh toán sửa tay không đụng số tiền; gửi lại cùng mã lượt không ghi đôi; CAS 409; hoàn tác đảo đúng giá trị"""
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
    """AC-26.1 — Nhập tệp giữ trạng thái thanh toán ghi rõ, giá trị lạ bị từ chối"""
    import json
    from core.exceptions import BusinessError
    values = {'quoc_gia': 'Hoa Kỳ', 'chi_tiet_sp': json.dumps([{'product': feedback[1][0].code, 'quantity': 1,
                'unit_price': '10', 'paid_amount': '10'}]), 'trang_thai_tt': 'Chưa thanh toán'}
    assert waybill_service.prepare_values(values)['trang_thai_tt'] == 'Chưa thanh toán'
    with pytest.raises(BusinessError):
        waybill_service.prepare_values({**values, 'trang_thai_tt': 'Tự đặt trạng thái'})


def test_items_do_not_overwrite_manual_status(feedback, nguoi_dung):
    """AC-26.1 — Sửa chi tiết sản phẩm không ghi đè trạng thái thanh toán sửa tay"""
    row = feedback[2][0]
    row.data['trang_thai_tt'] = 'Thanh toán 1 phần'
    row.save()
    waybill_service.update_items(nguoi_dung['admin'], row.pk,
        [{'product': feedback[1][0].code, 'quantity': 1, 'unit_price': '10', 'paid_amount': '10'}],
        row.updated_at.isoformat())
    row.refresh_from_db()
    assert row.data['trang_thai_tt'] == 'Thanh toán 1 phần'


def test_document_library_entrypoint(client, feedback, nguoi_dung):
    """AC-26.5 — Kho ảnh chứng từ mở được từ đường dẫn của nó"""
    client.force_login(nguoi_dung['admin'])
    response = client.get('/chung-tu-thanh-toan/')
    assert response.status_code == 200
    assert 'Kho ảnh' in response.content.decode()


def test_bill_metadata_filter_export_and_write_protection(client, feedback, nguoi_dung):
    """AC-26.5 — Cột Bill hiện số chứng từ và tối đa hai liên kết, lọc và xuất Excel gồm Ref, không lộ đường dẫn tệp, không sửa tay được"""
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
    """AC-26.4 — Tệp không phải ảnh, quá 5 ảnh bị từ chối; lưu hỏng giữa chừng thì không còn chứng từ hay tệp nào"""
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
    """AC-26.5 — Siêu dữ liệu chứng từ cho một khối dòng là đúng một truy vấn (vế metadata của AC-26.6)"""
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
    """AC-26.1 — Migration chứng từ chạy ngược xuôi giữ nguyên dữ liệu cũ của dòng vận đơn"""
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
        # Đang đứng ở trạng thái lịch sử: các cột model thêm sau (vd `val_phone_key`,
        # forms_builder/0016) chưa tồn tại, nên chỉ đọc đúng cột `data` thay vì
        # `refresh_from_db()` kéo cả model hiện tại
        assert type(row).all_objects.values_list('data', flat=True).get(pk=row.pk) == original
    finally:
        MigrationExecutor(connection).migrate(targets)
    row.refresh_from_db()
    assert row.data == original
    from org.models import Department
    assert Department.objects.filter(code='ke-toan').exists()


@pytest.mark.django_db(transaction=True)
def test_concurrent_document_edit_one_wins(feedback, nguoi_dung):
    """AC-26.3 — Hai người sửa cùng chứng từ một lúc: một người lưu, người kia nhận xung đột"""
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



# ══ Bài khoá P0-10 — kho chứng từ trước khi bật lại cờ (ADR-025) ═══

def _so_tep(settings):
    from pathlib import Path
    from orders.services import payment_service
    goc = Path(settings.STORAGE_DIR) / payment_service.SUBDIR
    return sorted(p.name for p in goc.glob('*')) if goc.exists() else []


@pytest.mark.parametrize('bo_phan', [None, 'ke-toan', 'van-don'])
def test_ceo_doc_duoc_nhung_khong_tao_sua_chung_tu(client, feedback, nguoi_dung, make_user, departments, settings, bo_phan):
    """AC-26.2 — Giám đốc (kể cả mang bộ phận Kế toán hay Vận đơn) xem được chứng từ và ảnh, không tạo, sửa, xoá,
    khôi phục, không lấy danh sách dòng để tạo; không chứng từ, phiên bản hay tệp nào đổi (P0-10)"""
    from core.constants import Rank
    from orders.models import PaymentDocument
    client.force_login(nguoi_dung['admin'])
    pk = create_document(client, feedback[2][0]).json()['id']
    anh = client.get(f'/chung-tu-thanh-toan/{pk}/').json()['images'][0]['url']
    ceo = make_user('ceo_chung_tu', Rank.CEO, departments['kt'] if bo_phan == 'ke-toan' else
                    departments['vd'] if bo_phan == 'van-don' else None)
    tep, phien_ban = _so_tep(settings), PaymentDocument.objects.get(pk=pk).version
    client.force_login(ceo)
    ct = client.get(f'/chung-tu-thanh-toan/{pk}/')
    assert ct.status_code == 200 and ct.json()['can_manage'] is False
    r = client.get(anh)
    assert r.status_code == 200
    b''.join(r.streaming_content)
    assert create_document(client, feedback[2][0], reference='CEO').status_code == 403
    for hanh_dong in ('edit', 'delete', 'restore'):
        assert client.post(f'/chung-tu-thanh-toan/{pk}/sua/', {'version': phien_ban, 'action': hanh_dong,
                                                               'reference': 'CEO'}).status_code == 403
    assert client.get('/chung-tu-thanh-toan/don/').status_code == 403
    assert PaymentDocument.objects.count() == 1 and PaymentDocument.objects.get(pk=pk).version == phien_ban
    assert _so_tep(settings) == tep


@pytest.mark.parametrize('ai,duoc', [('staff_sale_1', False), ('leader_sale_1', False), ('manager_sale', False),
                                     ('staff_mkt', False), ('manager_mkt', False), ('cskh', False), ('ceo', False),
                                     ('staff_vd', True), ('leader_vd', True), ('staff_kt', True), ('admin', True)])
def test_chi_van_don_ke_toan_admin_lay_duoc_danh_sach_dong(client, feedback, nguoi_dung, ai, duoc):
    """AC-26.2 — Danh sách dòng để tạo chứng từ và nút tạo chỉ cho Vận đơn, Kế toán, Admin: Sale, Marketing, CSKH,
    Giám đốc 403 và không có chứng từ nào; vai được phép thấy đủ các dòng vận đơn (ADR-033, P0-10)"""
    from orders.models import PaymentDocument
    client.force_login(nguoi_dung[ai])
    r = client.get('/chung-tu-thanh-toan/don/')
    tao = create_document(client, feedback[2][0])
    if duoc:
        assert r.status_code == 200 and {d['id'] for d in r.json()['rows']} >= {feedback[2][0].pk, feedback[2][1].pk}
        assert tao.status_code == 200
    else:
        assert r.status_code == 403
        assert tao.status_code == 403 and tao.json()['error'] == 'Bạn không còn quyền truy cập chứng từ này.'
        assert not PaymentDocument.objects.exists()


def test_tuyen_chung_tu_chi_co_o_kn_crm(client, feedback, nguoi_dung, settings):
    """AC-26.2 — Đường chứng từ chỉ có ở KN CRM: ở KN ERP là 404 kể cả với Admin (P0-10)"""
    settings.ROOT_URLCONF = 'knjsc.urls'
    client.force_login(nguoi_dung['admin'])
    assert client.get('/chung-tu-thanh-toan/don/').status_code == 404


@pytest.mark.parametrize('khac', ['reference', 'anh', 'record'])
def test_tao_lai_cung_ma_luot_khac_noi_dung_tra_409_khong_de_tep(client, feedback, nguoi_dung, settings, khac):
    """AC-26.3 — Gửi lại cùng mã lượt tạo mà nội dung khác (Ref, ảnh, dòng) thì 409, không nhân bản chứng từ, không
    ghi thêm tệp, chứng từ gốc giữ nguyên (P0-10)"""
    from orders.models import PaymentDocument, PaymentImage
    client.force_login(nguoi_dung['admin'])
    lan_dau = str(uuid.uuid4())
    goc = create_document(client, feedback[2][0], lan_dau, reference='GOC')
    assert goc.status_code == 200
    tep = _so_tep(settings)
    goi = {'record': feedback[2][0].pk, 'reference': 'GOC', 'operation': lan_dau, 'images': image_upload()}
    if khac == 'reference':
        goi['reference'] = 'KHAC'
    elif khac == 'anh':
        goi['images'] = image_upload('anh-khac.png')
    else:
        goi['record'] = feedback[2][1].pk
    r = client.post('/chung-tu-thanh-toan/tao/', goi)
    assert r.status_code == 409 and r.json()['error'] == 'Mã lượt tạo đã được dùng cho nội dung khác.'
    assert PaymentDocument.objects.count() == 1 and PaymentImage.objects.count() == 1
    assert _so_tep(settings) == tep
    d = PaymentDocument.objects.get()
    assert (d.reference, d.record_id) == ('GOC', feedback[2][0].pk)


def test_khoi_phuc_chung_tu_trung_ref_bi_tu_choi(client, feedback, nguoi_dung):
    """AC-26.3 — Khôi phục chứng từ đã xoá mà dòng đã có chứng từ khác cùng Ref (không phân biệt hoa thường) thì bị
    từ chối, chứng từ vẫn ở trạng thái xoá (P0-10)"""
    from orders.models import PaymentDocument
    client.force_login(nguoi_dung['admin'])
    a = create_document(client, feedback[2][0], reference='X').json()['id']
    assert client.post(f'/chung-tu-thanh-toan/{a}/sua/', {'version': 1, 'action': 'delete'}).status_code == 200
    assert create_document(client, feedback[2][0], reference='x').status_code == 200
    r = client.post(f'/chung-tu-thanh-toan/{a}/sua/', {'version': 2, 'action': 'restore'})
    assert r.status_code == 400 and 'Ref này đã tồn tại' in r.json()['error']
    goc = PaymentDocument.objects.get(pk=a)
    assert goc.deleted_at is not None and goc.version == 2
    assert PaymentDocument.objects.filter(deleted_at__isnull=True).count() == 1


def test_go_anh_khong_thuoc_chung_tu_va_khong_chuyen_don(client, feedback, nguoi_dung):
    """AC-26.4 — Sửa chứng từ không gỡ được ảnh của chứng từ khác, không gỡ hết ảnh, không chuyển chứng từ sang
    đơn khác; gỡ một ảnh kèm ảnh mới thì được (P0-10)"""
    from orders.models import PaymentDocument, PaymentImage
    client.force_login(nguoi_dung['admin'])
    a = create_document(client, feedback[2][0], reference='A').json()['id']
    b = create_document(client, feedback[2][0], reference='B').json()['id']
    anh_a = PaymentImage.objects.get(document_id=a).pk
    anh_b = PaymentImage.objects.get(document_id=b).pk
    url = f'/chung-tu-thanh-toan/{a}/sua/'
    r = client.post(url, {'version': 1, 'action': 'edit', 'reference': 'A', 'remove': anh_b})
    assert r.status_code == 400 and r.json()['error'] == 'Ảnh cần gỡ không thuộc chứng từ.'
    assert PaymentImage.objects.get(pk=anh_b).deleted_at is None and PaymentDocument.objects.get(pk=a).version == 1
    assert client.post(url, {'version': 1, 'action': 'edit', 'reference': 'A', 'remove': 'abc'}).status_code == 400
    r = client.post(url, {'version': 1, 'action': 'edit', 'reference': 'A', 'remove': anh_a})
    assert r.status_code == 400 and r.json()['error'] == 'Chứng từ cần giữ ít nhất một ảnh.'
    r = client.post(url, {'version': 1, 'action': 'edit', 'reference': 'A2', 'record': feedback[2][1].pk})
    assert r.status_code == 200 and PaymentDocument.objects.get(pk=a).record_id == feedback[2][0].pk
    r = client.post(url, {'version': 2, 'action': 'edit', 'reference': 'A2', 'remove': anh_a,
                          'images': image_upload('thay.png')})
    assert r.status_code == 200
    assert PaymentImage.objects.filter(document_id=a, deleted_at__isnull=True).count() == 1


def test_anh_cua_chung_tu_da_xoa_bi_chan_ca_voi_admin(client, feedback, nguoi_dung):
    """AC-26.4 — Ảnh của chứng từ đã xoá: 403 cả với Admin và Kế toán (đã chốt cùng kế hoạch P0); chi tiết vẫn xem
    được với người quản lý chứng từ; khôi phục thì ảnh xem lại được, tệp còn trên đĩa, không lưu đệm (P0-10)"""
    from orders.models import PaymentImage
    client.force_login(nguoi_dung['admin'])
    pk = create_document(client, feedback[2][0]).json()['id']
    anh = client.get(f'/chung-tu-thanh-toan/{pk}/').json()['images'][0]['url']
    assert client.post(f'/chung-tu-thanh-toan/{pk}/sua/', {'version': 1, 'action': 'delete'}).status_code == 200
    for ai in ('admin', 'staff_kt'):
        client.force_login(nguoi_dung[ai])
        assert client.get(anh).status_code == 403, ai
    client.force_login(nguoi_dung['admin'])
    assert client.get(f'/chung-tu-thanh-toan/{pk}/').json()['deleted'] is True
    client.force_login(nguoi_dung['staff_sale_1'])
    assert client.get(f'/chung-tu-thanh-toan/{pk}/').status_code == 403
    client.force_login(nguoi_dung['admin'])
    assert client.post(f'/chung-tu-thanh-toan/{pk}/sua/', {'version': 2, 'action': 'restore'}).status_code == 200
    r = client.get(anh)
    assert r.status_code == 200 and 'no-store' in r['Cache-Control'] and 'private' in r['Cache-Control']
    b''.join(r.streaming_content)
    cu = PaymentImage.objects.get(document_id=pk).pk
    assert client.post(f'/chung-tu-thanh-toan/{pk}/sua/', {'version': 3, 'action': 'edit', 'reference': 'R',
                                                           'remove': cu, 'images': image_upload('moi.png')}).status_code == 200
    assert client.get(f'/chung-tu-thanh-toan/anh/{cu}/').status_code == 403


def test_loc_record_ngoai_pham_vi_bi_tu_choi_khong_tra_rong(client, feedback, nguoi_dung, cskh_staff):  # noqa: F811
    """AC-26.5 — Kho ảnh lọc theo một dòng ngoài phạm vi thì 403, không trả danh sách rỗng; dòng không tồn tại 403,
    mã hỏng 400; người thấy dòng (kể cả CSKH được giao chăm sóc) nhận đúng chứng từ (P0-10)"""
    row = feedback[2][0]
    client.force_login(nguoi_dung['admin'])
    pk = create_document(client, row).json()['id']
    loc = f'/chung-tu-thanh-toan/?record={row.pk}&json=1'
    for ai in ('staff_sale_2', 'staff_mkt'):
        client.force_login(nguoi_dung[ai])
        assert client.get(loc).status_code == 403, ai
    client.force_login(nguoi_dung['staff_sale_1'])
    assert client.get('/chung-tu-thanh-toan/?record=999999&json=1').status_code == 403
    assert client.get('/chung-tu-thanh-toan/?record=abc&json=1').status_code == 400
    r = client.get(loc)
    assert r.status_code == 200 and [d['id'] for d in r.json()['documents']] == [pk]
    client.force_login(cskh_staff)
    assert client.get(loc).status_code == 403
    assign_rows(nguoi_dung['admin'], [row], care=cskh_staff.pk)
    assert client.get(loc).status_code == 200


@pytest.mark.parametrize('bien_the', ['../ngoai.png', 'tai-lieu/ngoai.png', 'tuyet_doi',
                                      'chung-tu-thanh-toan/../tai-lieu/ngoai.png', 'symlink', 'khong-co.png'])
def test_anh_co_duong_dan_ra_ngoai_thu_muc_khong_doc_duoc(client, feedback, nguoi_dung, settings, tmp_path, bien_the):
    """AC-26.4 — Bản ghi ảnh mang đường dẫn ra ngoài thư mục chứng từ (../, thư mục khác, đường tuyệt đối, liên kết
    mềm) hay tệp không tồn tại: 400 lời tiếng Việt, không trả nội dung tệp, không lỗi 500 (P0-10)"""
    import sys
    from pathlib import Path
    from orders.models import PaymentImage
    from orders.services import payment_service
    if bien_the == 'symlink' and sys.platform == 'win32':
        pytest.skip('Windows không tạo liên kết mềm khi chạy trực tiếp')
    kho = tmp_path / 'kho'
    settings.STORAGE_DIR = kho
    client.force_login(nguoi_dung['admin'])
    pk = create_document(client, feedback[2][0]).json()['id']
    png = (kho / payment_service.SUBDIR).glob('*').__next__().read_bytes()
    (tmp_path / 'ngoai.png').write_bytes(png)
    (kho / 'tai-lieu').mkdir(parents=True, exist_ok=True)
    (kho / 'tai-lieu' / 'ngoai.png').write_bytes(png)
    duong = {'tuyet_doi': str(tmp_path / 'ngoai.png'), 'symlink': f'{payment_service.SUBDIR}/lien-ket.png'}.get(bien_the, bien_the)
    if bien_the == 'symlink':
        (kho / payment_service.SUBDIR / 'lien-ket.png').symlink_to(tmp_path / 'ngoai.png')
    anh = PaymentImage.objects.get(document_id=pk)
    PaymentImage.objects.filter(pk=anh.pk).update(file_path=duong)
    r = client.get(f'/chung-tu-thanh-toan/anh/{anh.pk}/')
    assert r.status_code == 400 and r.json()['error'] == 'Không tìm thấy tệp ảnh. Liên hệ quản trị viên.'
    assert not getattr(r, 'streaming', False) and b'\x89PNG' not in r.content


def test_tat_co_thi_chung_tu_va_anh_that_deu_404(client, feedback, nguoi_dung, settings):
    """AC-26.5 — Tắt cờ chứng từ (như trên VPS) thì chi tiết, ảnh thật, tạo mới đều 404 với mọi vai; bật lại thì ảnh
    xem lại được, không mất dữ liệu (ADR-025, P0-10)"""
    from orders.models import PaymentDocument
    client.force_login(nguoi_dung['admin'])
    pk = create_document(client, feedback[2][0]).json()['id']
    anh = client.get(f'/chung-tu-thanh-toan/{pk}/').json()['images'][0]['url']
    settings.PAYMENT_DOCUMENTS_ENABLED = False
    for ai in ('admin', 'staff_vd'):
        client.force_login(nguoi_dung[ai])
        assert client.get(f'/chung-tu-thanh-toan/{pk}/').status_code == 404
        assert client.get(anh).status_code == 404
    assert create_document(client, feedback[2][0], reference='TAT').status_code == 404
    assert PaymentDocument.objects.count() == 1
    settings.PAYMENT_DOCUMENTS_ENABLED = True
    client.force_login(nguoi_dung['admin'])
    r = client.get(anh)
    assert r.status_code == 200
    b''.join(r.streaming_content)
