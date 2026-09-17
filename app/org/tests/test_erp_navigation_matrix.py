"""KNJSC 02.7–8: menu và endpoint tuân theo cùng quyền đã chốt."""
import pytest

pytestmark = pytest.mark.django_db

@pytest.mark.parametrize('role,organization,forms,create', [
    ('staff_sale_1',403,403,403), ('leader_sale_1',200,403,403),
    ('manager_sale',200,200,403), ('admin',200,200,200),
])
def test_menu_matches_server(client, nguoi_dung, role, organization, forms, create):
    user=nguoi_dung[role]
    client.force_login(user)
    for path, expected in [('/',200),('/bao-cao/',200),('/bao-cao/lich-su/',200),
        ('/bao-cao/tong-hop/',200),('/bang/',200),('/nhan-su/',organization),
        ('/bieu-mau/',200),('/bieu-mau/?tab=forms',forms),('/nhan-su/moi/',create)]:
        assert client.get(path).status_code == expected, (role,path)
    if create == 403:
        assert client.post('/nhan-su/moi/', {'username':'forbidden'}).status_code == 403
    html=client.get('/').content.decode()
    assert ('href="/nhan-su/"' in html) == (organization == 200)
    assert 'href="/bieu-mau/"' in html
