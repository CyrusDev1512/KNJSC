"""Đặt lại mật khẩu qua form thật; không giữ mật khẩu rõ sau gửi."""
import re
import pytest
from playwright.sync_api import expect

from core.constants import Rank
from .conftest import chup

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]


@pytest.mark.parametrize('role', ['manager_sale', 'ceo', 'admin'])
@pytest.mark.parametrize('width', [1440, 390])
def test_reset_login_and_reveal(live_server, trinh_duyet, dang_nhap, nguoi_dung,
                                make_user, role, width):
    """Reset hủy phiên cũ; mật khẩu mới dùng ngay, nút hiện/ẩn không lưu lại giá trị."""
    actor = make_user('ceo_browser', Rank.CEO) if role == 'ceo' else nguoi_dung[role]
    target = nguoi_dung['staff_sale_1']
    new_password = 'E2E-Reset-Only-2026!'
    ctx = trinh_duyet.new_context(viewport={'width': width, 'height': 900}, locale='vi-VN')
    staff_ctx = trinh_duyet.new_context()
    page, staff = ctx.new_page(), staff_ctx.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    try:
        dang_nhap(staff, target)
        dang_nhap(page, actor)
        response = page.goto(f'{live_server.url}/nhan-su/{target.profile.pk}/sua/')
        assert response.status == 200
        first = page.locator('[name=new_password1]')
        second = page.locator('[name=new_password2]')
        toggle = page.locator('[data-password-toggle=id_new_password1]')
        first.fill(new_password)
        second.fill(new_password)
        expect(first).to_have_attribute('type', 'password')
        toggle.click()
        expect(first).to_have_attribute('type', 'text')
        expect(first).to_have_value(new_password)
        expect(second).to_have_attribute('type', 'password')
        toggle.press('Enter')
        expect(first).to_have_attribute('type', 'password')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.get_by_role('button', name='Đặt lại mật khẩu', exact=True).click()
        expect(page.get_by_text('Đã đặt lại mật khẩu. Người dùng có thể đăng nhập bằng mật khẩu mới.', exact=True)).to_be_visible()
        expect(first).to_have_value('')
        expect(second).to_have_value('')
        page.reload()
        expect(first).to_have_value('')
        assert new_password not in page.content()
        target.refresh_from_db()
        assert target.check_password(new_password) and target.password != new_password
        assert not target.profile.must_change_password
        staff.reload()
        expect(staff).to_have_url(re.compile(r'/dang-nhap/'))
        dang_nhap(staff, target, mat_khau=new_password)
        assert '/doi-mat-khau/' not in staff.url
        assert staff.goto(live_server.url + '/').status == 200
        assert not errors
        chup(page, f'dat-lai-mat-khau-{role}-{width}')
    finally:
        ctx.close()
        staff_ctx.close()
