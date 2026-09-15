"""Thao tác vận hành có xác nhận cho bảng đã chứa dữ liệu; không chạy trong seed."""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from core.exceptions import BusinessError, OutOfScopeError
from forms_builder.models import TableDef
from orders.services import destination_service


class Command(BaseCommand):
    help = 'Chuẩn bị bảng đã được duyệt chuyển sang nghiệp vụ Vận đơn, giữ nguyên dòng cũ'

    def add_arguments(self, parser):
        parser.add_argument('--table', required=True, help='Mã bảng đã được duyệt chuyển đổi')
        parser.add_argument('--actor', required=True, help='Mã tài khoản Admin thực hiện')
        parser.add_argument('--expected-rows', required=True, type=int,
                            help='Số dòng đã xác nhận, gồm cả dòng xóa mềm')

    def handle(self, *args, **options):
        try:
            actor = get_user_model().objects.get(username=options['actor'], is_active=True)
            table = TableDef.all_objects.get(code=options['table'])
            destination_service.prepare_existing(actor, table.pk, expected_rows=options['expected_rows'])
        except (get_user_model().DoesNotExist, TableDef.DoesNotExist):
            raise CommandError('Không tìm thấy bảng hoặc tài khoản đang hoạt động.')
        except (BusinessError, OutOfScopeError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(
            f'Bảng {table.code} sẵn sàng được chọn nhận đơn; dữ liệu và đích hiện hành giữ nguyên.'))
