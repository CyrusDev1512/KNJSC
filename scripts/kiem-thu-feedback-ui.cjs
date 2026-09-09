/* Chỉ dùng với pytest test_feedback_browser_server trên database test riêng. */
const {chromium} = require('playwright');
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const root = path.resolve(__dirname, '..');
const signal = path.join(root, 'app/.feedback-browser-ready.json');
const result = path.join(root, 'app/.feedback-browser-result.json');
const out = path.join(root, '.agents/design-state/review/feedback');
const base = 'http://127.0.0.1:8031';
const grid = '/bang-tinh/van_don_moi/';
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
  const until = Date.now() + 60000;
  while (!fs.existsSync(signal) && Date.now() < until) await delay(200);
  if (!fs.existsSync(signal)) throw Error('Chưa có pytest live_server; không chạy trên DB local.');
  const fixture = JSON.parse(fs.readFileSync(signal, 'utf8'));
  fs.mkdirSync(out, {recursive:true});
  const browser = await chromium.launch({headless:true, channel:'chrome'});
  const context = await browser.newContext({viewport:{width:1440,height:1000}, locale:'vi-VN'});
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  async function login(user) {
    await page.goto(base + '/dang-nhap/');
    await page.locator('[name=username]').fill(user);
    await page.locator('[name=password]').fill('matkhau-kiem-thu-1');
    await Promise.all([page.waitForURL(url => !url.pathname.includes('dang-nhap')),
      page.locator('button[type=submit]').click()]);
  }
  async function save() {
    await Promise.all([page.waitForNavigation(), page.locator('#vd-assignment-save').click()]);
    await page.locator('#luoi-vd').waitFor();
  }
  async function openRow(id) {
    await page.locator(`#o-${id}-phu_trach_vd`).scrollIntoViewIfNeeded();
    await page.locator(`#o-${id}-phu_trach_vd`).focus();
    await page.keyboard.press('Enter');
    await page.locator('#vd-assignment [name=delivery]').waitFor();
  }
  try {
    await login('vd_leader');
    await page.goto(base + grid);
    await page.locator('#vd-statistics table').waitFor();
    assert.equal(await page.locator('#vd-entry').count(), 0);
    await openRow(fixture.rows[0]);
    await page.locator('#vd-assignment [name=delivery]').selectOption(String(fixture.delivery));
    await page.locator('#vd-assignment [name=care]').selectOption(String(fixture.care));
    await page.screenshot({path:path.join(out,'assignment-desktop.png')});
    await save();
    assert.match(await page.locator(`#o-${fixture.rows[0]}-phu_trach_vd`).innerText(), /staff_vd/);
    // Thao tác chọn vùng có thật qua bàn phím/chuột, sau đó giao hàng loạt.
    const first = page.locator(`#o-${fixture.rows[0]}-ma_don`);
    const second = page.locator(`#o-${fixture.rows[1]}-ma_don`);
    await first.click(); await second.click({modifiers:['Shift']});
    await page.locator('#vd-assign-selected').click();
    await page.locator('#vd-assignment [name=marketing]').waitFor();
    assert.match(await page.locator('#vd-assignment-info').innerText(), /2 dòng/);
    await page.locator('#vd-assignment [name=marketing]').selectOption(String(fixture.marketing));
    await save();
    assert.match(await page.locator(`#o-${fixture.rows[0]}-phu_trach_vd`).innerText(), /staff_vd/);
    // Hai request độc lập: mở phiên bản cũ rồi người khác phân công trước.
    await openRow(fixture.rows[0]);
    const other = await context.request.get(base + '/van-don/phan-cong/?row=' + fixture.rows[0]);
    const snapshot = await other.json();
    const token = await page.locator('#vd-assignment [name=csrfmiddlewaretoken]').inputValue();
    const changed = await context.request.post(base + '/van-don/phan-cong/', {
      headers:{'X-CSRFToken':token, 'Referer':base + grid},
      data:{versions:{[fixture.rows[0]]:snapshot.rows[0].version}, changes:{care:null}}});
    assert.equal(changed.status(), 200);
    await page.locator('#vd-assignment [name=delivery]').selectOption('__clear__');
    await page.locator('#vd-assignment-save').click();
    await page.getByText(/Chưa lưu: Phân công vừa được thay đổi/).waitFor();
    await page.screenshot({path:path.join(out,'assignment-conflict.png')});
    assert(await page.locator('#vd-assignment-save').isDisabled());
    await page.locator('#vd-assignment-reload').click();
    await page.locator('#vd-assignment [name=delivery]').waitFor();
    assert.equal(await page.locator('#vd-assignment [name=delivery]').inputValue(), '__keep__');
    await page.keyboard.press('Escape');
    // URL có thể nạp lại; bộ lọc nhanh không làm mất sản phẩm/sắp xếp.
    await page.goto(base + grid + '?sp=feedback-0&sap=ma_don');
    await page.locator('.vd-quick-group').nth(1).locator('summary').click();
    await page.locator('.vd-quick-form input[value="Chưa thanh toán"]').check();
    await Promise.all([page.waitForNavigation(), page.getByRole('button',{name:'Áp dụng lọc',exact:true}).click()]);
    assert.equal(new URL(page.url()).searchParams.get('sp'),'feedback-0');
    assert.equal(new URL(page.url()).searchParams.get('sap'),'ma_don');
    await page.reload();
    assert(await page.locator('.vd-quick-form input[value="Chưa thanh toán"]').isChecked());
    await page.locator('#vd-open-filters').click();
    assert(await page.locator('#tim').isVisible());
    assert(await page.locator('#bt-ben').getByRole('heading',{name:'Marketing',exact:true}).isVisible());
    await page.screenshot({path:path.join(out,'filters-desktop.png')});
    await page.goto(base + grid + '?f_ma_don=NO-MATCH');
    await page.getByText('Chưa có vận đơn khớp bộ lọc',{exact:true}).waitFor();
    await page.screenshot({path:path.join(out,'empty.png')});
    await page.setViewportSize({width:390,height:844});
    await page.goto(base + grid);
    await openRow(fixture.rows[1]);
    await page.screenshot({path:path.join(out,'assignment-mobile.png')});
    assert(await page.locator('#vd-assignment-save').isVisible());
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),false);
    await page.keyboard.press('Escape');
    await page.screenshot({path:path.join(out,'grid-mobile.png')});
    assert.deepEqual(errors,[]);
    fs.writeFileSync(result, JSON.stringify({ok:true, checks:17}));
    console.log('PASS: 17 nhóm kiểm UI; Chrome desktop/mobile, phân công đơn/lô, xung đột, bộ lọc, URL, rỗng.');
  } catch (error) {
    await page.screenshot({path:path.join(out,'failure.png')}).catch(() => {});
    fs.writeFileSync(result, JSON.stringify({ok:false,error:error.stack}));
    throw error;
  } finally { await browser.close(); }
})().catch(error => {console.error(error);process.exitCode=1;});
