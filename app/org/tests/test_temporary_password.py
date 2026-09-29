"""AC-1.5, KNJSC 02.3 — tạo và bàn giao mật khẩu tạm."""
import pytest
from django.contrib.auth import get_user_model
from core.models import AuditLog

pytestmark = pytest.mark.django_db

@pytest.mark.parametrize('password', ['', 'TayNhap-Kn2026!'])
def test_admin_creates_temporary_password(client, nguoi_dung, departments, password):
    client.force_login(nguoi_dung['admin'])
    payload = dict(username='HungPT', full_name='Phạm Hùng',
                   rank='staff', department=departments['sale'].pk, password=password)
    response = client.post('/nhan-su/moi/', payload)
    assert response.status_code == 200
    temporary = response.context['temporary_password']
    user = get_user_model().objects.get(username='HungPT')
    assert user.check_password(temporary) and user.profile.must_change_password
    if password:
        assert temporary == password
    else:
        assert len(temporary) == 16
        assert any(c.islower() for c in temporary)
        assert any(c.isupper() for c in temporary)
        assert any(c.isdigit() for c in temporary)
    assert 'no-store' in response['Cache-Control']
    assert temporary not in str(dict(client.session))
    assert not AuditLog.objects.filter(detail__contains=temporary).exists()
    assert temporary not in client.get('/nhan-su/moi/').content.decode()
    repeated = client.post('/nhan-su/moi/', payload)
    assert repeated.status_code == 200 and repeated.context['form'].errors
    user.refresh_from_db()
    assert user.check_password(temporary)
    assert get_user_model().objects.filter(username='HungPT').count() == 1

@pytest.mark.parametrize('password', ['123456789012', 'password123'])
def test_reject_weak_manual_password(client, nguoi_dung, departments, password):
    client.force_login(nguoi_dung['admin'])
    response=client.post('/nhan-su/moi/', dict(username='WeakUser',
        full_name='Weak User', rank='staff', department=departments['sale'].pk, password=password))
    assert response.status_code==200 and response.context['form'].errors
    assert not get_user_model().objects.filter(username='WeakUser').exists()
