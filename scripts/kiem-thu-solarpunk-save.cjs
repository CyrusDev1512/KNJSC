/* Ghi và khôi phục trên 120 đơn tổng hợp của preview riêng. */
const {chromium}=require('./solarpunk-browser.cjs');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:900}});
 await page.goto('http://localhost:18021/dang-nhap/');
 await page.locator('[name=username]').fill('quantri');await page.locator('[name=password]').fill('matkhaucuatoi');
 await Promise.all([page.waitForURL(u=>!u.pathname.includes('dang-nhap')),page.locator('button[type=submit]').click()]);
 await page.goto('http://localhost:18021/bang-tinh/van_don/');
 const cell=page.locator('.mg-cell[data-code="ten_khach"]').first();await cell.waitFor();
 const original=await cell.innerText();assert.ok(original.startsWith('Khách mẫu Solarpunk'));
 await cell.click();
 let pending;
 await page.route('**/luu-json/',route=>{pending=route});
 await cell.dblclick();await page.locator('#mg-input input').fill(original+' kiểm lưu');await page.keyboard.press('Enter');
 await page.waitForFunction(()=>document.querySelector('#bt-trang-thai').textContent==='Đang lưu');
 await page.locator('#bt-toan-man-nut').click();
 assert.equal(await page.locator('#sp-focus-status-slot #bt-trang-thai').innerText(),'Đang lưu');
 await page.locator('#sp-focus-exit').click();
 await page.locator('#bt-toan-man-nut').click();
 await pending.continue();await page.unroute('**/luu-json/');
 await page.waitForFunction(()=>document.querySelector('#bt-trang-thai').textContent==='Đã lưu');
 await page.locator('#mg-viewport').focus();await page.keyboard.press('Control+z');
 await page.waitForFunction(()=>document.querySelector('#bt-trang-thai').textContent==='Đã lưu');
 assert.equal(await cell.innerText(),original,'Undo survives focus transition and pending save');
 // Mạng lỗi: nháp ở RAM, báo lỗi vẫn nằm trong viewport tập trung.
 await page.route('**/luu-json/',r=>r.abort('failed'));
 await cell.dblclick();await page.locator('#mg-input input').fill(original+' thử mạng');await page.keyboard.press('Enter');
 await page.waitForFunction(()=>document.querySelector('#mg-message').classList.contains('mg-error'));
 assert.equal(await page.locator('#mg-message').isVisible(),true);
 await page.unroute('**/luu-json/');
 await page.locator('#mg-viewport').focus();await page.keyboard.press('Control+s');
 await page.waitForFunction(()=>document.querySelector('#bt-trang-thai').textContent==='Đã lưu');
 await page.keyboard.press('Control+z');
 await page.waitForFunction(()=>document.querySelector('#bt-trang-thai').textContent==='Đã lưu');
 assert.equal(await cell.innerText(),original);
 // Dán vùng 2 dòng qua cùng handler clipboard, rồi hoàn tác cả vùng.
 await cell.click();
 await page.locator('#mg-viewport').evaluate(el=>{const data=new DataTransfer();data.setData('text/plain','Khách mẫu Solarpunk dán 1\nKhách mẫu Solarpunk dán 2');el.dispatchEvent(new ClipboardEvent('paste',{clipboardData:data,bubbles:true,cancelable:true}));});
 await page.waitForFunction(()=>document.querySelector('.mg-cell[data-code="ten_khach"]').textContent.includes('dán 1'));
 await page.waitForFunction(()=>document.querySelector('#bt-trang-thai').textContent==='Đã lưu');
 await page.locator('#mg-viewport').focus();await page.keyboard.press('Control+z');
 await page.waitForFunction(()=>document.querySelector('#bt-trang-thai').textContent==='Đã lưu');
 assert.equal(await cell.innerText(),original);
 await browser.close();console.log('PASS: pending save, focus transitions, undo, network failure/retry, paste 2 rows/undo');
})().catch(e=>{console.error(e);process.exit(1)});
