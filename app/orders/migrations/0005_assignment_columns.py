from django.db import migrations


COLUMNS = [('phu_trach_vd', 'Phụ trách Vận đơn'), ('phu_trach_cskh', 'Phụ trách CSKH'),
           ('phu_trach_mkt', 'Phụ trách Marketing')]


def forwards(apps, schema_editor):
    tables = apps.get_model('forms_builder', 'TableDef').objects.using(schema_editor.connection.alias)
    columns = apps.get_model('forms_builder', 'ColumnDef').objects.using(schema_editor.connection.alias)
    for table in tables.filter(code='van_don_moi'):
        for order, (code, name) in enumerate(COLUMNS, 22):
            columns.get_or_create(table_id=table.pk, code=code,
                defaults={'name': name, 'field_type': 'text', 'order': order, 'options': []})


def backwards(apps, schema_editor):
    apps.get_model('forms_builder', 'ColumnDef').objects.using(schema_editor.connection.alias).filter(
        table__code='van_don_moi', code__in=[code for code, _ in COLUMNS]).delete()


class Migration(migrations.Migration):
    dependencies = [('orders', '0004_waybill_assignment')]
    operations = [migrations.RunPython(forwards, backwards)]
