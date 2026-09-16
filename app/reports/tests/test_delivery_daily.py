"""Báo cáo ngày Vận đơn dùng biểu mẫu riêng, không ghi vào bảng đơn hàng."""
from datetime import date

import pytest
from django.core.management import call_command

from forms_builder.models import DataRecord, FormDef
from reports.models import DailyReport
from reports.services import daily_service

pytestmark = pytest.mark.django_db


def test_delivery_daily_configure_submit_history(client, departments, nguoi_dung):
    call_command('configure_delivery_daily_report')
    call_command('configure_delivery_daily_report')
    form = FormDef.objects.get(code='bc_van_don_ngay')
    assert form.table.code == 'bao_cao_van_don_ngay'
    assert form.fields.count() == 5
    assert not DataRecord.objects.exists()
    user = nguoi_dung['staff_vd']
    assert form in daily_service.forms_for(user)
    assert form not in daily_service.forms_for(nguoi_dung['staff_sale_1'])
    values = {f.field.code: {'ngay':'2026-09-16', 'nhan_su':'gia_mao',
        'cong_viec':'Liên hệ hãng vận chuyển', 'ket_qua':'Đã cập nhật đơn',
        'vuong_mac':'Chờ xác nhận địa chỉ'}[f.link.column.code] for f in form.ordered_fields()}
    report = daily_service.submit(form, values, report_date=date(2026,9,16), actor=user)
    assert report.record.data['nhan_su'] == user.username
    assert report.record.table_id == form.table_id
    assert DailyReport.objects.count() == 1
    client.force_login(user)
    history = client.get('/bao-cao/lich-su/')
    assert history.status_code == 200
    assert history.context['trang'].paginator.count == 1
    assert 'Doanh số:' not in history.content.decode()
    assert 'Liên hệ hãng vận chuyển' in client.get(f'/bao-cao/{report.pk}/').content.decode()
    client.force_login(nguoi_dung['staff_sale_1'])
    assert client.get('/bao-cao/', {'bieu_mau':form.code}).status_code == 403
    assert client.get(f'/bao-cao/{report.pk}/').status_code == 404
