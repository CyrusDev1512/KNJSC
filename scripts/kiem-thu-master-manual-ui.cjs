const {chromium}=require('playwright'),assert=require('assert/strict'),fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..'),base='http://127.0.0.1:8031',signal=path.join(root,'app/.master-browser-ready.json'),result=path.join(root,'app/.master-browser-result.json');
(async()=>{for(let i=0;i<120&&!fs.existsSync(signal);i++)await new Promise(r=>setTimeout(r,500));assert(fs.existsSync(signal));const browser=await chromium.launch({channel:'chrome',headless:true}),context=await browser.newContext({viewport:{width:1440,height:900},permissions:['clipboard-read','clipboard-write']}),page=await context.newPage(),errors=[];let writes=0;page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.url().includes('/luu-json/')&&r.method()==='POST')writes++;});
const grid=base+'/bang-tinh/van_don_moi/?f_ma_don=MASTER-00000',cell=()=>page.locator('.mg-cell[data-code="bang"][data-r="0"]');
const open=async()=>{await page.goto(grid);await cell().waitFor();};
try{await page.goto(base+'/dang-nhap/');await page.locator('[name=username]').fill('quan_tri');await page.locator('[name=password]').fill('matkhau-kiem-thu-1');await Promise.all([page.waitForURL(u=>!u.pathname.includes('dang-nhap')),page.locator('button[type=submit]').click()]);await open();
await cell().dblclick({delay:120});await page.locator('#mg-editor input').fill('Manual-001');await page.keyboard.press('Enter');await page.waitForTimeout(250);
assert.equal(writes,0,'Enter không được ghi database trước khi bấm Lưu');
assert.equal(await cell().textContent(),'Manual-001');
await page.locator('#mg-columns-button').click();await page.getByRole('button',{name:'Đóng cột hiển thị',exact:true}).click();
assert.equal(await cell().textContent(),'Manual-001');
await page.keyboard.press('Control+s');await page.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đã lưu');assert.equal(writes,1);
await open();assert.equal(await cell().textContent(),'Manual-001');
// Bản đang làm đi qua popup, không tự lưu, không yêu cầu lưu.
const edit=async value=>{await cell().dblclick({delay:120});await page.locator('#mg-editor input').fill(value);};
await edit('Manual-002');await page.locator('#mg-columns-button').click();assert.equal(writes,1);
await page.locator('#mg-column-list').evaluate(e=>e.scrollTop=e.scrollHeight);
const close=page.getByRole('button',{name:'Đóng cột hiển thị',exact:true}),cb=await close.boundingBox();assert(cb.y>=0&&cb.y+cb.height<=900);await close.click();
await page.locator('#mg-filters-button').click();await page.getByRole('button',{name:'Đóng bộ lọc',exact:true}).click();
await page.locator('[data-filter="bang"]').click();await page.locator('#mg-column-filter-body input[name=q]').waitFor();
await page.waitForFunction(()=>!document.querySelector('#mg-column-filter-body.htmx-settling'));
await Promise.all([page.waitForResponse(r=>r.url().includes('/loc/bang/')&&r.url().includes('q=Manual')),page.locator('#mg-column-filter-body input[name=q]').pressSequentially('Manual')]);
await page.getByRole('button',{name:'Đóng lọc cột',exact:true}).click();assert.equal(await cell().textContent(),'Manual-002');
await page.locator('#mg-more-button').click();assert(await page.getByRole('button',{name:/Chia sẻ link/}).isDisabled());await page.locator('#mg-more summary').click();assert(await page.getByRole('link',{name:'Tải Excel',exact:true}).isVisible());
await page.locator('#mg-assign').click();await page.getByRole('button',{name:'Đóng phân công',exact:true}).click();assert.equal(writes,1);
await page.locator('.mg-cell[data-code="san_pham"][data-r="0"]').dblclick({delay:120});await page.locator('#vd-detail-body form').waitFor();await page.getByRole('button',{name:'Đóng chi tiết sản phẩm',exact:true}).click();assert.equal(writes,1);
await page.locator('#mg-undo').click();await page.waitForFunction(()=>document.querySelector('.mg-cell[data-code="bang"]').textContent==='Manual-001');
await page.locator('#mg-redo').click();await page.waitForFunction(()=>document.querySelector('.mg-cell[data-code="bang"]').textContent==='Manual-002');
// Lọc không khớp dòng đang sửa: Save vẫn lưu các ô đang chờ ngoài kết quả lọc.
await page.locator('#mg-search input').fill('khong-co-khach-nay');await page.locator('#mg-search button').click();await page.waitForFunction(()=>document.getElementById('mg-count').textContent.startsWith('0 dòng'));
await page.locator('#mg-more-button').click();await page.locator('#mg-save').click();await page.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đã lưu');assert.equal(writes,2);
await open();assert.equal(await cell().textContent(),'Manual-002');
// Tải lại bỏ bản chưa lưu, không sinh hộp xác nhận, không ghi nháp vào storage.
page.on('dialog',async d=>{errors.push('Unexpected dialog '+d.type());await d.dismiss();});
await edit('Discard-on-reload');await page.keyboard.press('Enter');await page.reload();await cell().waitFor();assert.equal(await cell().textContent(),'Manual-002');assert.equal(writes,2);
assert(!await page.evaluate(()=>JSON.stringify(localStorage).includes('Discard-on-reload')));
// Mất phản hồi rồi sửa tiếp: replay UUID cũ trước, sau đó lưu phần sửa thêm.
const operations=[],capture=r=>{if(r.url().endsWith('/luu-json/')&&r.method()==='POST')operations.push(JSON.parse(r.postData()).operation);};page.on('request',capture);
await edit('Network-one');await page.keyboard.press('Enter');await page.route('**/luu-json/',async route=>{await route.fetch();await route.abort('failed');await page.unroute('**/luu-json/');});
await page.keyboard.press('Control+s');await page.getByRole('button',{name:'Thử lại',exact:true}).waitFor();assert.equal(await cell().textContent(),'Network-one');
await edit('Network-two');await page.keyboard.press('Enter');await page.keyboard.press('Control+s');await page.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đã lưu');
assert.equal(operations.length,3);assert.equal(operations[0],operations[1]);assert.notEqual(operations[1],operations[2]);page.off('request',capture);
await open();assert.equal(await cell().textContent(),'Network-two');
// Menu và X không bị khuất trên mobile.
await page.setViewportSize({width:390,height:844});await page.locator('#mg-more-button').click();const mb=await page.locator('#mg-more').boundingBox();assert(mb.x>=0&&mb.x+mb.width<=390,'Menu … phải nằm trong màn hình mobile');
await page.keyboard.press('Escape');await page.locator('#mg-columns-button').click();await page.locator('#mg-column-list').evaluate(e=>e.scrollTop=e.scrollHeight);const mx=await close.boundingBox();assert(mx.y>=0&&mx.y+mx.height<=844);await page.screenshot({path:path.join(root,'.agents/design-state/review/master/manual-columns-mobile.png')});await close.click();
await page.setViewportSize({width:1440,height:900});await page.locator('#mg-more-button').click();await page.screenshot({path:path.join(root,'.agents/design-state/review/master/manual-menu.png')});
assert.deepEqual(errors,[]);fs.writeFileSync(result,JSON.stringify({ok:true}));console.log('PASS manual save smoke');
}catch(e){fs.writeFileSync(result,JSON.stringify({ok:false,error:e.stack,errors}));throw e;}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
