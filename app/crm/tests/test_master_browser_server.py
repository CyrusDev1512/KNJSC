"""AC-21.1, AC-21.2, AC-21.4, AC-21.5, AC-21.6 — Server Chrome dùng DB test riêng; mọi dữ liệu ghi đều là fixture."""
import json
import os
import time
from pathlib import Path
import pytest
from .test_waybill_feedback import feedback, delivery_leader
from forms_builder.models import DataRecord


@pytest.mark.trinh_duyet
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(os.environ.get('KN_MASTER_BROWSER') != '1', reason='Cần Chrome host / server test riêng')
def test_master_browser(live_server, feedback, delivery_leader, nguoi_dung, settings):
    from django.db import connection
    assert connection.settings_dict['NAME'].startswith('test_')
    settings.DEBUG = True
    settings.ALLOWED_HOSTS = ['*']
    profile=nguoi_dung['staff_mkt'].profile
    profile.full_name=('Nhân viên Marketing có tên dài ' * 5)[:150]
    profile.save(update_fields=['full_name'])
    table, _, source = feedback
    rows = []
    columns = list(table.columns.all())
    for i in range(1300):
        data = {**source[0].data, 'ma_don': f'MASTER-{i:05d}', 'ten_khach': f'Khách kiểm thử {i}',
                'ghi_chu': 'Nội dung dài để đọc mà không làm thay đổi chiều cao hàng. ' * 25}
        r = DataRecord(table=table, data=data, created_by=nguoi_dung['admin'])
        r.sync_indexed_columns(columns)
        rows.append(r)
    DataRecord.objects.bulk_create(rows)
    signal=Path('/app/.master-browser-ready.json'); result=Path('/app/.master-browser-result.json')
    result.unlink(missing_ok=True)
    try:
        signal.write_text(json.dumps({'rows':[r.pk for r in source], 'delivery':nguoi_dung['staff_vd'].pk}),encoding='utf-8')
        end=time.monotonic()+600
        while not result.exists() and time.monotonic()<end:
            time.sleep(.2)
        assert result.exists(), 'Chưa có kết quả Chrome'
        outcome=json.loads(result.read_text(encoding='utf-8'))
        assert outcome.get('ok'), outcome
    finally:
        signal.unlink(missing_ok=True);result.unlink(missing_ok=True)
