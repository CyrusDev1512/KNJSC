"""TL-12: xoá/khôi phục nhiều dòng giữ CAS, biên nhận, đơn gốc và audit; SQL không tăng từng dòng."""
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from core.models import AuditLog
from core.constants import AuditAction
from crm.models import GridCellHistory
from forms_builder.models import DataRecord
from forms_builder.services import record_service
from crm.tests.test_chi_admin_xoa_dong import _goi, MAU
from crm.tests.test_waybill_feedback import feedback  # noqa: F401

pytestmark = pytest.mark.django_db


def test_xoa_khoi_phuc_30_dong_khong_nhan_sql_tung_dong(client, feedback, nguoi_dung):
    """AC-21.18 — 30 dòng qua endpoint thật: mỗi lượt < 60 SQL, đủ lịch sử/audit từng dòng."""
    table, _, base = feedback
    admin = nguoi_dung['admin']
    rows = base + [record_service.create_record(table, {**MAU, 'ma_don':f'TEST-BULK-{i}'}, actor=admin) for i in range(28)]
    client.force_login(admin)
    with CaptureQueriesContext(connection) as queries:
        response = _goi(client, rows)
    assert response.status_code == 200, response.content
    assert len(queries) < 60, len(queries)
    ids = [r.pk for r in rows]
    assert not DataRecord.objects.filter(pk__in=ids).exists()
    assert GridCellHistory.objects.filter(record_id__in=ids, column='__row__', after=True).count() == 30
    assert AuditLog.objects.filter(target_type='DataRecord', target_id__in=list(map(str,ids)), action=AuditAction.DELETE).count() == 30
    versions = {r['id']:r['version'] for r in response.json()['row_results']}
    with CaptureQueriesContext(connection) as queries:
        response = _goi(client, rows, kind='restore_rows', action='restore', versions=versions)
    assert response.status_code == 200, response.content
    assert len(queries) < 60, len(queries)
    assert DataRecord.objects.filter(pk__in=ids).count() == 30
