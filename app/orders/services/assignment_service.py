"""Phân công vận đơn: quyền theo ID, khoá dòng cha và CAS cho cả lượt."""
from orders.constants import waybill_condition
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from core.audit import record as audit
from core.constants import AuditAction, Rank
from core.exceptions import BusinessError, OutOfScopeError
from core.scope import get_user_scope

FIELDS = {'delivery': ('van-don',), 'care': ('sale', 'cskh'), 'marketing': ('marketing',)}
COLUMNS = {'phu_trach_vd': 'delivery', 'phu_trach_cskh': 'care', 'phu_trach_mkt': 'marketing'}
LABELS = {'delivery': 'Vận đơn', 'care': 'CSKH', 'marketing': 'Marketing'}


def department(user):
    profile = getattr(user, 'profile', None)
    return profile.department.code if profile and profile.department_id else ''


def is_accountant(user):
    profile = getattr(user, 'profile', None)
    dept = getattr(profile, 'department', None)
    return bool(user.is_active and dept and dept.code == 'ke-toan'
                and dept.is_active and dept.deleted_at is None)


def can_assign(user):
    scope = get_user_scope(user)
    return user.is_active and (scope.is_admin or (
        department(user) == 'van-don' and scope.rank in (Rank.LEADER, Rank.MANAGER)))


def field_for(user):
    """Trường phân công ứng với bộ phận của người dùng — nút Tôi / Toàn bộ (ADR-033):
    'delivery' | 'care' | 'marketing'; None với Admin, Kế toán và bộ phận khác."""
    dept = department(user)
    return next((f for f, depts in FIELDS.items() if dept in depts), None)


def scope_condition(user, original, *, only_new=False):
    """Chỉ thay ngoại lệ của bảng mới; original là điều kiện quyền bảng cũ.

    Nhân viên Vận đơn thấy **toàn bộ** dòng của bảng vận đơn, kể cả dòng chưa
    phân công — mặc định công ty chốt 17.09.2026 (ADR-033, thay ADR-020/026).
    Lọc "chỉ dòng tôi phụ trách" là việc của tham số `cua_toi` ở lưới.
    """
    scope = get_user_scope(user)
    dept = department(user)
    new = waybill_condition()
    if can_assign(user) or is_accountant(user) or dept == 'van-don':
        allowed = Q()
    elif dept == 'cskh':
        allowed = Q(assignment__care_id=user.pk)
    elif dept == 'sale':
        own = Q(created_by_id=user.pk) | Q(order__created_by_id=user.pk) | Q(order__seller_id=user.pk)
        allowed = own | Q(assignment__care_id=user.pk)
        if scope.rank != Rank.STAFF:
            allowed |= original
    else:
        allowed = original
    # Caller đã giới hạn đúng bảng mới: bỏ nhánh bảng khác khỏi SQL,
    # vẫn dùng cùng điều kiện nghiệp vụ, không nhân bản quy tắc quyền.
    return allowed if only_new else (~new & original) | (new & allowed)


def label(user):
    if user is None:
        return ''
    return user.get_username()


def candidates(field):
    return get_user_model().objects.filter(is_active=True,
        profile__department__code__in=FIELDS[field]).filter(
        Q(profile__locked_until__isnull=True) | Q(profile__locked_until__lte=timezone.now())
    ).select_related('profile').order_by('username')


def display(row, code):
    assignment = getattr(row, 'assignment', None)
    return label(getattr(assignment, COLUMNS[code], None))


def related(queryset):
    return queryset.select_related('assignment__delivery__profile', 'assignment__care__profile',
                                   'assignment__marketing__profile', 'order__seller')


def integer(value):
    """Không làm tròn số thực hoặc nhận boolean làm ID/phiên bản."""
    if type(value) is not int and not (isinstance(value, str) and value.isascii() and value.isdecimal()):
        raise ValueError('Cần số nguyên')
    number = int(value)
    if not 0 <= number <= 2**63 - 1:
        raise ValueError('Số nằm ngoài giới hạn')
    return number


@transaction.atomic
def assign(user, versions, changes, *, request=None):
    from forms_builder.models import DataRecord
    from orders.models import WaybillAssignment
    if not can_assign(user):
        raise OutOfScopeError('Chỉ Leader/Manager Vận đơn và Admin được phân công.')
    if not isinstance(versions, dict) or not versions or not isinstance(changes, dict):
        raise BusinessError('Chọn dòng và người cần phân công.')
    if set(changes) - FIELDS.keys() or not changes:
        raise BusinessError('Trường phân công không hợp lệ.')
    try:
        expected = {integer(pk): integer(version) for pk, version in versions.items()}
    except (ValueError, TypeError):
        raise BusinessError('Phiên bản phân công không hợp lệ.')
    if len(expected) != len(versions) or any(v < 0 for v in expected.values()):
        raise BusinessError('Phiên bản phân công không hợp lệ.')
    targets = {}
    for field, value in changes.items():
        if value is None:
            targets[field] = None
        else:
            try:
                target = candidates(field).filter(pk=integer(value)).first()
            except (ValueError, TypeError):
                target = None
            if target is None:
                raise BusinessError(f'{LABELS[field]}: tài khoản bị khoá hoặc không đúng bộ phận.')
            targets[field] = target
    # Tất cả đường ghi lưới cũng khoá dòng cha; không khoá phía nullable của LEFT JOIN.
    rows = list(DataRecord.objects.filter(waybill_condition(),
        pk__in=expected).select_for_update(of=('self',)).order_by('pk'))
    if len(rows) != len(expected):
        raise OutOfScopeError()
    result = {}
    for row in rows:
        assignment = getattr(row, 'assignment', None)
        version = assignment.version if assignment else 0
        if expected[row.pk] != version:
            raise BusinessError('Phân công vừa được thay đổi. Tải lại để xem trước khi lưu.', code='conflict')
        if assignment is None:
            assignment = WaybillAssignment(record=row)
        before = {f: getattr(assignment, f + '_id') for f in targets}
        for field, target in targets.items():
            setattr(assignment, field, target)
        assignment.version += 1
        assignment.save()
        # Polling phát hiện dòng đổi mà không chép tên/ID vào JSON nghiệp vụ.
        DataRecord.objects.filter(pk=row.pk).update(updated_at=timezone.now())
        after = {f: getattr(assignment, f + '_id') for f in targets}
        audit(AuditAction.UPDATE, actor=user, target=row, request=request,
              detail=f'Phân công v{assignment.version}: {before} → {after}')
        result[row.pk] = assignment.version
    return result
