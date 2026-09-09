/* Kiểm đọc giao diện trên máy local; không tạo hoặc sửa đơn trong DB thật. */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({headless: true, channel: 'chrome'});
  const context = await browser.newContext({viewport: {width: 1440, height: 1000}, locale: 'vi-VN'});
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const base = process.env.KN_CRM_URL || 'http://127.0.0.1:8021';
  const out = path.resolve(__dirname, '../.impeccable/review');
  fs.mkdirSync(out, {recursive: true});
  try {
    await page.goto(base + '/dang-nhap/');
    await page.locator('[name=username]').fill(process.env.KN_TEST_USER || 'quantri');
    await page.locator('[name=password]').fill(process.env.KN_TEST_PASSWORD || 'matkhaucuatoi');
    await page.locator('button[type=submit]').click();
    await page.waitForURL(url => !url.pathname.includes('dang-nhap'));
    await page.goto(base + '/bang-tinh/van_don_moi/');
    await page.locator('#vd-entry form').waitFor();
    await page.locator('#vd-statistics table').waitFor();
    await page.getByRole('button', {name: 'Thêm sản phẩm', exact: true}).click();
    if (await page.locator('.vd-items tbody tr').count() !== 2) throw Error('Không thêm được sản phẩm');
    await page.locator('.vd-items tbody tr').last().getByRole('button', {name: 'Bỏ dòng'}).click();
    for (const [name, width, height] of [['desktop',1440,1000], ['mobile',390,844]]) {
      await page.setViewportSize({width, height});
      await page.locator('#vd-page').evaluate(el => {el.scrollTop = 0;});
      await page.screenshot({path: path.join(out, name + '.png')});
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
      if (overflow) throw Error(name + ': tràn ngang toàn trang');
      await page.locator('#vd-page').evaluate(el => {el.scrollTop = el.scrollHeight;});
      await page.screenshot({path: path.join(out, name + '-statistics.png')});
      await page.locator('#luoi-vd').evaluate(el => {
        const target = el.querySelector('.bt-hang-chu [data-cot="trang_thai_vc"]');
        el.scrollLeft = target ? target.offsetLeft : el.scrollWidth;
      });
      if (!(await page.locator('#luoi-vd').evaluate(el => el.scrollLeft > 0))) throw Error('Lưới không cuộn ngang');
      await page.waitForTimeout(150);
      const groupVisible = await page.locator('#luoi-vd').evaluate(el => {
        const box = el.getBoundingClientRect();
        return [...el.querySelectorAll('.vd-group-header span')].some(label => {
          const r = label.getBoundingClientRect();
          return label.textContent.trim() && r.right > box.left && r.left < box.right;
        });
      });
      if (!groupVisible) {
        const geometry = await page.locator('#luoi-vd').evaluate(el => ({scrollLeft: el.scrollLeft,
          viewport: el.getBoundingClientRect().toJSON(), groups: [...el.querySelectorAll('.vd-group-header span')].map(label => ({text: label.textContent, box: label.getBoundingClientRect().toJSON(), transform: label.style.transform}))}));
        throw Error(name + ': tên nhóm cột biến mất khi cuộn ngang ' + JSON.stringify(geometry));
      }
      const emptyVisible = await page.locator('#luoi-vd').evaluate(el => {
        const empty = el.querySelector('.vd-empty-cell .rong');
        if (!empty) return true;
        const box = el.getBoundingClientRect();
        const r = empty.getBoundingClientRect();
        return r.right > box.left && r.left < box.right && r.bottom > box.top && r.top < box.bottom;
      });
      if (!emptyVisible) {
        const geometry = await page.locator('#luoi-vd').evaluate(el => ({scrollLeft: el.scrollLeft,
          viewport: el.getBoundingClientRect().toJSON(), empty: el.querySelector('.vd-empty-cell .rong').getBoundingClientRect().toJSON(),
          transform: el.querySelector('.vd-empty-cell .rong').style.transform}));
        throw Error(name + ': empty state hidden after horizontal scroll ' + JSON.stringify(geometry));
      }
      await page.screenshot({path: path.join(out, name + '-grid-right.png')});
      await page.locator('#luoi-vd').evaluate(el => {el.scrollLeft = 0;});
    }
    if (errors.length) throw Error(errors.join('\n'));
    console.log('ĐẠT: ba khu, thêm/bỏ dòng sản phẩm, máy tính 1440px, điện thoại 390px, cuộn ngang; không có lỗi JavaScript.');
  } finally { await browser.close(); }
})().catch(error => {console.error(error); process.exitCode = 1;});
