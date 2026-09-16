"""Đi theo URL do biểu mẫu ERP thực sự sinh ra khi thêm sản phẩm."""
import re

import pytest
from django.core.management import call_command

from forms_builder.models import FormDef
from orders.models import Product
from reports.tests.test_aggregations import bang_mkt

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('kind,role,staff', [
    ('mkt', 'manager_mkt', 'staff_mkt'),
    ('sale', 'manager_sale', 'staff_sale_1'),
])
def test_add_product_using_rendered_report_endpoint(client, bang_mkt, nguoi_dung, kind, role, staff):
    bang_mkt.code = 'bao_cao_mkt'
    bang_mkt.save(update_fields=['code'])
    bang_mkt.columns.filter(code='san_pham').update(field_type='choice')
    FormDef.objects.create(code='bc_mkt_ngay', name='Marketing', table=bang_mkt, department=bang_mkt.department)
    call_command('configure_erp_reports')
    client.force_login(nguoi_dung[role])
    page = client.get('/bao-cao/', {'bieu_mau':f'bc_{kind}_ngay'})
    assert page.status_code == 200
    url = re.search(r'hx-post="([^"]+/cot/san_pham/lua-chon/)"', page.content.decode()).group(1)
    response = client.post(url, {'nhan_moi':'Sản phẩm mẫu báo cáo'}, HTTP_HX_REQUEST='true')
    assert response.status_code == 200
    assert Product.objects.filter(name='Sản phẩm mẫu báo cáo').count() == 1
    assert 'Sản phẩm mẫu báo cáo' in response.content.decode()
    client.force_login(nguoi_dung[staff])
    assert client.post(url, {'nhan_moi':'Không được tạo'}).status_code == 403
    assert not Product.objects.filter(name='Không được tạo').exists()
