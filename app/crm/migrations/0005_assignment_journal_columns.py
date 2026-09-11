"""Sửa tên cột kỹ thuật, không sửa dữ liệu hoặc các phiên bản đã ghi."""
from django.db import migrations

OLD='["__membership","__access","phu_trach_van_don","phu_trach_cskh","marketing"]'
NEW='["__membership","__access","phu_trach_vd","phu_trach_cskh","phu_trach_mkt"]'


def replace(apps,schema_editor,old,new):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT pg_get_functiondef('crm_grid_capture()'::regprocedure)")
        definition=cursor.fetchone()[0]
        if old not in definition:raise RuntimeError('Không đúng phiên bản hàm nhật ký cần nâng cấp')
        cursor.execute(definition.replace(old,new))


def forward(apps,schema_editor):replace(apps,schema_editor,OLD,NEW)
def backward(apps,schema_editor):replace(apps,schema_editor,NEW,OLD)


class Migration(migrations.Migration):
    dependencies=[('crm','0004_grid_change_triggers')]
    operations=[migrations.RunPython(forward,backward)]
