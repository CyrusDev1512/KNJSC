"""Kiểm xuôi/ngược metadata trên database do pytest quản lý."""
import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from forms_builder.models import TableDef, DataRecord
from reports.models import ReportSource


@pytest.mark.django_db(transaction=True)
def test_report_source_migration_preserves_business_rows(departments):
    assert connection.settings_dict["NAME"].startswith("test_")
    table = TableDef.objects.create(code="migration_erp", name="ERP", department=departments["sale"])
    row = DataRecord.objects.create(table=table, department=table.department, data={"so_don": 7})
    ReportSource.objects.create(table=table, kind="sale", columns={"orders": "so_don"})
    try:
        MigrationExecutor(connection).migrate([("reports", "0001_initial")])
        assert "reports_reportsource" not in connection.introspection.table_names()
        assert DataRecord.objects.get(pk=row.pk).data == {"so_don": 7}
    finally:
        MigrationExecutor(connection).migrate([("reports", "0002_erp_report_sources")])
    assert "reports_reportsource" in connection.introspection.table_names()
    assert DataRecord.objects.get(pk=row.pk).data == {"so_don": 7}
    assert not ReportSource.objects.exists()
