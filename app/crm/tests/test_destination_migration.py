"""Migration metadata không sửa các dòng vận đơn hay liên kết đơn gốc."""
import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

@pytest.mark.django_db(transaction=True)
def test_destination_migration_roundtrip(departments):
    from forms_builder.models import TableDef, DataRecord
    assert connection.settings_dict['NAME'].startswith('test_')
    table=TableDef.objects.create(code='migration-destination',name='Migration',department=departments['vd'])
    row=DataRecord.objects.create(table=table,department=table.department,data={'ghi_chu':'giữ nguyên'})
    try:
        MigrationExecutor(connection).migrate([('forms_builder','0011_delivery_view_mode')])
        with connection.cursor() as cursor:
            columns={c.name for c in connection.introspection.get_table_description(cursor,'forms_builder_tabledef')}
        assert 'workflow' not in columns and 'receives_orders' not in columns
        assert DataRecord.objects.get(pk=row.pk).data == {'ghi_chu':'giữ nguyên'}
    finally:
        executor=MigrationExecutor(connection);executor.migrate(executor.loader.graph.leaf_nodes())
    table.refresh_from_db()
    assert table.workflow == '' and table.receives_orders is False
    assert DataRecord.objects.get(pk=row.pk).table_id == table.pk
