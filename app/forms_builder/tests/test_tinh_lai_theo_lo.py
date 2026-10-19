"""TL-25/26/118/123: tính lại dùng cấu trúc hiện hành, không N+1 hoặc chạy tiếp hàng đợi sau lỗi."""
from unittest.mock import patch
import threading
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from forms_builder.models import ColumnDef, DataRecord
from forms_builder.services import table_service
from crm.tests.test_bang_tinh_luu_o import bang_sale  # noqa: F401

pytestmark = pytest.mark.django_db(transaction=True)


def rows(table, user, count):
    table.workflow = ''
    table.save(update_fields=['workflow'])
    return DataRecord.objects.bulk_create([DataRecord(table=table, department=table.department,
        created_by=user, data={'doanh_thu':'100', 'so_luong':2, 'gia_dv':'0'}) for _ in range(count)])


def test_tinh_lai_khong_doc_lai_table_tung_dong(bang_sale, nguoi_dung):
    """AC-11.35 — 180 dòng trong một lô có số SQL cố định, vẫn tính đúng từng dòng."""
    rows(bang_sale, nguoi_dung['admin'], 180)
    with CaptureQueriesContext(connection) as q:
        assert table_service.resync_table(bang_sale, batch=200) == 180
    assert len(q) < 30, len(q)
    assert set(DataRecord.objects.filter(table=bang_sale).values_list('data__gia_dv', flat=True)) == {'50.00'}


def test_lo_sau_khong_ghi_cong_thuc_cu(bang_sale, nguoi_dung, monkeypatch):
    """AC-11.35 — Cấu hình đổi giữa hai lô: lô sau đọc công thức mới, lượt cũ không ghi đè nó."""
    created = rows(bang_sale, nguoi_dung['admin'], 2)
    monkeypatch.setattr(table_service, 'RECOMPUTE_THREADS', 1)
    def change(n):
        if n == 1:
            ColumnDef.objects.filter(table=bang_sale, code='gia_dv').update(compute_op='multiply')
    table_service.resync_table(bang_sale, batch=1, on_progress=change)
    created[1].refresh_from_db()
    assert created[1].data['gia_dv'] == '200.00'


def test_gom_tac_vu_dang_cho_khong_lam_mat_luot_moi_khi_dang_chay(bang_sale, nguoi_dung, monkeypatch):
    """AC-11.35 — Hai yêu cầu chờ chung một job; đang chạy vẫn cần lượt kế để phủ lô đã qua."""
    rows(bang_sale, nguoi_dung['admin'], 2)
    monkeypatch.setattr(table_service, 'RECOMPUTE_SYNC_MAX_ROWS', 0)
    with patch('forms_builder.services.import_service._day_vao_hang_doi') as enqueue:
        first = table_service.schedule_resync(bang_sale)
        second = table_service.schedule_resync(bang_sale)
        assert first.pk == second.pk
        assert enqueue.call_count == 1
        first.mark_running()
        third = table_service.schedule_resync(bang_sale)
        assert third.pk != first.pk


def test_bo_cot_chu_khong_tinh_lai(bang_sale, nguoi_dung):
    """AC-11.22 — Bỏ cột chữ không nhãn/không công thức giữ JSON và không quét lại bảng."""
    row = rows(bang_sale, nguoi_dung['admin'], 1)[0]
    col = ColumnDef.objects.create(table=bang_sale, code='note', name='Ghi chú', field_type='text')
    with patch.object(table_service, 'schedule_resync') as resync:
        table_service.remove_column(col, actor=nguoi_dung['admin'])
    resync.assert_not_called()
    row.refresh_from_db()
    assert row.data['gia_dv'] == '0'


def test_lo_hong_khong_nhan_tiep_phan_con_lai(bang_sale, nguoi_dung, monkeypatch):
    """AC-11.35 — Hai worker: khi một lô lỗi, không nhận 8 lô còn lại; chờ lô đang chạy rồi báo lỗi."""
    made = rows(bang_sale, nguoi_dung['admin'], 10)
    monkeypatch.setattr(table_service, 'RECOMPUTE_THREADS', 2)
    from forms_builder.services import record_service
    original = record_service.save_rows
    failed = threading.Event()
    seen = []
    def save(batch, **kwargs):
        seen.append(batch[0].pk)
        if batch[0].pk == made[1].pk:
            failed.set()
            raise ValueError('Lô thử bị lỗi')
        if batch[0].pk == made[0].pk:
            assert failed.wait(5)
        return original(batch, **kwargs)
    monkeypatch.setattr(record_service, 'save_rows', save)
    with pytest.raises(ValueError, match='Lô thử bị lỗi'):
        table_service.resync_table(bang_sale, batch=1)
    assert len(seen) <= 2, seen
