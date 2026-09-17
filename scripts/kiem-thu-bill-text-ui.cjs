/* Kiểm Bill text trên database Solarpunk cô lập; khôi phục giá trị sau kiểm tra. */
const {chromium} = require('./solarpunk-browser.cjs');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({channel:'chrome', headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:900}});
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
  await page.goto('http://localhost:18021/dang-nhap/');
  await page.locator('[name=username]').fill('quantri');
  await page.locator('[name=password]').fill('matkhaucuatoi');
  await Promise.all([
    page.waitForURL(url => !url.pathname.includes('dang-nhap')),
    page.locator('button[type=submit]').click(),
  ]);
  await page.goto('http://localhost:18021/bang-tinh/van_don_moi/');
  const viewport = page.locator('#mg-viewport');
  let bill;
  for (let left=0; left<=6000; left+=600) {
    await viewport.evaluate((node, value) => { node.scrollLeft = value; }, left);
    await page.waitForTimeout(60);
    const candidate = page.locator('.mg-cell[data-code="bill"]').first();
    if (await candidate.count()) { bill = candidate; break; }
  }
  assert.ok(bill, 'Phải tìm thấy cột Bill');
  const original = await bill.innerText();
  async function change(value) {
    const box = await bill.boundingBox();
    await page.mouse.click(box.x + 3, box.y + box.height - 3);
    await viewport.focus();
    await page.keyboard.press('F2');
    await page.locator('#mg-input input, #mg-input textarea').fill(value);
    await page.keyboard.press('Enter');
    await page.keyboard.press('Control+s');
    await page.getByText('Đã lưu', {exact:true}).waitFor();
  }
  await change('javascript:alert(1)');
  assert.equal(await bill.locator('a').count(), 0, 'Giao thức nguy hiểm chỉ được hiển thị như chữ');
  await change('https://example.com/bill-test');
  const link = bill.locator('a.mg-url-link');
  assert.equal(await link.count(), 1);
  assert.equal(await link.getAttribute('target'), '_blank');
  assert.match(await link.getAttribute('rel'), /noopener/);
  await page.keyboard.press('Control+z');
  await page.waitForFunction(() => document.querySelector('.mg-cell[data-code="bill"]')?.textContent === 'javascript:alert(1)');
  assert.equal(await bill.locator('a').count(), 0, 'Undo phải trả lại text nguy hiểm mà không tạo link');
  await page.keyboard.press('Control+z');
  const restored = original === '—' ? '' : original;
  await page.waitForFunction(value => document.querySelector('.mg-cell[data-code="bill"]')?.textContent === value, restored);
  assert.deepEqual(errors, []);
  await browser.close();
  console.log(JSON.stringify({passed:true}));
})().catch(error => { console.error(error); process.exit(1); });
