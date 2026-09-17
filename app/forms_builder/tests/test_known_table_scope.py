"""Phạm vi bảng đã biết: cùng quyền, không dựng lại truy vấn toàn hệ thống."""
import pytest
from django.contrib.auth import get_user_model
from forms_builder.models import DataRecord, Grant, GrantAction, TableDef

pytestmark = pytest.mark.django_db


@pytest.fixture
def scope_tables(departments, nguoi_dung):
    tables = []
    for code, department in [('scope_sale', 'sale'), ('scope_mkt', 'mkt'),
                             ('van_don', 'vd'), ('van_don_moi', 'vd')]:
        table = TableDef.objects.create(code=code, name=code, department=departments[department])
        for user in nguoi_dung.values():
            if user.profile.department_id == table.department_id:
                row = DataRecord.objects.create(table=table, data={}, created_by=user,
                    department=table.department, team=user.profile.team)
        # Có tombstone để kiểm cả manager thông thường và manager lịch sử.
        DataRecord.objects.create(table=table, data={}, created_by=row.created_by,
            department=table.department).delete(by=nguoi_dung['admin'])
        tables.append(table)
    return tables


def test_known_scope_matches_global_for_roles_grants_and_soft_delete(scope_tables, nguoi_dung, teams):
    for table in scope_tables:
        for shared in (False, True):
            table.is_shared = shared
            table.save(update_fields=['is_shared'])
            for granted in (False, True):
                grants = []
                if granted:
                    grants = [Grant.objects.create(table=table, user=nguoi_dung['staff_mkt'], action=GrantAction.VIEW),
                              Grant.objects.create(table=table, team=teams['sale2'], action=GrantAction.EDIT)]
                for source in nguoi_dung.values():
                    # Cache quyền chỉ có vòng đời request, không dùng lại sau cấp quyền.
                    user = get_user_model().objects.get(pk=source.pk)
                    for manager in (DataRecord.objects, DataRecord.all_objects):
                        expected = set(manager.in_scope(user).filter(table=table).values_list('pk', flat=True))
                        actual = set(manager.in_scope(user, table=table).values_list('pk', flat=True))
                        assert actual == expected, (table.code, shared, granted, user.username)
                for grant in grants:
                    grant.delete()
        for field in ('is_active', 'deleted_at'):
            from django.utils import timezone
            setattr(table, field, False if field == 'is_active' else timezone.now())
            table.save(update_fields=[field])
            for source in nguoi_dung.values():
                user = get_user_model().objects.get(pk=source.pk)
                assert not DataRecord.all_objects.in_scope(user, table=table).exists()
            setattr(table, field, True if field == 'is_active' else None)
            table.save(update_fields=[field])
        # Model bảng có thể được đọc trước khi quyền dùng chung thay đổi.
        # Quyền phải theo trạng thái SQL hiện hành, không theo object đã giữ.
        for current in (False, True):
            table.is_shared = not current
            TableDef.objects.filter(pk=table.pk).update(is_shared=current)
            for source in nguoi_dung.values():
                user = get_user_model().objects.get(pk=source.pk)
                expected = set(DataRecord.objects.in_scope(user).filter(table=table).values_list('pk', flat=True))
                assert set(DataRecord.objects.in_scope(user, table=table).values_list('pk', flat=True)) == expected


@pytest.mark.parametrize('code,user_key', [('scope_sale', 'staff_sale_1'),
    ('scope_mkt', 'staff_mkt'), ('van_don', 'staff_vd')])
def test_known_ordinary_table_does_not_scan_permission_subquery(scope_tables, nguoi_dung, code, user_key):
    table = next(t for t in scope_tables if t.code == code)
    query = DataRecord.objects.in_scope(nguoi_dung[user_key], table=table)
    sql = str(query.query).upper()
    assert 'ORDERS_ORDER' not in sql and 'ORDERS_WAYBILLASSIGNMENT' not in sql
    # Một SELECT phạm vi: không quét lại tập ID toàn bảng qua IN (SELECT ...).
    assert sql.count('SELECT') == 1
    assert query.exists()
