"""Xuất template thật trên DB test cho phép đo browser tái lập, không dùng dữ liệu khách."""
import json
import os
from pathlib import Path
import pytest
from .test_waybill_feedback import feedback


@pytest.mark.django_db
@pytest.mark.skipif(os.environ.get('GRID_SCROLL_FIXTURE') != '1', reason='Chỉ xuất fixture đo cuộn riêng')
def test_export_scroll_fixture(client, settings, feedback, nguoi_dung):
    from django.db import connection
    assert connection.settings_dict['NAME'].startswith('test_')
    settings.ROOT_URLCONF = 'knjsc.urls_bangtinh'
    settings.CRM_OPT_RENDER = False
    client.force_login(nguoi_dung['admin'])
    url = f'/bang-tinh/{feedback[0].code}/'
    response = client.get(url)
    assert response.status_code == 200
    data = client.get(url+'du-lieu/').json()
    assert data['rows'] and data['columns']
    folder = Path('/storage/grid-scroll')
    folder.mkdir(exist_ok=True)
    (folder/'fixture.html').write_bytes(response.content)
    (folder/'fixture.json').write_text(json.dumps(data))
