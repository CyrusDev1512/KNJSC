/* Kiểm tra trình duyệt trên database Solarpunk cô lập; không dùng dữ liệu vận hành. */
const {chromium} = require('./solarpunk-browser.cjs');
const assert = require('node:assert/strict');
const fs = require('node:fs');

(async () => {
  fs.mkdirSync('storage/erp-focus-verification', {recursive:true});
  const browser = await chromium.launch({channel:'chrome', headless:true});
  const results = [];
  for (const width of [1440, 390]) {
    const context = await browser.newContext({viewport:{width,height:900}});
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    await page.goto('http://localhost:18020/dang-nhap/');
    await page.locator('[name=username]').fill('quantri');
    await page.locator('[name=password]').fill('matkhaucuatoi');
    await Promise.all([
      page.waitForURL(url => !url.pathname.includes('dang-nhap')),
      page.locator('button[type=submit]').click(),
    ]);

    await page.locator('#sp-dock-collapse').click();
    assert.equal(await page.locator('#thanh-ben').isVisible(), false);
    assert.equal(await page.locator('#sp-dock-expand').isVisible(), true);
    await page.reload();
    assert.equal(await page.locator('#thanh-ben').isVisible(), false, 'Dock phải nhớ trạng thái sau reload');
    await page.locator('#sp-dock-expand').click();
    assert.equal(await page.locator('#thanh-ben').isVisible(), true);

    if (width === 390) await page.evaluate(() => localStorage.setItem('knjsc-nen', 'dark'));
    await page.goto('http://localhost:18020/bang/van_don/');
    await page.locator('#erp-focus-enter').click();
    assert.equal(await page.locator('.topbar').isVisible(), false);
    assert.equal(await page.locator('#thanh-ben').isVisible(), false);
    assert.equal(await page.locator('.bang-cuon').isVisible(), true);
    assert.equal(await page.locator('.loc').isVisible(), false);
    if (!await page.locator('#erp-native-fullscreen').isDisabled()) {
      await page.locator('#erp-native-fullscreen').click();
      await page.waitForFunction(() => Boolean(document.fullscreenElement));
      await page.keyboard.press('Escape');
      await page.waitForFunction(() => !document.fullscreenElement);
      assert.equal(await page.locator('.topbar').isVisible(), false, 'Thoát Fullscreen API vẫn giữ Tập trung');
    }
    await page.locator('#erp-focus-tools').click();
    assert.equal(await page.locator('.loc').isVisible(), true);
    await page.screenshot({path:`storage/erp-focus-verification/focus-${width}.png`, fullPage:true});
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('.loc').isVisible(), false, 'Esc đầu đóng Công cụ');
    assert.equal(await page.locator('.topbar').isVisible(), false, 'Esc đầu chưa thoát Tập trung');
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('.topbar').isVisible(), true, 'Esc kế tiếp thoát Tập trung');
    assert.equal(await page.locator('[contenteditable=true], input[data-cell], select[data-cell]').count(), 0,
      'Bảng ERP không được có trình sửa ô');
    results.push({width, errors});
    assert.deepEqual(errors, []);
    await context.close();
  }
  await browser.close();
  console.log(JSON.stringify({passed:results.length, results}));
})().catch(error => { console.error(error); process.exit(1); });
