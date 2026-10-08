"""AC-21.18, AC-21.19 — Chỉ Admin xoá dòng trên lưới (ADR-049, chủ dự án 08.10.2026).

Lưới chưa từng có nút xoá dòng bất kỳ: hai đường cũ `xoa-dong/`, `khoi-phuc-dong/` đã tắt (409) từ khi đổi lưới
(ADR-021). Chủ dự án chốt: thêm nút Xoá dòng **chỉ cho Admin** — xoá mềm, khôi phục được (Ctrl+Z), dòng vận đơn kéo
theo đơn gốc (AC-6.12). Mọi vai khác bị từ chối 403 có nhật ký. (Bảng vận đơn vốn không cho tạo dòng trên lưới,
nên đường Ctrl+Z gỡ dòng vừa gõ không có ở đây và không đổi.)

Đường ghi là `luu-json/` như mọi lần ghi khác của lưới: biên nhận chống gửi lặp, khoá dòng, so phiên bản (CAS).
"""
import uuid

import pytest

from core.constants import AuditAction
from core.models import AuditLog
from crm.models import GridCellHistory
from forms_builder.models import DataRecord
from forms_builder.services import record_service
from orders.models import Order
from core.constants import Rank

from .test_waybill_feedback import assign_rows, cskh_staff, delivery_leader, feedback  # noqa: F401

pytestmark = pytest.mark.django_db
BASE = '/bang-tinh/van_don/'
MAU = {'ngay': '2026-10-08', 'ten_khach': 'Khách', 'so_dien_thoai': '0900', 'quoc_gia': 'Hoa Kỳ', 'loai_tien': 'USD'}


def _goi(client, rows, *, kind='delete_rows', action='delete', operation=None, versions=None):
    versions = versions or {}
    return client.post(BASE + 'luu-json/', {
        'operation': operation or str(uuid.uuid4()), 'kind': kind, 'cells': [],
        'row_changes': [{'id': r.pk, 'action': action,
                         'version': versions.get(r.pk, r.updated_at.isoformat())} for r in rows]},
        content_type='application/json')


def _tong(client):
    return client.get(BASE + 'du-lieu/').json()['total']


def test_admin_xoa_dong_va_hoan_tac(client, feedback, nguoi_dung):  # noqa: F811
    """AC-21.18 — Admin xoá dòng trên lưới: dòng xoá mềm (ghi người xoá), đơn gốc bị bỏ có nhật ký, lịch sử dòng ghi
    lại, tổng số dòng giảm; khôi phục (Ctrl+Z) bằng phiên bản vừa trả về thì dòng và đơn sống lại"""
    _, _, rows = feedback
    admin = nguoi_dung['admin']
    client.force_login(admin)
    assert _tong(client) == 2
    don = Order.objects.get(record=rows[0])

    r = _goi(client, [rows[0]])
    assert r.status_code == 200, r.content
    ket_qua = r.json()['row_results']
    assert [(k['id'], k['deleted']) for k in ket_qua] == [(rows[0].pk, True)]
    dong = DataRecord.all_objects.get(pk=rows[0].pk)
    assert dong.deleted_at is not None and dong.deleted_by_id == admin.pk
    assert not Order.objects.filter(pk=don.pk).exists()
    assert AuditLog.objects.filter(action=AuditAction.DELETE, detail__contains=don.code).exists()
    assert GridCellHistory.objects.filter(record=dong, column='__row__', after=True).exists()
    assert DataRecord.objects.filter(pk=rows[1].pk).exists()
    assert _tong(client) == 1

    r = _goi(client, [dong], kind='restore_rows', action='restore', versions={dong.pk: ket_qua[0]['version']})
    assert r.status_code == 200, r.content
    assert r.json()['row_results'][0]['deleted'] is False
    assert DataRecord.objects.filter(pk=dong.pk).exists() and Order.objects.filter(pk=don.pk).exists()
    assert _tong(client) == 2


@pytest.fixture
def cac_vai(nguoi_dung, make_user, departments, delivery_leader, cskh_staff, feedback):  # noqa: F811
    """Mọi vai không phải Admin; vai nào cũng mở được lưới vận đơn và thấy ít nhất một dòng."""
    from orders.services import order_service
    _, products, rows = feedback
    assign_rows(delivery_leader, [rows[0]], care=cskh_staff.pk)
    # Quản lý Sale chỉ mở được bảng vận đơn khi có đơn của mình trên đó (phạm vi bảng, AC-10.23)
    for i, ten in enumerate(('leader_sale_1', 'manager_sale')):
        order_service.create_order(phone=f'09888800{i}', customer_name='Khách quản lý', actor=nguoi_dung[ten],
                                   lines=[{'product': products[0].code, 'quantity': 1, 'unit_price': '10.00'}])
    return {
        'staff_vd': nguoi_dung['staff_vd'],
        'leader_vd': delivery_leader,
        'manager_vd': make_user('manager_vd', Rank.MANAGER, departments['vd']),
        'nguoi_len_don': nguoi_dung['staff_sale_1'],
        'leader_sale': nguoi_dung['leader_sale_1'],
        'manager_sale': nguoi_dung['manager_sale'],
        'cskh_phu_trach': cskh_staff,
        'ke_toan': nguoi_dung['staff_kt'],
        'ceo': make_user('giam_doc', Rank.CEO),
        'admin': nguoi_dung['admin'],
    }


@pytest.mark.parametrize('vai', ['staff_vd', 'leader_vd', 'manager_vd', 'nguoi_len_don', 'leader_sale',
                                 'manager_sale', 'cskh_phu_trach', 'ke_toan', 'ceo'])
def test_vai_khac_bi_tu_choi_co_nhat_ky(client, feedback, cac_vai, vai):  # noqa: F811
    """AC-21.19 — Mọi vai không phải Admin (kể cả Manager, Leader Vận đơn và người lên đơn) xoá hay khôi phục dòng đều
    bị từ chối 403, có nhật ký từ chối; dòng và đơn gốc giữ nguyên; khối dữ liệu báo `capabilities.delete` = false"""
    rows = feedback[2]
    nguoi = cac_vai[vai]
    client.force_login(nguoi)
    khoi = client.get(BASE + 'du-lieu/').json()
    assert khoi['rows'], 'tiền đề: vai mở được lưới và thấy dòng'
    assert khoi['capabilities']['delete'] is False
    dich = DataRecord.objects.get(pk=khoi['rows'][0]['id'])     # một dòng chính vai này đang thấy
    truoc = AuditLog.objects.filter(action=AuditAction.DENIED, actor=nguoi).count()
    r = _goi(client, [dich])
    assert r.status_code == 403, r.content
    assert AuditLog.objects.filter(action=AuditAction.DENIED, actor=nguoi).count() == truoc + 1
    assert DataRecord.objects.filter(pk=dich.pk).exists()
    assert Order.objects.filter(record=dich).exists()
    # Khôi phục cũng chỉ Admin
    record_service.delete_record(DataRecord.objects.get(pk=rows[1].pk), actor=cac_vai['admin'])
    da_xoa = DataRecord.all_objects.get(pk=rows[1].pk)
    assert _goi(client, [da_xoa], kind='restore_rows', action='restore').status_code == 403
    assert DataRecord.all_objects.get(pk=rows[1].pk).deleted_at is not None


def test_capabilities_delete_chi_admin(client, feedback, nguoi_dung):  # noqa: F811
    """AC-21.19 — Khối dữ liệu báo `capabilities.delete` = true cho Admin (lưới hiện mục Xoá dòng)"""
    client.force_login(nguoi_dung['admin'])
    assert client.get(BASE + 'du-lieu/').json()['capabilities']['delete'] is True


def test_cas_toan_luot_va_gui_lai_khong_xoa_hai_lan(client, feedback, nguoi_dung):  # noqa: F811
    """AC-21.18 — Một dòng đã đổi (phiên bản cũ) thì cả lượt 409, không dòng nào bị xoá; gửi lại đúng mã thao tác đã
    thành công thì trả lại kết quả cũ, không xoá và không ghi nhật ký lần hai"""
    _, _, rows = feedback
    client.force_login(nguoi_dung['admin'])
    r = _goi(client, rows, versions={rows[1].pk: '2000-01-01T00:00:00+00:00'})
    assert r.status_code == 409, r.content
    assert DataRecord.objects.filter(pk__in=[r_.pk for r_ in rows]).count() == 2

    ma = str(uuid.uuid4())
    assert _goi(client, [rows[0]], operation=ma).status_code == 200
    so_nhat_ky = AuditLog.objects.filter(action=AuditAction.DELETE).count()
    lai = _goi(client, [rows[0]], operation=ma)
    assert lai.status_code == 200 and lai.json()['replayed'] is True
    assert AuditLog.objects.filter(action=AuditAction.DELETE).count() == so_nhat_ky


def test_khoi_phuc_khi_ma_don_da_co_dong_song_bi_chan(client, feedback, nguoi_dung):  # noqa: F811
    """AC-21.18 — Khôi phục dòng đã xoá khi mã đơn của nó đã có dòng sống khác: 400 bằng lời tiếng Việt nêu mã, dòng
    vẫn ở trạng thái đã xoá (AC-36.11)"""
    table, _, rows = feedback
    admin = nguoi_dung['admin']
    client.force_login(admin)
    ma_don = rows[0].data['ma_don']
    r = _goi(client, [rows[0]])
    version = r.json()['row_results'][0]['version']
    record_service.create_record(table, {**MAU, 'ma_don': ma_don}, actor=nguoi_dung['staff_vd'])
    dong = DataRecord.all_objects.get(pk=rows[0].pk)
    r = _goi(client, [dong], kind='restore_rows', action='restore', versions={dong.pk: version})
    assert r.status_code == 400 and ma_don in r.json()['error'], r.content
    assert DataRecord.all_objects.get(pk=rows[0].pk).deleted_at is not None


@pytest.mark.parametrize('loi', ['co_o', 'sai_hanh_dong'])
def test_goi_xoa_dong_sai_dang_bi_tu_choi(client, feedback, nguoi_dung, loi):  # noqa: F811
    """AC-21.18 — Lượt xoá dòng không được kèm sửa ô, và hành động phải khớp loại lượt (xoá đi với delete_rows,
    khôi phục đi với restore_rows): sai thì 400, không dòng nào đổi"""
    _, _, rows = feedback
    client.force_login(nguoi_dung['admin'])
    body = {'operation': str(uuid.uuid4()), 'kind': 'delete_rows', 'cells': [],
            'row_changes': [{'id': rows[0].pk, 'action': 'delete', 'version': rows[0].updated_at.isoformat()}]}
    if loi == 'co_o':
        body['cells'] = [{'id': rows[1].pk, 'column': 'ghi_chu', 'old': rows[1].data.get('ghi_chu'), 'value': 'x'}]
    else:
        body['row_changes'][0]['action'] = 'restore'
    r = client.post(BASE + 'luu-json/', body, content_type='application/json')
    assert r.status_code == 400, r.content
    assert DataRecord.objects.filter(pk=rows[0].pk).exists()

