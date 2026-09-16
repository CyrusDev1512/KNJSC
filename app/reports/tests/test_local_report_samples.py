import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

from forms_builder.models import FormDef
from orders.models import Product
from reports.models import DailyReport
from reports.tests.test_aggregations import bang_mkt

pytestmark = pytest.mark.django_db


def test_samples_are_submitted_idempotent_and_cannot_login(bang_mkt):
    bang_mkt.code = 'bao_cao_mkt'
    bang_mkt.save(update_fields=['code'])
    FormDef.objects.create(code='bc_mkt_ngay', name='Marketing', table=bang_mkt, department=bang_mkt.department)
    Product.objects.create(code='sample', name='Mẫu sản phẩm')
    call_command('configure_erp_reports')
    call_command('configure_delivery_daily_report')
    call_command('seed_local_report_history')
    call_command('seed_local_report_history')
    assert DailyReport.objects.count() == 36
    users = get_user_model().objects.filter(username__startswith='mau_erp_1609_')
    assert users.count() == 12
    assert all(not user.is_active and not user.has_usable_password() for user in users)
    assert DailyReport.objects.values('team').distinct().count() == 6


def test_samples_refuse_production(settings):
    settings.SETTINGS_MODULE = 'knjsc.settings.production'
    with pytest.raises(CommandError, match='dev/test'):
        call_command('seed_local_report_history')
