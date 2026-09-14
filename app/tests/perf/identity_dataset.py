from datetime import date, timedelta
from django.conf import settings
from django.db import transaction
from django.contrib.auth import get_user_model
from forms_builder.models import DataRecord, FormDef
from reports.models import DailyReport
assert settings.DATABASES['default']['NAME']=='knjsc_erp_verify'
with transaction.atomic():
    for kind in ['mkt','sale']:
        form=FormDef.objects.get(code=f'bc_{kind}_ngay')
        for n in range(20):
            user=get_user_model().objects.select_related('profile').get(username=f'erp_{kind}_{n}')
            if DailyReport.objects.filter(form=form,created_by=user,report_date__lt=date(2010,1,1)).exists():
                continue
            original=DataRecord.objects.filter(table=form.table,created_by=user).first()
            rows=[]
            for i in range(1000):
                day=date(2000,1,1)+timedelta(days=i)
                data={**original.data,'ngay':str(day)}
                rows.append(DataRecord(table=form.table,created_by=user,department=form.department,
                    team=user.profile.team,data=data,val_date=day,val_product=original.val_product,
                    val_seller=user.username,val_revenue=original.val_revenue))
            DataRecord.objects.bulk_create(rows,batch_size=1000)
            DailyReport.objects.bulk_create([DailyReport(form=form,record=r,report_date=r.val_date,
                created_by=user,department=form.department,team=user.profile.team) for r in rows],batch_size=1000)
print('Reports:',DailyReport.objects.count())
