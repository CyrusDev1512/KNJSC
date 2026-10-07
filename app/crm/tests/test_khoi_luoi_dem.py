"""AC-10.26 — Khối lưới `du-lieu/` đệm mốc phiên bản và tổng số dòng (07.10.2026).

Ở 385.000 dòng mỗi khối 100 dòng quét phạm vi hai lần (COUNT + MAX cho mốc, COUNT cho tổng): 222–929 ms. Nay hai
giá trị đó đọc qua `caches['crm']`, khoá gồm phạm vi người xem, `GridRevision` của bảng (trigger tăng khi commit mọi
thay đổi dòng, đơn, phân công, quyền, hồ sơ, xoá cứng) và `MAX(updated_at)` cả bảng. Bài kiểm chốt: lặp khối không
quét lại; 409 vẫn như cũ; đổi phân công hay xoá cứng không trả số cũ; Redis hỏng vẫn đúng.
"""
import uuid

import pytest
from django.core.cache import caches

from forms_builder.models import DataRecord
from forms_builder.services import record_service

from .test_waybill_feedback import assign_rows, delivery_leader, feedback  # noqa: F401

BASE = '/bang-tinh/van_don/'
MAU = {'ngay': '2026-10-07', 'ten_khach': 'Khách', 'so_dien_thoai': '0900', 'quoc_gia': 'Hoa Kỳ', 'loai_tien': 'USD'}


@pytest.fixture
def dem(settings):
    settings.CACHES = {**settings.CACHES, 'crm': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                                                  'LOCATION': 'thu-khoi-luoi'}}
    caches['crm'].clear()
    yield caches['crm']
    caches['crm'].clear()


def _khoi(client, **tham_so):
    r = client.get(BASE + 'du-lieu/', tham_so)
    return r.status_code, r.json()


def _ghi(client, dong, gia_tri):
    dong.refresh_from_db()
    return client.post(BASE + 'luu-json/', {'operation': str(uuid.uuid4()), 'cells': [
        {'id': dong.pk, 'column': 'ghi_chu', 'old': dong.data.get('ghi_chu'), 'value': gia_tri}]},
        content_type='application/json')


@pytest.mark.django_db
def test_khoi_lap_khong_quet_lai_pham_vi(client, feedback, nguoi_dung, dem, monkeypatch):  # noqa: F811
    """AC-10.26 — Đọc lại khối khi bảng không đổi: không chạy lại phép quét phạm vi (mốc và tổng), bớt đúng hai
    truy vấn; tổng và phiên bản y nguyên"""
    from django.db import connection
    from django.test.utils import CaptureQueriesContext
    from crm.services import master_grid_service as service

    goc, goi = service.stamp, []
    monkeypatch.setattr(service, 'stamp', lambda u, t: goi.append(1) or goc(u, t))
    client.force_login(nguoi_dung['staff_vd'])
    _khoi(client)                                         # lượt đầu còn nạp phiên đăng nhập
    dem.clear()
    goi.clear()
    with CaptureQueriesContext(connection) as lan_dau:
        _, a = _khoi(client)
    with CaptureQueriesContext(connection) as lan_hai:
        _, b = _khoi(client)
    assert len(goi) == 1
    assert len(lan_dau) - len(lan_hai) == 2
    assert (a['total'], a['version']) == (b['total'], b['version']) == (2, a['version'])
    # Bộ lọc khác là mục đệm khác: tổng đúng theo lọc
    _, c = _khoi(client, sp=feedback[1][0].code)
    assert c['total'] == 1


@pytest.mark.django_db
def test_sua_trong_pham_vi_van_409_ngoai_pham_vi_khong(client, feedback, nguoi_dung, dem):  # noqa: F811
    """AC-10.26 — Bộ đệm đã ấm: dòng trong phạm vi bị sửa thì khối với phiên bản cũ vẫn 409 (AC-21.2); dòng ngoài
    phạm vi người xem bị sửa thì không 409"""
    _, rows = feedback[0], feedback[2]
    client.force_login(nguoi_dung['staff_sale_2'])        # chỉ thấy dòng của đơn mình (rows[1])
    _, cu = _khoi(client)
    assert cu['total'] == 1
    client.force_login(nguoi_dung['admin'])
    assert _ghi(client, rows[0], 'Ngoài phạm vi Sale 2').status_code == 200
    client.force_login(nguoi_dung['staff_sale_2'])
    assert _khoi(client, version=cu['version'])[0] == 200
    client.force_login(nguoi_dung['admin'])
    assert _ghi(client, rows[1], 'Trong phạm vi Sale 2').status_code == 200
    client.force_login(nguoi_dung['staff_sale_2'])
    assert _khoi(client, version=cu['version'])[0] == 409


@pytest.mark.django_db(transaction=True)
def test_doi_phan_cong_va_xoa_cung_khong_tra_so_cu(client, feedback, nguoi_dung, delivery_leader, dem):  # noqa: F811
    """AC-10.26 — Thay đổi đã commit không làm đổi `updated_at` lớn nhất (giao CSKH cho Sale, xoá mềm theo lô, xoá cứng một dòng cũ)
    vẫn làm khối tính lại: tổng và phiên bản đổi đúng, không đọc số cũ từ bộ đệm"""
    _, _, rows = feedback
    sale2, vd = nguoi_dung['staff_sale_2'], nguoi_dung['staff_vd']
    client.force_login(sale2)
    assert _khoi(client)[1]['total'] == 1
    moc = dict(DataRecord.all_objects.filter(table=feedback[0]).values_list('pk', 'updated_at'))
    assign_rows(delivery_leader, [rows[0]], care=sale2.pk)
    for pk, luc in moc.items():                           # chỉ đổi updated_at: trigger không tăng revision
        DataRecord.all_objects.filter(pk=pk).update(updated_at=luc)
    assert _khoi(client)[1]['total'] == 2

    c1, c2 = (record_service.create_record(feedback[0], {**MAU, 'ma_don': f'DH-CU{i}'}, actor=vd) for i in (1, 2))
    record_service.create_record(feedback[0], {**MAU, 'ma_don': 'DH-MOI'}, actor=vd)
    client.force_login(vd)
    _, a = _khoi(client)
    assert a['total'] == 5
    DataRecord.all_objects.filter(pk=c1.pk).delete()      # xoá mềm theo lô: không chạm updated_at
    _, b = _khoi(client)
    assert b['total'] == 4                               # mốc phạm vi (stamp) không đổi như trước; tổng không cũ
    DataRecord.all_objects.filter(pk=c2.pk).hard_delete()
    _, c = _khoi(client)
    assert c['total'] == 3 and c['version'] != b['version']


@pytest.mark.django_db
def test_redis_hong_van_dung(client, feedback, nguoi_dung, dem, monkeypatch):  # noqa: F811
    """AC-10.26 — Bộ đệm lỗi (Redis mất) thì khối tính thẳng từ cơ sở dữ liệu: tổng đúng, sửa trong phạm vi vẫn 409"""
    def hong(*a, **k):
        raise ConnectionError('redis mất')
    monkeypatch.setattr(dem, 'get', hong)
    monkeypatch.setattr(dem, 'set', hong)
    client.force_login(nguoi_dung['staff_vd'])
    _, cu = _khoi(client)
    assert cu['total'] == 2
    assert _ghi(client, feedback[2][0], 'Khi Redis mất').status_code == 200
    assert _khoi(client, version=cu['version'])[0] == 409
    assert _khoi(client)[1]['total'] == 2


@pytest.mark.django_db
def test_panel_bo_loc_dem_khong_tra_so_cu(client, feedback, nguoi_dung, dem):  # noqa: F811
    """AC-10.26 — Số đếm của panel Bộ lọc (giá trị cột, sản phẩm) đọc qua cùng bộ đệm: lặp lại không đếm lại; sửa ô
    trên lưới thì lần mở sau ra số mới"""
    from django.http import QueryDict
    from crm.services import grid_service, sidebar_service

    table, _, rows = feedback
    vd = nguoi_dung['staff_vd']
    cot = table.columns.get(code='ghi_chu')
    sp = lambda: sorted((i[0], i[2]) for i in sidebar_service.product_options(vd, table, [], QueryDict())['items'])  # noqa: E731
    truoc, sp_truoc = grid_service.filter_options(vd, table, cot), sp()
    assert len(dem._cache) >= 2
    assert grid_service.filter_options(vd, table, cot) == truoc and sp() == sp_truoc
    client.force_login(vd)
    assert _ghi(client, rows[0], 'Giá trị panel mới').status_code == 200
    assert ('Giá trị panel mới', 1) in grid_service.filter_options(vd, table, cot)
    assert sp() == sp_truoc
