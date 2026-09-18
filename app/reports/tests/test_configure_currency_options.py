"""TL-41 — cột Đơn vị tiền của bảng báo cáo mẫu 15.09 chỉ có VND, còn báo cáo ngày tự điền
USD/CAD/PHP theo quốc gia; `configure_erp_reports` phải bổ sung ba mã tiền vào cột có sẵn."""
import pytest
from django.core.management.base import CommandError

from forms_builder.meaning import FieldType
from forms_builder.models import ColumnDef, FormDef
from forms_builder.services import record_service
from reports.management.commands.configure_erp_reports import configure_source
from reports.tests.test_aggregations import bang_mkt  # noqa: F401

pytestmark = pytest.mark.django_db


def test_existing_vnd_currency_column_gets_market_currencies(bang_mkt, nguoi_dung):
    """AC-22.12 — Cột `loai_tien` có sẵn chỉ VND: cấu hình bổ sung USD/CAD/PHP, giữ tên
    và VND, chạy lại không đổi; cột không phải Chọn một thì báo lỗi; nộp Canada → CAD."""
    ColumnDef.objects.create(table=bang_mkt, name='Đơn vị tiền', code='loai_tien',
                             field_type=FieldType.CHOICE, options=['VND'], order=91)
    FormDef.objects.create(table=bang_mkt, department=bang_mkt.department,
                           code='bc_mkt_test_ngay', name='Báo cáo Marketing ngày')
    configure_source(bang_mkt, 'mkt')
    column = ColumnDef.objects.get(table=bang_mkt, code='loai_tien')
    assert column.options == ['VND', 'USD', 'CAD', 'PHP'] and column.name == 'Đơn vị tiền'
    configure_source(bang_mkt, 'mkt')
    assert ColumnDef.objects.get(pk=column.pk).options == ['VND', 'USD', 'CAD', 'PHP']

    row = record_service.create_record(bang_mkt, {
        'ngay': '2026-09-18', 'marketer': 'mkt', 'san_pham': 'SP', 'so_mess': 2, 'cpqc': '10',
        'so_don': 1, 'doanh_so': '20', 'thi_truong': 'Canada'}, actor=nguoi_dung['staff_mkt'])
    assert row.data['loai_tien'] == 'CAD'

    column.field_type = FieldType.TEXT
    column.save(update_fields=['field_type'])
    with pytest.raises(CommandError):
        configure_source(bang_mkt, 'mkt')
