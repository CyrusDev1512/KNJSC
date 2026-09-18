"""Bộ lọc nhân sự phải áp dụng trước tổng hợp, xuất và thống kê trạng thái."""
from io import BytesIO

import pytest
from openpyxl import load_workbook

from reports.models import ReportSource
from reports.tests.test_aggregations import bang_mkt
from reports.tests.test_mkt_excel import marketing_scope
from reports.tests.test_activity import delivery_source

pytestmark = pytest.mark.django_db


@pytest.fixture
def source(marketing_scope):
    return ReportSource.objects.create(table=marketing_scope.table, kind='sale',
        columns={'mess':'so_mess', 'orders':'so_don', 'sales':'doanh_so', 'market':'thi_truong'})


@pytest.mark.parametrize('role', ['staff_sale_1', 'leader_sale_1', 'manager_sale', 'admin'])
def test_person_filter_matches_export_and_totals(client, source, nguoi_dung, role):
    client.force_login(nguoi_dung[role])
    person = nguoi_dung['staff_sale_1']
    query = {'nguon':source.table.code, 'nhan_su':str(person.pk),
             'tu':'2026-08-01', 'den':'2026-08-31', 'nhom':'person'}
    response = client.get('/bao-cao/tong-hop/', query)
    assert response.status_code == 200
    assert response.context['result'].totals['so_dong'] == 1
    assert response.context['rows'][0]['team'] == person.profile.team.name
    book = load_workbook(BytesIO(client.get('/bao-cao/tong-hop/xuat/', query).content), data_only=True)
    rows = list(book.active.values)
    assert rows[3][:3] == ('Team', 'Sale', 'Leader')
    assert rows[4][0] == person.profile.team.name
    assert rows[-1][3:6] == (10, 2, 100)


def test_team_filter_and_combination(client, source, nguoi_dung, teams):
    client.force_login(nguoi_dung['manager_sale'])
    query = {'nguon':source.table.code, 'team':str(teams['sale1'].pk),
             'tu':'2026-08-01', 'den':'2026-08-31'}
    assert client.get('/bao-cao/tong-hop/', query).context['result'].totals['so_dong'] == 3
    query['nhan_su'] = str(nguoi_dung['staff_sale_2'].pk)
    assert client.get('/bao-cao/tong-hop/', query).context['result'].totals['so_dong'] == 0


@pytest.mark.parametrize('path', ['/bao-cao/tong-hop/', '/bao-cao/tong-hop/xuat/'])
def test_filter_cannot_expose_other_team(client, source, nguoi_dung, teams, path):
    client.force_login(nguoi_dung['leader_sale_1'])
    query = {'nguon':source.table.code, 'tu':'2026-08-01', 'den':'2026-08-31'}
    response = client.get(path, {**query, 'nhan_su':nguoi_dung['staff_sale_2'].pk})
    assert response.status_code == 403
    assert client.get(path, {**query, 'team':teams['sale2'].pk}).status_code == 403
    assert client.get(path, {**query, 'nhan_su':'abc'}).status_code == 400
    response = client.get('/bao-cao/tong-hop/', query)
    ids = {p['id'] for p in response.context['people']}
    assert nguoi_dung['staff_sale_2'].pk not in ids


def test_delivery_filter_uses_assignee_not_creator(client, delivery_source, nguoi_dung):
    client.force_login(nguoi_dung['admin'])
    query = {'nguon':delivery_source.table.code, 'nhan_su':nguoi_dung['staff_sale_1'].pk,
             'tu':'2026-08-01', 'den':'2026-08-31'}
    r = client.get('/bao-cao/tong-hop/', query)
    assert r.status_code == 200
    assert r.context['result'].totals['c_orders'] == 2
    assert sum(item['count'] for item in r.context['shipping']) == 2
