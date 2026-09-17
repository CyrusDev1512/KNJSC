"""Khởi tạo metadata báo cáo công việc Vận đơn; không tạo đơn hoặc dòng báo cáo."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from forms_builder.models import ColumnDef, FieldDef, FormDef, FormField, FormTableLink, TableDef
from org.models import Department

COLUMNS = (
    ('ngay', 'Ngày báo cáo', 'date', 'date', True),
    ('nhan_su', 'Nhân sự', 'text', 'seller', False),
    ('cong_viec', 'Công việc đã thực hiện', 'long_text', '', True),
    ('ket_qua', 'Kết quả', 'long_text', '', True),
    ('vuong_mac', 'Vướng mắc và đề xuất', 'long_text', '', False),
)


class Command(BaseCommand):
    help = 'Tạo biểu mẫu báo cáo ngày Vận đơn theo nội dung được duyệt 16/09/2026.'

    @transaction.atomic
    def handle(self, *args, **options):
        department = Department.objects.filter(code='van-don', is_active=True).first()
        if department is None:
            raise CommandError('Chưa có bộ phận Vận đơn đang hoạt động.')
        table, _ = TableDef.objects.get_or_create(code='bao_cao_van_don_ngay', defaults={
            'name':'Báo cáo công việc Vận đơn', 'department':department,
            'description':'Báo cáo công việc ngày; tách khỏi dữ liệu đơn hàng.'})
        if table.department_id != department.pk or table.workflow:
            raise CommandError('Bảng báo cáo hiện có không khớp cấu hình; không tự ghi đè.')
        form, _ = FormDef.objects.get_or_create(code='bc_van_don_ngay', defaults={
            'name':'Báo cáo Vận đơn ngày', 'table':table, 'department':department})
        if form.table_id != table.pk or form.department_id != department.pk:
            raise CommandError('Biểu mẫu hiện có trỏ tới nguồn khác; không tự ghi đè.')
        for order, (code, name, kind, meaning, required) in enumerate(COLUMNS):
            column, _ = ColumnDef.objects.get_or_create(table=table, code=code, defaults={
                'name':name, 'field_type':kind, 'meaning':meaning, 'order':order})
            if column.field_type != kind or column.meaning != meaning:
                raise CommandError(f'Cột {code} đã có cấu hình khác; không tự thay đổi.')
            if FormTableLink.objects.filter(form_field__form=form, column=column).exists():
                continue
            field, _ = FieldDef.objects.get_or_create(department=department,
                code='bc_vd_'+code, defaults={'name':name, 'field_type':kind, 'meaning':meaning})
            form_field = FormField.objects.create(form=form, field=field, order=order, required=required)
            FormTableLink.objects.create(form_field=form_field, column=column)
        self.stdout.write('Đã cấu hình báo cáo ngày Vận đơn; không tạo dữ liệu đơn hàng.')
