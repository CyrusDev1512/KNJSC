"""Hồi quy màn hình Biểu mẫu & tài liệu và người tạo trống."""
import pytest
from django.urls import reverse
from forms_builder.models import FormDef, TableDef

pytestmark = pytest.mark.django_db


def test_form_without_creator(client, departments, nguoi_dung):
    table = TableDef.objects.create(name='Bảng thử', code='hub_table', department=departments['sale'])
    FormDef.objects.create(name='Biểu mẫu không người tạo', code='hub_form',
                           table=table, department=departments['sale'])
    client.force_login(nguoi_dung['admin'])
    response = client.get('/bieu-mau/')
    assert response.status_code == 200
    assert 'Biểu mẫu không người tạo' in response.content.decode()


@pytest.mark.parametrize('role,manage', [('staff_sale_1',False), ('leader_sale_1',False),
                                      ('manager_sale',True), ('admin',True)])
def test_hub_tabs_preserve_permissions(client, nguoi_dung, role, manage):
    client.force_login(nguoi_dung[role])
    response = client.get('/bieu-mau/')
    assert response.status_code == 200
    assert response.context['active_tab'] == ('forms' if manage else 'documents')
    assert client.get('/bieu-mau/?tab=forms').status_code == (200 if manage else 403)
    assert client.get('/bieu-mau/?tab=documents').status_code == 200


def test_documents_bookmark_preserves_filters(client, nguoi_dung):
    client.force_login(nguoi_dung['staff_sale_1'])
    response = client.get('/tai-lieu/', {'tim':'Sale & MKT', 'trang':2, 'muc':5})
    assert response.status_code == 302
    from urllib.parse import urlparse, parse_qs
    query = parse_qs(urlparse(response.url).query)
    assert query == {'tab':['documents'], 'tim':['Sale & MKT'], 'trang':['2'], 'muc':['5']}


def test_only_active_tab_queries_documents(client, nguoi_dung, monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError('Không tải tài liệu khi đang xem biểu mẫu')
    monkeypatch.setattr('documents.presentation.document_list_context', unexpected)
    client.force_login(nguoi_dung['admin'])
    assert client.get('/bieu-mau/?tab=forms').status_code == 200


def test_navigation_groups_and_crm_button(client, nguoi_dung):
    from core.navigation import visible_navigation
    groups = visible_navigation(nguoi_dung['admin'])
    assert [(g['label'], [m['label'] for m in g['items']]) for g in groups] == [
        ('Tổng quan', ['Tổng quan','Bảng tin']),
        ('Nội bộ', ['Quản lý task','Tài nguyên']),
        ('Tổ chức', ['Nhân sự','Bộ phận và team','Đánh giá nhân sự']),
        ('Báo cáo', ['Nộp báo cáo ngày','Lịch sử báo cáo','Báo cáo tổng hợp']),
        ('Dữ liệu', ['Bảng dữ liệu','Biểu mẫu & tài liệu']),
        ('Quản trị', ['Nhật ký hoạt động','Ma trận phân quyền','Tác vụ nền']),
    ]
    client.force_login(nguoi_dung['staff_sale_1'])
    html = client.get('/bieu-mau/').content.decode()
    assert 'Mở KN CRM trong tab mới' in html
    assert 'Tác vụ nền' in html


@pytest.mark.parametrize('role', ['manager_sale', 'admin'])
def test_form_list_stays_under_query_budget(client, nguoi_dung, departments, role, django_assert_max_num_queries):
    table = TableDef.objects.create(name='Bảng ngân sách truy vấn', code='hub_budget', department=departments['sale'])
    FormDef.objects.bulk_create([FormDef(name=f'Biểu mẫu {i}', code=f'budget_{i}', table=table,
        department=departments['sale'], created_by=nguoi_dung['manager_sale']) for i in range(30)])
    client.force_login(nguoi_dung[role])
    client.get('/bieu-mau/?tab=forms')
    with django_assert_max_num_queries(10):
        response = client.get('/bieu-mau/?tab=forms')
        assert response.status_code == 200
        assert len(response.context['page_obj']) == 25
