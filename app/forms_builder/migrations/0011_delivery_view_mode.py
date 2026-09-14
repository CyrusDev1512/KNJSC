from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('forms_builder', '0010_master_cover_index')]
    operations = [
        migrations.AddField('tabledef', 'delivery_view_all', models.BooleanField(default=False, verbose_name='Vận đơn xem toàn bảng')),
        migrations.AddField('tabledef', 'delivery_view_version', models.PositiveIntegerField(default=0, editable=False)),
    ]
