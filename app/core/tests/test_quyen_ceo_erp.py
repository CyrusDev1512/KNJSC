"""Nghiệm thu CEO thật sau tích hợp task FIX EROR: chỉ xem báo cáo và bảng ERP."""
import pytest

from core.constants import Rank
from core.navigation import visible_navigation
from core.scope import get_user_scope
from forms_builder.models import ColumnDef, DataRecord, TableDef

pytestmark = pytest.mark.django_db


def test_ceo_doc_bang_nhieu_bo_phan_khong_co_quyen_quan_tri(client, make_user, departments, nguoi_dung):
    """AC-44.6 — CEO xem toàn công ty nhưng không được nâng thành Admin."""
    ceo = make_user('ceo_kiem_thu', Rank.CEO)
    scope = get_user_scope(ceo)
    assert scope.all_departments and not scope.is_admin
    nav = visible_navigation(ceo)
    assert not any(group['label'] == 'Quản trị' for group in nav)
    assert 'bang' in {item['code'] for group in nav for item in group['items']}
    client.force_login(ceo)
    for endpoint in ('/nhat-ky/', '/ma-tran-quyen/', '/tac-vu/'):
        assert client.get(endpoint).status_code == 403
    for department, owner in (('sale', 'staff_sale_1'), ('mkt', 'staff_mkt')):
        table = TableDef.objects.create(code=f'ceo_{department}', name=f'Bảng {department}',
                                        department=departments[department], created_by=nguoi_dung[owner])
        ColumnDef.objects.create(table=table, code='noi_dung', name='Nội dung', field_type='text')
        row = DataRecord.objects.create(table=table, department=table.department,
                                       created_by=nguoi_dung[owner], data={'noi_dung': f'Dữ liệu {department}'})
        response = client.get(f'/bang/{table.code}/')
        assert response.status_code == 200
        assert f'Dữ liệu {department}' in response.content.decode()
        assert client.post(f'/bang/{table.code}/o/{row.pk}/noi_dung/', {'gia_tri': 'Sửa trái phép'}).status_code == 404
        row.refresh_from_db()
        assert row.data['noi_dung'] == f'Dữ liệu {department}'


def test_ceo_khong_co_luong_nop_bao_cao(client, make_user):
    """AC-44.6 — CEO không có menu/CTA nộp; GET và POST trực tiếp đều bị chặn."""
    ceo = make_user('ceo_chi_xem', Rank.CEO)
    nav = visible_navigation(ceo)
    assert 'bao_cao_ngay' not in {item['code'] for group in nav for item in group['items']}
    client.force_login(ceo)
    assert client.get('/bao-cao/').status_code == 403
    assert client.post('/bao-cao/', {}).status_code == 403
    response = client.get('/bao-cao/lich-su/')
    assert response.status_code == 200
    assert 'href="/bao-cao/"' not in response.content.decode()
