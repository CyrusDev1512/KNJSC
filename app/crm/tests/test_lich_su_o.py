"""Lịch sử từng ô trên lưới Vận đơn — AC-21.13 (chủ dự án 28.09.2026).

Chuột phải một ô thì xem ai sửa, lúc nào, từ gì thành gì (API `lich-su/` lọc theo dòng + cột,
đã kiểm quyền dòng). Ô bị **người khác** sửa trong 24 giờ mang dấu góc: khối dữ liệu `du-lieu/`
trả thêm `recent` cho mỗi dòng — danh sách mã cột, một truy vấn cho cả khối.
"""
from datetime import timedelta
from unittest import mock

import pytest
from django.utils import timezone

from core.constants import Rank
from crm.tests.test_waybill_feedback import feedback  # noqa: F401  (fixture dùng lại)

from .test_master_grid import BASE, write

pytestmark = pytest.mark.django_db


def test_o_vua_bi_nguoi_khac_sua_co_dau_va_lich_su_theo_o(client, feedback, nguoi_dung, make_user, departments):  # noqa: F811
    """AC-21.13 — Ô bị người khác sửa trong 24 giờ mang dấu (`recent`); chính mình sửa hay sửa đã
    quá 24 giờ thì không; lịch sử theo ô chỉ trả đúng cột đó, kèm mã người sửa, trước → sau"""
    _, _, dong = feedback
    minh = nguoi_dung['staff_vd']
    khac = make_user('vd_khac', Rank.STAFF, departments['vd'])

    client.force_login(minh)
    assert write(client, dong[0], value='Giao chiều').status_code == 200
    assert write(client, dong[0], column='ten_khach', old=dong[0].data['ten_khach'], value='Khách Mới').status_code == 200
    cu = timezone.now() - timedelta(hours=25)
    with mock.patch('django.utils.timezone.now', return_value=cu):
        assert write(client, dong[1], value='Ghi chú hôm kia').status_code == 200

    def dau(user):
        client.force_login(user)
        rows = client.get(BASE + 'du-lieu/').json()['rows']
        return {r['id']: sorted(r.get('recent', [])) for r in rows}

    assert dau(khac) == {dong[0].pk: ['ghi_chu', 'ten_khach'], dong[1].pk: []}
    assert dau(minh) == {dong[0].pk: [], dong[1].pk: []}, "ô chính mình sửa không đánh dấu"

    client.force_login(khac)
    ls = client.get(BASE + 'lich-su/', {'record': dong[0].pk, 'column': 'ten_khach'}).json()['items']
    assert [(h['column'], h['after'], h['actor']) for h in ls] == [('ten_khach', 'Khách Mới', ls[0]['actor'])]
    assert ls[0]['actor'] and ls[0]['before'] == dong[0].data['ten_khach']


def test_lich_su_o_van_chan_nguoi_ngoai_pham_vi(client, feedback, nguoi_dung):  # noqa: F811
    """AC-21.13 — Chiều từ chối: người không xem được dòng thì không đọc được lịch sử ô (403) và
    khối dữ liệu của họ không lộ dòng đó"""
    _, _, dong = feedback
    client.force_login(nguoi_dung['staff_vd'])
    write(client, dong[1], value='Riêng tư')
    client.force_login(nguoi_dung['staff_sale_1'])          # chỉ thấy đơn mình lên (dong[0])
    assert client.get(BASE + 'lich-su/', {'record': dong[1].pk, 'column': 'ghi_chu'}).status_code == 403
    ids = {r['id'] for r in client.get(BASE + 'du-lieu/').json()['rows']}
    assert dong[1].pk not in ids
