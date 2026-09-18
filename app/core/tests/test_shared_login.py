"""Phiên ERP/CRM dùng chung danh tính, vẫn kiểm quyền ở từng request."""
import json
import os
import subprocess
import sys
import time

import pytest
from django.test import Client, override_settings


def test_cookie_environment_contract():
    env = dict(os.environ, SESSION_COOKIE_DOMAIN='example.test',
               CSRF_COOKIE_DOMAIN='example.test', SESSION_COOKIE_NAME='knjsc_session_v2',
               CSRF_COOKIE_NAME='knjsc_csrf_v2')
    code = "from knjsc.settings import base as s; import json; print(json.dumps([getattr(s,k,None) for k in ['SESSION_COOKIE_DOMAIN','CSRF_COOKIE_DOMAIN','SESSION_COOKIE_NAME','CSRF_COOKIE_NAME']]))"
    actual = json.loads(subprocess.check_output([sys.executable, '-c', code], env=env))
    assert actual == ['example.test', 'example.test', 'knjsc_session_v2', 'knjsc_csrf_v2']
    for name in ['SESSION_COOKIE_DOMAIN', 'CSRF_COOKIE_DOMAIN']:
        env[name] = ''
    for name in ['SESSION_COOKIE_NAME', 'CSRF_COOKIE_NAME']:
        env.pop(name)
    assert json.loads(subprocess.check_output([sys.executable, '-c', code], env=env)) == [None, None, 'sessionid', 'csrftoken']


@pytest.fixture
def shared(settings):
    settings.SESSION_COOKIE_DOMAIN = 'example.test'
    settings.SESSION_COOKIE_NAME = 'knjsc_session_v2'
    settings.CSRF_COOKIE_DOMAIN = 'example.test'
    settings.CSRF_COOKIE_NAME = 'knjsc_csrf_v2'
    settings.SESSION_COOKIE_SECURE = True
    settings.CSRF_COOKIE_SECURE = True
    settings.CSRF_TRUSTED_ORIGINS = ['https://erp.example.test', 'https://crm.example.test']
    settings.ALLOWED_HOSTS = ['erp.example.test', 'crm.example.test', 'testserver']


@pytest.mark.django_db
@pytest.mark.parametrize('first,second', [('knjsc.urls', 'knjsc.urls_bangtinh'), ('knjsc.urls_bangtinh', 'knjsc.urls')])
@pytest.mark.parametrize('role', ['staff_sale_1', 'leader_sale_1', 'manager_sale', 'admin'])
def test_login_identity_and_logout_across_apps(shared, nguoi_dung, first, second, role):
    browser = Client()
    user = nguoi_dung[role]
    with override_settings(ROOT_URLCONF=first):
        response = browser.post('/dang-nhap/', {'username': user.username, 'password': 'matkhau-kiem-thu-1'}, secure=True)
        assert response.status_code == 302
        cookie = response.cookies['knjsc_session_v2']
        assert cookie['domain'] == 'example.test' and cookie['secure'] and cookie['httponly']
        assert cookie['samesite'] == 'Lax' and cookie['path'] == '/'
    with override_settings(ROOT_URLCONF=second):
        response = browser.get('/', secure=True)
        assert response.wsgi_request.user.pk == user.pk
        assert response.wsgi_request.user.is_authenticated
        assert browser.post('/dang-xuat/', secure=True).status_code == 302
    with override_settings(ROOT_URLCONF=first):
        assert not browser.get('/', secure=True).wsgi_request.user.is_authenticated


@pytest.mark.django_db
@pytest.mark.parametrize('invalidate', ['timeout', 'epoch', 'disabled', 'password'])
def test_shared_session_invalidated(shared, nguoi_dung, invalidate):
    browser = Client()
    user = nguoi_dung['staff_sale_1']
    with override_settings(ROOT_URLCONF='knjsc.urls'):
        browser.post('/dang-nhap/', {'username': user.username, 'password': 'matkhau-kiem-thu-1'}, secure=True)
    if invalidate == 'timeout':
        session = browser.session
        session['last_seen_at'] = int(time.time()) - 3700
        session.save()
    elif invalidate == 'epoch':
        user.profile.session_epoch += 1
        user.profile.save(update_fields=['session_epoch'])
    elif invalidate == 'disabled':
        user.is_active = False
        user.save(update_fields=['is_active'])
    else:
        user.set_password('another-test-password-209')
        user.save(update_fields=['password'])
    with override_settings(ROOT_URLCONF='knjsc.urls_bangtinh'):
        response = browser.get('/', secure=True)
        assert not response.wsgi_request.user.is_authenticated


@pytest.mark.django_db
def test_old_cookie_and_unsafe_redirect_are_not_used(shared, nguoi_dung):
    browser = Client()
    with override_settings(SESSION_COOKIE_NAME='sessionid', ROOT_URLCONF='knjsc.urls'):
        browser.force_login(nguoi_dung['admin'])
    with override_settings(ROOT_URLCONF='knjsc.urls_bangtinh'):
        assert not browser.get('/', secure=True).wsgi_request.user.is_authenticated
        response = browser.post('/dang-nhap/?next=https://untrusted.example/', {
            'username': 'staff_sale_1', 'password': 'matkhau-kiem-thu-1'}, secure=True)
        assert response.status_code == 302 and 'untrusted' not in response['Location']
        assert browser.get('/', secure=True).wsgi_request.user.pk == nguoi_dung['staff_sale_1'].pk


@pytest.mark.django_db
def test_csrf_and_first_password_change_still_required(shared, nguoi_dung):
    browser = Client(enforce_csrf_checks=True, HTTP_HOST='erp.example.test', HTTP_ORIGIN='https://erp.example.test')
    user = nguoi_dung['staff_sale_1']
    with override_settings(ROOT_URLCONF='knjsc.urls'):
        browser.get('/dang-nhap/', secure=True)
        assert browser.post('/dang-nhap/', {'username': user.username, 'password': 'matkhau-kiem-thu-1'}, secure=True).status_code == 403
        csrf = browser.cookies['knjsc_csrf_v2'].value
        assert browser.post('/dang-nhap/', {'username': user.username, 'password': 'matkhau-kiem-thu-1', 'csrfmiddlewaretoken': csrf}, secure=True).status_code == 302
    with override_settings(ROOT_URLCONF='knjsc.urls_bangtinh'):
        assert browser.post('/dang-xuat/', {'csrfmiddlewaretoken': csrf}, secure=True).status_code == 403
        user.profile.must_change_password = True
        user.profile.save(update_fields=['must_change_password'])
        assert browser.get('/', secure=True)['Location'] == '/doi-mat-khau/'
