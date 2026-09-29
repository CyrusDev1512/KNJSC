"""Quyền điều hướng ERP theo quyết định 25.09, không áp sang lưới CRM."""
import pytest
from django.test import override_settings
from core.navigation import visible_navigation
from core.constants import Rank

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('rank', list(Rank))
def test_menu_va_url_quan_tri(client, make_user, rank):
    """AC-44.2 — Chỉ Admin thấy nhóm và truy cập trang quản trị."""
    user = make_user('user', rank)
    nav = visible_navigation(user)
    assert any(g['label']=='Quản trị' for g in nav) == (rank == Rank.ADMIN)
    client.force_login(user)
    for url in ('/nhat-ky/', '/ma-tran-quyen/', '/tac-vu/'):
        assert client.get(url).status_code == (200 if rank == Rank.ADMIN else 403), url


@pytest.mark.parametrize('rank', list(Rank))
def test_bang_du_lieu_erp_gioi_han_manager(client, make_user, rank):
    """AC-44.3 — Mọi cửa Bảng dữ liệu ERP chặn cấp dưới Manager."""
    user = make_user('user', rank)
    codes = {i['code'] for g in visible_navigation(user) for i in g['items']}
    allowed = rank in (Rank.MANAGER, 'ceo', Rank.ADMIN)
    assert ('bang' in codes) == allowed
    assert 'bieu_mau' in codes
    client.force_login(user)
    assert client.get('/bang/').status_code == (200 if allowed else 403)
    if not allowed:
        for url in ('/bang/khong-co/', '/bang/khong-co/xuat/', '/bang/khong-co/cot/',
                    '/bang/khong-co/mau-nhap.xlsx', '/bang/moi/'):
            assert client.get(url).status_code == 403, url


@override_settings(ROOT_URLCONF='knjsc.urls_bangtinh')
def test_leader_crm_khong_bi_chan_bo_sung(client, nguoi_dung, departments):
    """AC-44.5 — Leader còn vào màn quản lý bảng dùng chung qua CRM."""
    from forms_builder.models import TableDef
    TableDef.objects.create(name='Vận đơn', code='van_don', workflow='waybill', department=departments['sale'])
    client.force_login(nguoi_dung['leader_sale_1'])
    assert client.get('/bang/van_don/cot/').status_code == 200


@pytest.mark.parametrize('rank', [rank for rank in Rank if rank != Rank.ADMIN])
def test_tac_vu_ca_nhan_van_tai_duoc_khong_mo_tac_vu_nguoi_khac(client, make_user, settings, rank):
    """AC-44.4 — Tải tác vụ cá nhân vẫn được, ngoài chủ sở hữu bị từ chối."""
    from pathlib import Path
    from core.models import BackgroundJob
    from core.constants import JobKind, JobStatus
    user = make_user('chu_file', rank)
    other = make_user('nguoi_khac', rank)
    Path(settings.STORAGE_DIR, 'report-test.csv').write_text('test\n', encoding='utf-8')
    job = BackgroundJob.objects.create(kind=JobKind.EXPORT, status=JobStatus.DONE,
        created_by=user, target_type='report', result_path='report-test.csv')
    private = BackgroundJob.objects.create(kind=JobKind.EXPORT, created_by=other)
    client.force_login(user)
    html = client.get(f'/tac-vu/{job.pk}/')
    assert html.status_code == 200
    assert 'Mọi tác vụ' not in html.content.decode()
    assert client.get(f'/tac-vu/{job.pk}/tien-do/').status_code == 200
    response = client.get(f'/tac-vu/{job.pk}/tai/')
    assert response.status_code == 200
    assert b''.join(response.streaming_content) == b'test\n'
    for suffix in ('', 'tien-do/', 'tai/'):
        assert client.get(f'/tac-vu/{private.pk}/{suffix}').status_code == 404


def test_xem_toan_cong_ty_khong_cho_xem_tac_vu_nguoi_khac(make_user, monkeypatch):
    """AC-44.4 — Phạm vi dữ liệu rộng không đồng nghĩa vận hành hệ thống.

    Kiểm hợp đồng Scope riêng; nghiệm thu tài khoản CEO thực tế cần bản CEO tích hợp.
    """
    from core.models import BackgroundJob
    from core.constants import JobKind
    from core.scope import Scope
    from core import managers
    user = make_user('nguoi_xem_toan_cong_ty', Rank.MANAGER)
    other = make_user('nguoi_khac', Rank.STAFF)
    own = BackgroundJob.objects.create(kind=JobKind.EXPORT, created_by=user)
    BackgroundJob.objects.create(kind=JobKind.EXPORT, created_by=other)
    monkeypatch.setattr(managers, 'get_user_scope', lambda _: Scope(
        user_id=user.pk, rank=Rank.MANAGER, all_departments=True))
    assert list(BackgroundJob.objects.in_scope(user)) == [own]


@override_settings(ROOT_URLCONF='knjsc.urls_bangtinh')
@pytest.mark.parametrize('rank', [rank for rank in Rank if rank != Rank.ADMIN])
def test_danh_sach_tac_vu_crm_chi_admin(client, make_user, rank):
    """Danh sách vận hành hệ thống không mở cho nhân sự qua URL CRM."""
    client.force_login(make_user('crm_user', rank))
    assert client.get('/tac-vu/').status_code == 403


@override_settings(ROOT_URLCONF='knjsc.urls_bangtinh')
def test_danh_sach_tac_vu_crm_admin_duoc_xem(client, make_user):
    client.force_login(make_user('crm_admin', Rank.ADMIN))
    assert client.get('/tac-vu/').status_code == 200
