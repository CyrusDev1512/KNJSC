// Chỉ chạy với pytest/live_server và database test riêng ở cổng 8864.
const {chromium} = require('playwright');
const fs = require('fs');
const assert = require('assert/strict');
const folder = 'storage/destination-prepare';
const base = 'http://127.0.0.1:8864';
const result = {ok: false, cases: [], errors: []};

(async () => {
  const ready = JSON.parse(fs.readFileSync(`${folder}/browser-ready.json`));
  const browser = await chromium.launch({channel: 'chrome', headless: true});
  async function login(context, username) {
    const page = await context.newPage();
    page.on('pageerror', error => result.errors.push(error.message));
    await page.goto(`${base}/dang-nhap/`);
    await page.locator('[name=username]').fill(username);
    await page.locator('[name=password]').fill('matkhau-kiem-thu-1');
    await Promise.all([
      page.waitForURL(url => !url.pathname.includes('dang-nhap')),
      page.locator('button[type=submit]').click(),
    ]);
    return page;
  }
  try {
    for (const width of [1440, 390]) {
      const adminContext = await browser.newContext({viewport: {width, height: 900}});
      const saleContext = await browser.newContext({viewport: {width, height: 900}});
      adminContext.setDefaultTimeout(15000);
      saleContext.setDefaultTimeout(15000);
      const admin = await login(adminContext, 'quan_tri');
      await admin.goto(`${base}/cau-hinh/nhan-don/`);
      const option = admin.locator(`option[value="${ready.destination}"]`);
      assert.equal(await option.isDisabled(), false);
      await admin.locator('[name=table]').selectOption(String(ready.destination));
      await Promise.all([admin.waitForNavigation(), admin.getByRole('button', {name: 'Lưu bảng nhận đơn'}).click()]);
      assert.equal(await admin.locator('[name=table]').inputValue(), String(ready.destination));

      const sale = await login(saleContext, 'staff_sale_1');
      assert.equal((await sale.goto(`${base}/cau-hinh/nhan-don/`)).status(), 403);
      await sale.goto(`${base}/van-don/len-don/`);
      await sale.locator('[name=customer_name]').fill(`Prepare QA ${width}`);
      await sale.locator('[name=phone]').fill(`098000${width}`);
      await sale.locator('[name=market]').selectOption({label: 'Hoa Kỳ'});
      await sale.locator('[name=currency]').selectOption('USD');
      await sale.locator('[name=payment_method]').selectOption({label: 'Thẻ'});
      await sale.locator('[name=product]').selectOption(ready.product);
      await sale.locator('[name=quantity]').fill('2');
      await sale.locator('[name=unit_price]').fill('12.50');
      await sale.getByRole('button', {name: 'Lưu đơn', exact: true}).click();
      await sale.locator('.vd-success').waitFor();
      assert((await sale.locator('.vd-success').innerText()).includes('Vận đơn DB'));

      await admin.locator('[name=table]').selectOption(String(ready.original));
      await Promise.all([admin.waitForNavigation(), admin.getByRole('button', {name: 'Lưu bảng nhận đơn'}).click()]);
      result.cases.push({width, destinationSelectable: true, saleSaved: true, adminOnly: true, switchedBack: true});
      await adminContext.close();
      await saleContext.close();
    }
    assert.equal(result.errors.length, 0);
    result.ok = true;
  } catch (error) {
    result.errors.push(error.message);
    process.exitCode = 1;
  } finally {
    await browser.close();
    fs.writeFileSync(`${folder}/browser-result.json`, JSON.stringify(result, null, 2));
    console.log(JSON.stringify(result));
  }
})();
