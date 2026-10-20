"""Connection riêng, đồng bộ trước service; không đặt barrier sau khóa."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection
from django.db.migrations.executor import MigrationExecutor
from django.http import Http404

from core.constants import Rank
from core.exceptions import OutOfScopeError
from org.models import UserProfile
from org.services.account_management import delete_account, reset_account_password

pytestmark = pytest.mark.django_db(transaction=True)


def run_pair(calls):
    barrier = Barrier(2)

    def run(call):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            call()
            return "ok"
        except (OutOfScopeError, Http404):
            return "denied"
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run, call) for call in calls]
        return [future.result(timeout=30) for future in futures]


def test_admin_cross_delete_keeps_one_active_admin(make_user):
    one = make_user("admin_one", Rank.ADMIN)
    two = make_user("admin_two", Rank.ADMIN)
    result = run_pair([
        lambda: delete_account(two.profile.pk, actor=one),
        lambda: delete_account(one.profile.pk, actor=two),
    ])
    assert sorted(result) == ["denied", "ok"]
    assert UserProfile.objects.alive().filter(rank=Rank.ADMIN, user__is_active=True).count() == 1


def test_delete_and_reset_never_revive_account(make_user, departments):
    admin = make_user("owner", Rank.ADMIN)
    target = make_user("target", Rank.STAFF, departments["sale"])
    run_pair([
        lambda: delete_account(target.profile.pk, actor=admin),
        lambda: reset_account_password(target.profile.pk, "New-Concurrent-Password-42!", actor=admin),
    ])
    target.refresh_from_db()
    assert not target.is_active and not target.has_usable_password()
    assert target.profile.deleted_at is not None


def test_migration_roundtrip_preserves_accounts_and_loses_deletion_mark(make_user):
    assert connection.settings_dict["NAME"].startswith("test_")
    admin = make_user("migration_admin", Rank.ADMIN)
    target = make_user("migration_target", Rank.STAFF)
    delete_account(target.profile.pk, actor=admin)
    try:
        MigrationExecutor(connection).migrate([("org", "0005_userprofile_staff_code")])
        columns = {col.name for col in connection.introspection.get_table_description(connection.cursor(), "org_userprofile")}
        assert "deleted_at" not in columns
        assert get_user_model().objects.filter(pk=target.pk, is_active=False).exists()
    finally:
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
    assert UserProfile.objects.get(user_id=target.pk).deleted_at is None
    assert not get_user_model().objects.get(pk=target.pk).is_active


def test_hai_admin_cung_tu_ha_cap_van_con_mot_admin(make_user):
    """AC-2.3 — Hai Admin cùng lúc tự hạ cấp: đúng một lượt qua, còn đúng một Admin hoạt động (TL-94)"""
    from core.exceptions import BusinessError
    from org.services import account_service
    from org.services.account_management import locked_target

    one, two = (make_user(ten, Rank.ADMIN) for ten in ("admin_one", "admin_two"))
    for u in (one, two):
        u.is_staff = u.is_superuser = True
        u.save(update_fields=["is_staff", "is_superuser"])

    def tu_ha(user):
        def goi():
            try:
                with locked_target(user, user.profile.pk) as (a, p):
                    account_service.update_profile(p, {"rank": Rank.MANAGER},
                                                   before=account_service.snapshot_profile(p), actor=a)
            except BusinessError:
                raise OutOfScopeError()
        return goi

    assert sorted(run_pair([tu_ha(one), tu_ha(two)])) == ["denied", "ok"]
    from django.contrib.auth import get_user_model
    assert get_user_model().objects.filter(profile__rank=Rank.ADMIN, is_active=True).count() == 1
