from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies=[('crm','0002_grid_cell_history'),('orders','0006_line_unit_snapshot'),('org','0003_userprofile_birthday'),('forms_builder','0010_master_cover_index')]
    operations=[
        migrations.CreateModel(name='GridRevision',fields=[('table',models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,primary_key=True,serialize=False,to='forms_builder.tabledef')),('revision',models.BigIntegerField(default=0)),('fields',models.JSONField(default=dict))]),
        migrations.CreateModel(name='GridChange',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('revision',models.BigIntegerField()),('record_ids',models.JSONField(default=list)),('columns',models.JSONField(default=list)),('reset',models.BooleanField(default=False)),('table',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,to='forms_builder.tabledef'))],options={'constraints':[models.UniqueConstraint(fields=('table','revision'),name='crm_change_table_revision')]}),
        migrations.CreateModel(name='GridPendingChange',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('transaction_id',models.BigIntegerField(db_index=True)),('table_id',models.BigIntegerField()),('record_ids',models.JSONField(default=list)),('columns',models.JSONField(default=list)),('reset',models.BooleanField(default=False))]),
    ]
