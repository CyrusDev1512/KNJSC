"""Bổ sung đúng 100 dòng mẫu đã duyệt; không chạy seed chung hoặc sửa bảng cũ."""
from datetime import date
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.db.models import Count
from core.audit import record as audit
from core.constants import AuditAction, Rank
from core.management.commands.du_lieu_mau import COT_BC_MKT, COT_TINH_BC_MKT
from forms_builder.models import DataRecord, TableDef
from forms_builder.services import table_service, record_service, form_service
from org.models import Department, Team, UserProfile
from org.services import org_service
from reports.management.commands.configure_erp_reports import SALE_COLUMNS, configure_source

TAG = 'KNJSC-MAU-BAOCAO-20260915-PC'
CODES = ('bao_cao_mkt', 'bao_cao_sale')
NAMES = (
    'Nguyễn Minh Anh', 'Trần Hoài An', 'Lê Tuấn Phong', 'Phạm Ngọc Mai',
    'Hoàng Gia Bảo', 'Vũ Khánh Linh', 'Đặng Thanh Tùng', 'Bùi Thu Hà',
    'Đỗ Nhật Nam', 'Ngô Hải Yến', 'Phan Quang Huy', 'Dương Thảo Vy',
    'Lý Đức Minh', 'Võ Phương Nhi', 'Mai Anh Khoa', 'Tạ Bảo Ngọc',
    'Đinh Tiến Dũng', 'Cao Mỹ Duyên', 'Hồ Trung Kiên', 'Trịnh Thanh Trúc',
)

def verify():
    result = []
    for code in CODES:
        table = TableDef.objects.get(code=code)
        assert TAG in table.description
        rows = list(DataRecord.objects.filter(table=table).select_related('created_by__profile', 'team'))
        assert len(rows) == 50
        assert len({r.team_id for r in rows}) == 5
        assert len({r.created_by_id for r in rows}) == 10
        for row in rows:
            profile = row.created_by.profile
            assert row.team_id == profile.team_id and row.department_id == profile.department_id == table.department_id
            assert not row.created_by.is_active and not row.created_by.has_usable_password()
            assert row.data['ghi_chu'].startswith(TAG)
            assert row.data['team_mau'] == row.team.name
            assert row.data['loai_tien'] == 'VND'
        result.append({'table':code, 'rows':len(rows), 'teams':5, 'people':10,
                       'dates':sorted({str(r.val_date) for r in rows})})
    return result

@transaction.atomic
def provision(admin_username='quantri'):
    with connection.cursor() as cursor:
        cursor.execute('SELECT pg_try_advisory_xact_lock(hashtext(%s))', [TAG])
        if not cursor.fetchone()[0]:
            raise RuntimeError('Một phiên khác đang tạo cùng bộ dữ liệu mẫu.')
    admin = get_user_model().objects.get(username=admin_username, is_active=True, is_superuser=True)
    existing = list(TableDef.all_objects.filter(code__in=CODES))
    if existing:
        if len(existing) == 2 and all(TAG in t.description and t.deleted_at is None for t in existing):
            return {'already_present':True, 'verified':verify()}
        raise RuntimeError('Đã có bảng báo cáo ngoài bộ mẫu; dừng để không ghi đè.')
    User = get_user_model()
    if User.objects.filter(username__startswith='mau_baocao_').exists():
        raise RuntimeError('Tên tài khoản mẫu đã tồn tại; không sửa tài khoản cũ.')
    before = dict(DataRecord.objects.exclude(table__code__in=CODES).values('table_id').annotate(n=Count('id')).values_list('table_id','n'))
    for group, (department_code, department_name, table_code, table_name, owner_column) in enumerate((
        ('marketing','Marketing','bao_cao_mkt','Báo cáo Marketing','marketer'),
        ('sale','Sale','bao_cao_sale','Báo cáo Sale','sale'),
    )):
        department = Department.all_objects.filter(code=department_code).first()
        if department is None:
            department = org_service.create_department(name=department_name, code=department_code, actor=admin)
        if department.deleted_at or not department.is_active:
            raise RuntimeError('Bộ phận hiện có đã ngừng hoạt động; không tự kích hoạt.')
        table = table_service.create_table(name=table_name, code=table_code, department=department,
            description=TAG + ' — 50 dòng dữ liệu kiểm thử, tên nhân sự và số liệu đều là mẫu; tiền VND.', actor=admin)
        base = [(code,name,kind,meaning) for name,code,kind,meaning in COT_BC_MKT] if group == 0 else SALE_COLUMNS
        for order,(code,name,kind,meaning) in enumerate(base):
            table_service.add_column(table, actor=admin, code=code, name=name, field_type=kind, meaning=meaning, order=order)
        if group == 0:
            for order,(name,code,operation,left,right,decimals) in enumerate(COT_TINH_BC_MKT,start=20):
                table_service.add_column(table, actor=admin, code=code, name=name, field_type='money',
                    is_computed=True, compute_op=operation, compute_left=left, compute_right=right,
                    compute_decimals=decimals, order=order)
        for order,code,name,kind,options in (
            (1,'team_mau','Team','text',[]),
            (91,'loai_tien','Đơn vị tiền','choice',['VND']),
            (92,'ghi_chu','Ghi chú','text',[]),
        ):
            table_service.add_column(table, actor=admin, code=code, name=name, field_type=kind, options=options, order=order)
        form_service.create_form(name=f'{table_name} ngày', code='bc_mkt_ngay' if group==0 else 'bc_sale_ngay',
            department=department, table=table, actor=admin)
        configure_source(table, 'mkt' if group==0 else 'sale')
        columns = list(table.columns.all())
        for team_index in range(5):
            team = org_service.create_team(name=f'Mẫu — {department_name} {team_index+1:02}', department=department, actor=admin)
            for member in range(2):
                index = team_index*2 + member
                name = 'Mẫu — ' + NAMES[group*10 + index]
                user = User.objects.create_user(username=f'mau_baocao_{department_code}_{index+1:02}', password=None, is_active=False)
                UserProfile.objects.create(user=user, full_name=name, rank=Rank.STAFF, department=department,
                                           team=team, must_change_password=False)
                audit(AuditAction.CREATE, actor=admin, target=user, detail=TAG + ': tạo nhân sự mẫu, vô hiệu hóa đăng nhập.')
                for day in range(11,16):
                    orders = 3 + index + (day-11)*2
                    values = {'ngay':date(2026,9,day), owner_column:name, 'team_mau':team.name,
                        'so_mess':40+index*13+(day-11)*7, 'so_don':orders,
                        'doanh_so':Decimal(orders)*Decimal('250000.00'),
                        'thi_truong':'Canada' if index%2==0 else 'Philippines', 'loai_tien':'VND',
                        'ghi_chu':TAG + ' — Dữ liệu mẫu, chưa gắn sản phẩm; không phải báo cáo đã nộp.'}
                    if group==0:
                        values['cpqc'] = Decimal(40000+index*1500+(day-11)*2000)
                    else:
                        values['ngay_ra_don'] = date(2026,9,day)
                    record_service.create_record(table, values, actor=user, columns=columns)
    after = dict(DataRecord.objects.exclude(table__code__in=CODES).values('table_id').annotate(n=Count('id')).values_list('table_id','n'))
    # Không khóa bảng vận đơn: nếu người thật vừa ghi, chỉ báo số đếm thay đổi để đối chiếu.
    return {'already_present':False, 'verified':verify(), 'other_table_counts_before':before, 'other_table_counts_after':after}
