from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from openpyxl import Workbook

from forms_builder.models import TableDef, DataRecord
from forms_builder.services import import_service

pytestmark = pytest.mark.django_db


def upload(rows):
    book = Workbook()
    book.active.append(['Ngày', 'Tên khách', 'Số điện thoại', 'Mã đơn', 'Quốc gia', 'Loại tiền', 'Đối soát kế toán'])
    for row in rows:
        book.active.append(row)
    buffer = BytesIO()
    book.save(buffer)
    return SimpleUploadedFile('kiem-tra.xlsx', buffer.getvalue())


def row(code, phone='001234', choice=None, country='Canada'):
    return ['2026-09-15', 'Khách thử', phone, code, country, 'CAD', choice]


def test_preview_detects_bad_values_and_duplicate_orders(nguoi_dung):
    call_command('tao_bang_van_don')
    table = TableDef.objects.get(code='van_don')
    DataRecord.objects.create(table=table, department=table.department, data={'ma_don': 'OLD'})
    job = import_service.prepare(table, upload([row('NEW'), row('SAI-QG', country='Sao Hoả'), row('BAD', choice='Không có trong sổ'), row('OLD'), row(' NEW ')]), actor=nguoi_dung['admin'])
    assert job.summary['preview_error_count'] == 4
    assert job.summary['preview_valid_count'] == 1
    assert [n for n, _ in job.summary['preview_errors']] == [3, 4, 5, 6]
    assert table.records.count() == 1
    import_service.confirm(job, actor=nguoi_dung['admin'])
    job.refresh_from_db()
    assert job.summary['created'] == 1
    assert job.summary['error_count'] == 4
    assert table.records.count() == 2


def test_worker_rechecks_duplicates_after_preview(nguoi_dung):
    call_command('tao_bang_van_don')
    table = TableDef.objects.get(code='van_don')
    actor = nguoi_dung['admin']
    first = import_service.prepare(table, upload([row('SAME')]), actor=actor)
    second = import_service.prepare(table, upload([row('SAME')]), actor=actor)
    assert first.summary['preview_error_count'] == second.summary['preview_error_count'] == 0
    import_service.confirm(first, actor=actor)
    import_service.confirm(second, actor=actor)
    second.refresh_from_db()
    assert second.summary['created'] == 0
    assert second.summary['error_count'] == 1
    assert table.records.count() == 1


def test_old_preview_is_aligned_without_changing_data():
    summary = {'mapping': [{'cot_tep': 'Ngày', 'code': 'ngay'}, {'cot_tep': 'Bill', 'code': 'bill'}],
               'sample': [['BILL-01', '2026-09-15']]}
    assert import_service.preview_sample(summary) == [['2026-09-15', 'BILL-01']]
    assert summary['sample'] == [['BILL-01', '2026-09-15']]


@pytest.mark.django_db(transaction=True)
def test_two_import_workers_do_not_create_duplicate_codes(nguoi_dung, settings, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import close_old_connections
    call_command('tao_bang_van_don')
    table = TableDef.objects.get(code='van_don')
    actor = nguoi_dung['admin']
    monkeypatch.setattr(import_service, '_day_vao_hang_doi', lambda *args: None)
    jobs = [import_service.prepare(table, upload([row('CONCURRENT')]), actor=actor) for _ in range(2)]
    for job in jobs:
        import_service.confirm(job, actor=actor)
    barrier = Barrier(2)
    def work(pk):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            import_service.run(pk)
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(work, [job.pk for job in jobs]))
    for job in jobs:
        job.refresh_from_db()
    assert sorted(job.summary['created'] for job in jobs) == [0, 1]
    assert table.records.count() == 1
