from django.db import migrations


def add_accounting(apps, schema_editor):
    apps.get_model('org', 'Department').objects.get_or_create(
        code='ke-toan', defaults={'name': 'Kế toán', 'is_active': True})


class Migration(migrations.Migration):
    dependencies = [('org', '0003_userprofile_birthday')]
    # Không xoá phòng ban có thể đã được gán nhân sự khi quay lui code.
    operations = [migrations.RunPython(add_accounting, migrations.RunPython.noop)]
