"""Quyết định 16/09/2026: ngày hệ thống, sửa có phân quyền và chống ghi đè."""
from core.identity import employee_code
import pytest
from django.utils import timezone
from reports.models import DailyReport
from reports.tests.test_bao_cao_ngay import bm_sale, _nop

pytestmark = pytest.mark.django_db


def test_submit_ignores_forged_report_dates(client, bm_sale, nguoi_dung):
    client.force_login(nguoi_dung['staff_sale_1'])
    response = client.post('/bao-cao/', {'bieu_mau': bm_sale.code,
        'ngay_bao_cao': '2000-01-01', 'ngay': '2000-01-02', 'so_mess': '100'})
    assert response.status_code == 302
    report = DailyReport.objects.get()
    assert report.report_date == timezone.localdate()
    assert report.record.data['ngay'] == timezone.localdate().isoformat()


@pytest.mark.parametrize('role,allowed', [
    ('staff_sale_1', False), ('staff_sale_1b', False), ('leader_sale_1', True),
    ('leader_sale_2', False), ('manager_sale', True), ('manager_mkt', False), ('admin', True)])
def test_amend_scope_and_revision(client, bm_sale, nguoi_dung, role, allowed):
    report = _nop(bm_sale, nguoi_dung['staff_sale_1'])
    client.force_login(nguoi_dung[role])
    url = f'/bao-cao/{report.pk}/sua/'
    response = client.get(url)
    if not allowed:
        assert response.status_code in (403, 404)
        assert client.post(url, {'so_mess': '250'}).status_code in (403, 404)
        report.record.refresh_from_db()
        assert report.record.data['so_mess'] == 1000
        return
    assert response.status_code == 200
    version = response.context['version']
    response = client.post(url, {'version': version, 'so_mess': '250', 'so_don': '50',
        'doanh_so': '5000000', 'ngay': '1999-01-01'})
    assert response.status_code == 302
    report.refresh_from_db()
    report.record.refresh_from_db()
    assert report.record.data['so_mess'] == 250

    assert report.record.data['ngay'] == report.report_date.isoformat()
    assert report.created_by == nguoi_dung['staff_sale_1']
    assert report.revisions.count() == 1
    revision = report.revisions.get()
    assert revision.actor == nguoi_dung[role]
    assert revision.before['so_mess'] == 1000 and revision.after['so_mess'] == 250
    assert client.post(url, {'version': version, 'so_mess': '999'}).status_code == 409
    report.record.refresh_from_db()
    assert report.record.data['so_mess'] == 250


def test_submitted_record_cannot_be_changed_from_grid(bm_sale, nguoi_dung):
    from forms_builder.services import grant_service, record_service
    from core.exceptions import BusinessError
    report = _nop(bm_sale, nguoi_dung['staff_sale_1'])
    assert not grant_service.can_edit_record(nguoi_dung['staff_sale_1'], report.record)
    with pytest.raises(BusinessError):
        record_service.update_cell(report.record, 'so_mess', '999', actor=nguoi_dung['admin'])


def test_marketing_configure_adds_inputs_and_confirmed_formulas(bm_sale):
    from reports.management.commands.configure_erp_reports import configure_source
    from forms_builder.models import ColumnDef
    from forms_builder.services import record_service
    from decimal import Decimal
    table = bm_sale.table
    ColumnDef.objects.create(table=table, code='san_pham', name='Sản phẩm', field_type='text', meaning='product')
    ColumnDef.objects.create(table=table, code='cpqc', name='CPQC', field_type='money')
    configure_source(table, 'mkt')
    table.refresh_from_db()
    # Doanh thu suy ra từ vận đơn (ADR-038): không ánh xạ, không cột nhập; Hóa đơn vẫn nhập
    assert 'revenue' not in table.erp_report.columns
    assert table.erp_report.columns['invoice'] == 'hoa_don'
    assert table.erp_report.columns['segment'] == 'tep_khach_hang'
    configure_source(table, 'mkt')
    row = record_service.create_record(table, {'ngay':'2026-09-16', 'so_mess':100,
        'so_don':20, 'cpqc':Decimal('200'), 'doanh_so':Decimal('1000'),
        'hoa_don':Decimal('75'), 'thi_truong':'Canada'})
    assert {key: Decimal(row.data[key]) for key in ('cpo','gia_mess','cpqc_doanh_so','aov')} == {
        'cpo':Decimal('10'), 'gia_mess':Decimal('2'), 'cpqc_doanh_so':Decimal('.2'), 'aov':Decimal('50')}
    assert 'hoa_don_doanh_thu' not in row.data


def test_report_formula_does_not_divide_rounded_intermediates(bm_sale):
    from reports.management.commands.configure_erp_reports import configure_source
    from forms_builder.models import ColumnDef, DataRecord
    from reports.services.daily_service import compute_report
    from decimal import Decimal
    table = bm_sale.table
    ColumnDef.objects.create(table=table, code='san_pham', name='Sản phẩm', field_type='text', meaning='product')
    ColumnDef.objects.create(table=table, code='cpqc', name='CPQC', field_type='money')
    configure_source(table, 'mkt')
    table.refresh_from_db()
    row = DataRecord(table=table, data={'cpqc':'0.01', 'so_mess':100000, 'so_don':1000, 'doanh_so':'0'})
    compute_report(row, table, list(table.columns.all()))
    # Hóa đơn/Doanh thu không còn tính từng dòng (ADR-038); các tỉ số khác làm tròn đúng chỗ
    assert 'hoa_don_doanh_thu' not in row.data
    assert Decimal(row.data['gia_mess']) == Decimal('0.0000') and Decimal(row.data['cpo']) == Decimal('0.0000')
    assert row.data['cpqc_doanh_so'] is None
    row.data['cpqc'] = '0'
    compute_report(row, table, list(table.columns.all()))
    assert Decimal(row.data['cpo']) == Decimal('0')
    assert Decimal(row.data['aov']) == 0


def test_revision_cannot_be_rewritten(client, bm_sale, nguoi_dung):
    from reports.services import daily_service
    report = _nop(bm_sale, nguoi_dung['staff_sale_1'])
    daily_service.amend(report, {'so_mess':'5'}, version=report.record.updated_at.isoformat(), actor=nguoi_dung['leader_sale_1'])
    revision = report.revisions.get()
    with pytest.raises(RuntimeError):
        revision.save()
    with pytest.raises(RuntimeError):
        report.revisions.update(before={})
    with pytest.raises(RuntimeError):
        report.revisions.all().delete()
    client.force_login(nguoi_dung['staff_sale_1'])
    assert 'Lịch sử chỉnh sửa' in client.get(f'/bao-cao/{report.pk}/').content.decode()
    client.force_login(nguoi_dung['staff_sale_2'])
    assert client.get(f'/bao-cao/{report.pk}/').status_code == 404


def test_new_marketing_report_derives_currency_and_keeps_zero(client, bm_sale, nguoi_dung):
    from forms_builder.models import ColumnDef
    from reports.management.commands.configure_erp_reports import configure_source
    table = bm_sale.table
    ColumnDef.objects.create(table=table, code='san_pham', name='Sản phẩm', field_type='text', meaning='product')
    ColumnDef.objects.create(table=table, code='cpqc', name='CPQC', field_type='money')
    configure_source(table, 'mkt')
    values = {'ngay':'1999-01-01', 'so_mess':'0', 'cpqc':'0', 'so_don':'0',
              'doanh_so':'0', 'hoa_don':'0', 'san_pham':'Mẫu',
              'thi_truong':'Canada', 'loai_tien':'USD'}
    payload = {f.field.code:values.get(f.link.column.code,'') for f in bm_sale.ordered_fields()}
    client.force_login(nguoi_dung['staff_sale_1'])
    response = client.post('/bao-cao/', {**payload,'bieu_mau':bm_sale.code, 'ngay_bao_cao':'1999-01-01'})
    assert response.status_code == 302
    report = DailyReport.objects.get()
    assert report.record.data['loai_tien'] == 'CAD'
    assert report.record.data['ngay'] == timezone.localdate().isoformat()
    assert report.record.data['hoa_don'] == '0'
    assert 'doanh_thu' not in report.record.data and 'hoa_don_doanh_thu' not in report.record.data
    client.force_login(nguoi_dung['manager_sale'])
    detail = client.get(f'/bao-cao/{report.pk}/sua/')
    assert 'value="0"' in detail.content.decode()


def test_summary_converts_currencies_to_vnd_before_adding(bm_sale, nguoi_dung):
    """Báo cáo Sale lẫn CAD và USD: quy ₫ từng dòng rồi mới cộng (ADR-040), không để trống"""
    from decimal import Decimal
    from forms_builder.models import DataRecord
    from reports.models import ReportSource
    from reports.services.activity_service import build
    from reports.aggregations import total_values
    source = ReportSource.objects.create(table=bm_sale.table, kind='sale', columns={
        'mess':'so_mess','orders':'so_don','sales':'doanh_so','market':'thi_truong','currency':'loai_tien'})
    for market, currency in [('Canada','CAD'),('Hoa Kỳ','USD')]:
        DataRecord.objects.create(table=bm_sale.table, department=bm_sale.department,
            created_by=nguoi_dung['staff_sale_1'], data={'ngay':'2026-09-16','so_mess':10,
            'so_don':2,'doanh_so':'100','thi_truong':market,'loai_tien':currency})
    result = build(nguoi_dung['manager_sale'], source)
    values = dict(zip([c.label for c in result.columns], total_values(result)))
    assert values['Số Mess'] == 20
    assert values['Doanh số'] == Decimal('100') * 17500 + Decimal('100') * 25500
    assert result.currency_label.startswith('VND') and not result.currency_warning
    filtered = build(nguoi_dung['manager_sale'], source, market='Canada')
    values = dict(zip([c.label for c in filtered.columns], total_values(filtered)))
    assert values['Doanh số'] == Decimal('100') * 17500


def test_report_grid_cannot_override_system_fields(bm_sale, nguoi_dung):
    from forms_builder.models import ColumnDef
    from forms_builder.services import record_service
    from core.exceptions import BusinessError
    from reports.management.commands.configure_erp_reports import configure_source
    from crm.services.master_grid_service import metadata
    table = bm_sale.table
    ColumnDef.objects.create(table=table, code='san_pham', name='Sản phẩm', field_type='text', meaning='product')
    ColumnDef.objects.create(table=table, code='seller', name='Nhân sự', field_type='text', meaning='seller')
    configure_source(table, 'sale')
    table.refresh_from_db()
    row = record_service.create_record(table, {'ngay':'1999-01-01','seller':'gia_mao',
        'thi_truong':'Canada','loai_tien':'USD','so_mess':0}, actor=nguoi_dung['staff_sale_1'])
    assert row.data['ngay'] == timezone.localdate().isoformat()
    assert row.data['seller'] == employee_code(nguoi_dung['staff_sale_1'])
    assert row.data['loai_tien'] == 'CAD'
    for code, value in [('ngay','2000-01-01'),('seller','gia_mao'),('loai_tien','USD')]:
        with pytest.raises(BusinessError):
            record_service.update_cell(row, code, value, actor=nguoi_dung['admin'])
    columns = list(table.columns.all())
    for column in columns:
        column.table = table
    protected = {item['code'] for item in metadata(columns) if item['protected']}
    assert {'ngay','seller','loai_tien'} <= protected
