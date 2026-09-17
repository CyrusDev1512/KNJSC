"""Server kiểm UI với 10.000 dòng synthetic; không dùng database dev."""
import json
import os
import time
from pathlib import Path
import uuid
import ast
from unittest.mock import patch
import pytest
from .test_waybill_feedback import feedback
from .test_payment_documents import image_upload


@pytest.mark.trinh_duyet
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(os.environ.get('KN_PAYMENT_BROWSER') != '1', reason='Cần Chrome host và cổng test riêng')
def test_payment_browser(live_server, feedback, nguoi_dung, settings):
    from django.db import connection
    from forms_builder.models import DataRecord
    from orders.models import PaymentDocument, PaymentImage
    from orders.services import payment_service
    assert connection.settings_dict['NAME'].startswith('test_')
    settings.DEBUG = True
    settings.ALLOWED_HOSTS = ['*']
    table, _, originals = feedback
    columns = list(table.columns.all())
    rows = []
    for i in range(9998):
        row = DataRecord(table=table, data={**originals[0].data, 'ma_don': f'PAY-{i:05d}',
            'ten_khach': f'Khách kiểm thử {i}'}, created_by=nguoi_dung['admin'], department=table.department)
        row.sync_indexed_columns(columns)
        rows.append(row)
    DataRecord.objects.bulk_create(rows, batch_size=1000)
    document = payment_service.create(nguoi_dung['admin'], originals[0].pk, 'REF-000123', '', '',
                                      [image_upload()], uuid.uuid4())
    template = document.images.get()
    documents = PaymentDocument.objects.bulk_create([PaymentDocument(record_id=pk,
        reference=f'REF-{pk:08}', created_by=nguoi_dung['admin'], updated_by=nguoi_dung['admin'],
        operation=uuid.uuid4(), fingerprint='synthetic') for pk in [originals[1].pk, *[r.pk for r in rows]]], batch_size=1000)
    PaymentImage.objects.bulk_create([PaymentImage(document=d, file_path=template.file_path,
        file_name='synthetic.png', file_kind='png', file_size=template.file_size,
        created_by=nguoi_dung['admin']) for d in documents], batch_size=1000)
    metrics = {}
    baseline_path = Path('/app/.payment-baseline.py')
    if baseline_path.exists():
        # Chỉ so chi phí đọc khối trước/sau thêm metadata, cùng DB và code còn lại.
        from crm.services import master_grid_service as master
        from django.http import QueryDict
        source = ast.parse(baseline_path.read_text(encoding='utf-8-sig'))
        function = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == 'serialize')
        namespace = dict(master.__dict__)
        exec(compile(ast.Module(body=[function], type_ignores=[]), 'baseline-95988c9', 'exec'), namespace)
        for label, serializer in [('before_metadata', namespace['serialize']), ('after_metadata', master.serialize)]:
            samples = []
            with patch.object(master, 'serialize', serializer):
                for i in range(30):
                    start = time.perf_counter()
                    payload = master.block(nguoi_dung['admin'], table, QueryDict(f'offset={i * 300}'))
                    samples.append(round((time.perf_counter() - start) * 1000, 2))
                    assert len(payload['rows']) == 100 and payload['total'] == 10000
            metrics[label] = samples
    ready = Path('/app/.payment-ready.json')
    result = Path('/app/.payment-result.json')
    result.unlink(missing_ok=True)
    ready.write_text(json.dumps({'document': document.pk, 'row': originals[0].pk, 'metrics': metrics,'delivery':nguoi_dung['staff_vd'].pk}), encoding='utf-8')
    try:
        end = time.monotonic() + 900
        while not result.exists() and time.monotonic() < end:
            time.sleep(.2)
        assert result.exists(), 'Thiếu kết quả Chrome'
        report = json.loads(result.read_text(encoding='utf-8'))
        assert report.get('ok'), report
    finally:
        ready.unlink(missing_ok=True)
        result.unlink(missing_ok=True)
