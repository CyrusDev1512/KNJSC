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

    assert.equal(await page.locator('.sp-view-actions').isVisible(), true);
    const themeBefore = await page.evaluate(() => document.documentElement.dataset.theme);
    await page.locator('#nut-nen').click();
    assert.notEqual(await page.evaluate(() => document.documentElement.dataset.theme), themeBefore);
    assert.equal(await page.locator('#nut-nen').getAttribute('aria-label'), 'Chuyển sang nền sáng');
    if (width === 1440) await page.locator('#nut-nen').click();

    await page.locator('#sp-erp-fullscreen').click();
    await page.waitForFunction(() => document.documentElement.classList.contains('sp-erp-immersive'));
    assert.equal(
      await page.evaluate(() => Boolean(document.fullscreenElement)),
      false,
      'Mở rộng giao diện ERP không được ẩn thanh địa chỉ và tab trình duyệt',
    );
    const edge = await page.evaluate(() => {
      const app = document.querySelector('body.sp-erp>.app');
      const box = app.getBoundingClientRect();
      const appStyle = getComputedStyle(app);
      return {
        backgroundImage: getComputedStyle(document.body, '::before').content,
        padding: [appStyle.paddingTop, appStyle.paddingRight, appStyle.paddingBottom, appStyle.paddingLeft],
        left: Math.round(box.left), right: Math.round(innerWidth - box.right),
        topRadius: getComputedStyle(document.querySelector('.topbar')).borderRadius,
        contentRadius: getComputedStyle(document.querySelector('.noi-dung')).borderRadius,
      };
    });
    assert.equal(edge.backgroundImage, 'none', 'Toàn màn hình không được để lộ ảnh nền');
    assert.deepEqual(edge.padding, ['0px', '0px', '0px', '0px']);
    assert.equal(edge.left, 0);
    assert.equal(edge.right, 0);
    assert.equal(edge.topRadius, '0px');
    assert.equal(edge.contentRadius, '0px');
    assert.equal(await page.locator('#sp-erp-fullscreen').getAttribute('aria-pressed'), 'true');
    assert.equal(await page.evaluate(() => localStorage.getItem('knjsc-erp-immersive')), '1');
    await page.reload();
    assert.equal(await page.evaluate(() => document.documentElement.classList.contains('sp-erp-immersive')), true);
    assert.equal(await page.locator('#sp-erp-fullscreen').getAttribute('aria-pressed'), 'true');
    assert.equal(await page.evaluate(() => Boolean(document.fullscreenElement)), false);
    await page.screenshot({path:`storage/erp-focus-verification/immersive-${width}.png`, fullPage:true});

    const otherPage = await context.newPage();
    await otherPage.goto('http://localhost:18020/bang/van_don/');
    assert.equal(await otherPage.evaluate(() => document.documentElement.classList.contains('sp-erp-immersive')), true);
    await otherPage.keyboard.press('Escape');
    await page.waitForFunction(() => !document.documentElement.classList.contains('sp-erp-immersive'));
    assert.equal(await page.evaluate(() => localStorage.getItem('knjsc-erp-immersive')), '0');
    await otherPage.close();

    assert.equal(await page.locator('#sp-erp-fullscreen').getAttribute('aria-pressed'), 'false');

    await page.locator('#sp-dock-collapse').click();
    assert.equal(await page.locator('#thanh-ben').isVisible(), false);
    assert.equal(await page.locator('#sp-dock-expand').isVisible(), true);
    await page.reload();
    assert.equal(await page.locator('#thanh-ben').isVisible(), false, 'Dock phải nhớ trạng thái sau reload');
    await page.locator('#sp-dock-expand').click();
    assert.equal(await page.locator('#thanh-ben').isVisible(), true);

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
