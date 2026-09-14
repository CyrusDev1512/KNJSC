// Chỉ chạy trên DB test riêng. Không ảnh/trace/log chứa mật khẩu tạm.
const { chromium } = require('playwright');
const assert = require('assert/strict');
const fs = require('fs');
const base = 'http://127.0.0.1:8135';
const run = Date.now().toString(36);
const results = [];
async function login(page, username, password) {
  await page.goto(base + '/dang-nhap/');
  await page.locator('[name=username]').fill(username);
  await page.locator('[name=password]').fill(password);
  await Promise.all([page.waitForNavigation(), page.locator('button[type=submit]').click()]);
}
(async () => {
  for(let attempt=0;attempt<30;attempt++) {
    try { if((await fetch(base+'/dang-nhap/')).ok) break; } catch (_) {}
    if(attempt===29) throw new Error('Test server unavailable');
    await new Promise(resolve=>setTimeout(resolve,500));
  }
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  for (const width of [1440, 390]) for (const manual of [false, true]) {
    const username = `identity_${run}_${width}_${Number(manual)}`;
    const errors = [];
    const admin = await browser.newContext({ viewport: { width, height: 900 } });
    const page = await admin.newPage();
    page.on('pageerror', error => errors.push({type:'pageerror',message:error.message.replace(/[A-Za-z0-9_!@#%&*+-]{10,}/g,'[redacted]')}));
    page.on('console', message => { if (message.type() === 'error') errors.push({type:'console',path:message.location().url ? new URL(message.location().url).pathname : ''}); });
    await login(page, 'erp_admin', 'erp-test-only-2026');
    await page.goto(base + '/nhan-su/moi/');
    await page.locator('[name=username]').fill(username);
    await page.locator('[name=email]').fill(username + '@example.test');
    await page.locator('[name=full_name]').fill('Nhân sự thử nghiệm định danh');
    await page.locator('[name=department]').selectOption({ label: 'sale' });
    await page.locator('[name=rank]').selectOption('staff');
    if (manual) await page.locator('[name=password]').fill('BanGiao-2026-Xy!');
    const start = Date.now();
    const [response] = await Promise.all([page.waitForNavigation(), page.getByRole('button', { name: 'Lưu', exact: true }).click()]);
    await page.getByRole('heading', { name: 'Đã tạo nhân sự', exact: true }).waitFor();
    const createMs = Date.now() - start;
    assert(response.headers()['cache-control'].includes('no-store'));
    const temporary = await page.locator('#temporary-password').inputValue();
    assert(temporary.length >= 10);
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    await page.getByRole('link', { name: 'Về danh sách nhân sự' }).click();
    await page.goto(base+'/nhan-su/?tim='+encodeURIComponent(username));
    await page.locator('a[href^="/nhan-su/"][href$="/sua/"]').first().click();
    await page.locator('[name=full_name]').fill('Nhân sự thử nghiệm định danh');
    await Promise.all([page.waitForURL(base+'/nhan-su/'),page.getByRole('button',{name:'Lưu',exact:true}).click()]);
    await page.goto(base + '/nhan-su/moi/');
    assert.equal(await page.locator('#temporary-password').count(), 0);
    await admin.close();

    const staff = await browser.newContext({ viewport: { width, height: 900 }, acceptDownloads: true });
    const userPage = await staff.newPage();
    userPage.on('pageerror', error => errors.push({type:'pageerror',message:error.message.replace(/[A-Za-z0-9_!@#%&*+-]{10,}/g,'[redacted]')}));
    userPage.on('console', message => { if (message.type() === 'error') errors.push({type:'console',path:message.location().url ? new URL(message.location().url).pathname : ''}); });
    await login(userPage, username, temporary);
    assert(new URL(userPage.url()).pathname === '/doi-mat-khau/');
    const nextPassword = 'DaDoi-2026-Zx!';
    await userPage.locator('[name=old_password]').fill(temporary);
    await userPage.locator('[name=new_password1]').fill(nextPassword);
    await userPage.locator('[name=new_password2]').fill(nextPassword);
    await Promise.all([userPage.waitForURL(base + '/'), userPage.locator('button[type=submit]').click()]);
    const day = '2039-06-10';
    await userPage.goto(base + `/bao-cao/?bieu_mau=bc_sale_ngay&ngay=${day}`);
    assert.equal(await userPage.locator('#o-sale_sale').inputValue(), username);
    for (const [name, value] of Object.entries({ ngay: day, so_mess: '100', so_don: '5', doanh_so: '1000' })) {
      await userPage.locator(`[name=sale_${name}]`).fill(value);
    }
    await userPage.locator('[name=sale_san_pham]').selectOption({ label: 'ERP product 0' });
    await userPage.locator('[name=sale_thi_truong]').selectOption({ label: 'Canada' });
    await Promise.all([userPage.waitForURL('**/bao-cao/lich-su/'), userPage.getByRole('button', { name: 'Nộp báo cáo', exact: true }).click()]);
    const filterTimes = [];
    for (const term of [username.toUpperCase(), 'Nhân sự thử nghiệm']) {
      await userPage.locator('#tim').fill(term);
      const begin = Date.now();
      await Promise.all([userPage.waitForNavigation(), userPage.getByRole('button', { name: 'Lọc', exact: true }).click()]);
      filterTimes.push(Date.now() - begin);
      assert.equal(await userPage.locator(`[data-employee-code="${username}"]`).count(), 1);
    }
    const detailHref = await userPage.getByRole('link', { name: 'Xem', exact: true }).first().getAttribute('href');
    await userPage.goto(base + detailHref);
    assert.equal(await userPage.locator(`[data-employee-code="${username}"]`).count(), 1);
    await userPage.goto(base + `/bao-cao/tong-hop/?nguon=bao_cao_sale&tu=${day}&den=${day}`);
    const downloadEvent = userPage.waitForEvent('download');
    await userPage.getByRole('link', { name: 'Xuất Excel', exact: true }).click();
    assert.equal(await (await downloadEvent).failure(), null);
    assert.equal((await staff.request.get(base + '/nhan-su/moi/')).status(), 403);
    await staff.close();
    const check = await browser.newContext();
    const checkPage = await check.newPage();
    await login(checkPage, username, temporary);
    assert.equal(new URL(checkPage.url()).pathname, '/dang-nhap/');
    await login(checkPage, username, nextPassword);
    assert.equal(new URL(checkPage.url()).pathname, '/');
    await check.close();
    if(errors.length) console.error(JSON.stringify(errors));
    assert.equal(errors.length, 0);
    results.push({ width, manual, username, createMs, filterTimes, passed: true });
  }
  await browser.close();
  fs.writeFileSync('storage/erp-verification/identity-browser.json', JSON.stringify(results, null, 2));
  console.log(JSON.stringify({ passed: results.length, results }));
})().catch(error => {
  console.error('Identity E2E failed:', error.name);
  console.error((error.stack||'').split('\n').filter(line=>line.trim().startsWith('at ')).join('\n'));
  process.exit(1);
});
