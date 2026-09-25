// Chỉ chạy với fixture ACCOUNT_BROWSER trong PostgreSQL test riêng; không ghi mật khẩu/cookie ra bằng chứng.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const folder = process.env.ACCOUNT_EVIDENCE;
if (!folder) throw new Error('Thiếu ACCOUNT_EVIDENCE của fixture test');
const ready = JSON.parse(fs.readFileSync(path.join(folder, 'account-browser-ready.json')));
const erp = 'http://erp.accounts.test:18047';
const crm = 'http://crm.accounts.test:18047';
const initial = 'matkhau-kiem-thu-1';
const reset = 'Browser-Reset-Only-2026!';
const changed = 'Browser-Changed-Only-2026!';
const result = {ok: false, cases: [], errors: []};

async function login(page, username, password=initial) {
  await page.goto(erp + '/dang-nhap/');
  await page.locator('[name=username]').fill(username);
  await page.locator('[name=password]').fill(password);
  await Promise.all([page.waitForURL(url => !url.pathname.startsWith('/dang-nhap')),
    page.locator('button[type=submit]').click()]);
}

(async () => {
  const browser = await chromium.launch({channel: 'chrome', headless: true,
    args: ['--host-resolver-rules=MAP erp.accounts.test 127.0.0.1, MAP crm.accounts.test 127.0.0.1', '--no-proxy-server']});
  try {
    for (const item of ready.cases) {
      const options = {viewport: {width:item.width, height:900}, locale:'vi-VN'};
      const manager = await browser.newContext(options);
      const employee = await browser.newContext(options);
      const page = await manager.newPage();
      const victim = await employee.newPage();
      const crmTab = await employee.newPage();
      const jsErrors = [];
      page.on('pageerror', error => jsErrors.push(error.message));
      const start = Date.now();
      await login(victim, item.target);
      await crmTab.goto(crm + '/thu-muc/');
      assert(!crmTab.url().includes('/dang-nhap/'));
      await login(page, item.actor);
      await page.goto(erp + '/nhan-su/');
      await page.locator(`a[href='/nhan-su/${item.pk}/sua/']`).click();
      assert.equal(await page.locator('[name=rank]').count(), item.role === 'admin' ? 1 : 0);
      await page.locator('[name=new_password1]').fill(reset);
      await page.locator('[name=new_password2]').fill('Different-Confirmation!');
      await page.getByRole('button', {name:'Đặt lại mật khẩu', exact:true}).click();
      assert.equal(await page.locator('[name=new_password1]').inputValue(), '');
      assert(await page.locator('.errorlist').count() > 0);
      await page.locator('[name=new_password1]').fill(reset);
      await page.locator('[name=new_password2]').fill(reset);
      await page.getByRole('button', {name:'Đặt lại mật khẩu', exact:true}).click();
      await page.getByText('Đã đặt lại mật khẩu.', {exact:false}).waitFor();
      await victim.reload();
      assert(victim.url().includes('/dang-nhap/'));
      await crmTab.reload();
      assert(crmTab.url().includes('/dang-nhap/'));
      await login(victim, item.target, reset);
      assert(victim.url().includes('/doi-mat-khau/'));
      await victim.locator('[name=old_password]').fill(reset);
      await victim.locator('[name=new_password1]').fill(changed);
      await victim.locator('[name=new_password2]').fill(changed);
      await Promise.all([victim.waitForURL(url => !url.pathname.startsWith('/doi-mat-khau')),
        victim.locator('button[type=submit]').click()]);
      await page.goto(erp + '/nhan-su/');
      await page.locator(`a[href='/nhan-su/${item.pk}/xoa/']`).click();
      await page.getByRole('link', {name:'Hủy',exact:true}).click();
      await page.locator(`a[href='/nhan-su/${item.pk}/xoa/']`).click();
      await page.screenshot({path:path.join(folder, `account-confirm-${item.role}-${item.width}.png`), fullPage:true});
      await page.locator('[name=confirm]').check();
      await page.getByRole('button', {name:'Xác nhận xóa',exact:true}).click();
      assert.equal(await page.locator(`a[href='/nhan-su/${item.pk}/sua/']`).count(), 0);
      await victim.reload();
      assert(victim.url().includes('/dang-nhap/'));
      if (item.role !== 'admin') {
        const denied = await page.goto(`${erp}/nhan-su/${ready.admin_pk}/sua/`);
        assert.equal(denied.status(), 403);
      }
      assert.deepEqual(jsErrors, []);
      result.cases.push({role:item.role, width:item.width, passed:true, elapsed_ms:Date.now()-start});
      await manager.close();
      await employee.close();
    }
    const ctx = await browser.newContext();
    const staff = await ctx.newPage();
    await login(staff, ready.staff);
    assert.equal((await staff.goto(erp + '/nhan-su/')).status(), 403);
    assert.equal((await staff.goto(`${erp}/nhan-su/${ready.admin_pk}/sua/`)).status(), 403);
    await ctx.close();
    result.ok = true;
  } catch (error) {
    result.errors.push(error.message.replaceAll(initial, '[redacted]').replaceAll(reset, '[redacted]').replaceAll(changed, '[redacted]'));
    process.exitCode = 1;
  } finally {
    await browser.close();
    fs.writeFileSync(path.join(folder, 'account-browser-result.json'), JSON.stringify(result,null,2));
    console.log(JSON.stringify(result));
  }
})();
