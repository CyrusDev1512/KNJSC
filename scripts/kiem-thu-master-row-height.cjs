/* Hồi quy chiều cao hàng; chỉ gọi trong fixture Chrome dùng DB test. */
const assert=require('assert/strict');
module.exports=async function rowHeightChecks({page,context,base}){
  const grid=base+'/bang-tinh/van_don_moi/?sap=ma_don';
  const open=async(url=grid)=>{await page.goto(url);await page.locator('.mg-cell[data-id]').first().waitFor();};
  const row=r=>page.locator(`.mg-row[aria-rowindex="${r+2}"]`);
  const handle=r=>page.locator(`[data-row-resize="${r}"]`);
  const height=async r=>{await page.evaluate(()=>new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(done))));return row(r).evaluate(e=>e.getBoundingClientRect().height);};
  const drag=async(r,delta,{cancel=false}={})=>{
    const b=await handle(r).boundingBox();await page.mouse.move(b.x+20,b.y+b.height/2);await page.mouse.down();
    await page.mouse.move(b.x+20,b.y+b.height/2+delta,{steps:10});
    if(cancel)await page.keyboard.press('Escape');await page.mouse.up();await page.waitForTimeout(80);
  };
  await page.setViewportSize({width:1440,height:900});await open();
  assert(await handle(0).count(),'Phải có tay kéo chiều cao ở số hàng');
  const id=await page.locator('.mg-cell[data-r="0"]').first().getAttribute('data-id');
  const firstCode=await page.locator('.mg-cell[data-r="0"][data-code="ma_don"]').textContent();
  const firstY=(await row(0).boundingBox()).y;assert.equal(await height(0),28);
  await drag(0,132);assert.equal(await height(0),160);
  const geometry=await row(0).evaluate(e=>({y:e.getBoundingClientRect().y,bottom:e.getBoundingClientRect().bottom,heights:[...e.querySelectorAll('.mg-cell,.mg-number')].map(c=>c.getBoundingClientRect().height)}));
  assert.equal(geometry.y,firstY);assert(geometry.heights.every(h=>h===160));assert.equal((await row(1).boundingBox()).y,geometry.bottom);
  await drag(0,60,{cancel:true});assert.equal(await height(0),160);
  await handle(0).focus();await page.keyboard.press('ArrowDown');assert.equal(await height(0),164);
  await page.keyboard.press('ArrowUp');assert.equal(await height(0),160);
  await drag(0,700);assert.equal(await height(0),400);
  await drag(0,-700);assert.equal(await height(0),28);await drag(0,132);
  await open();assert.equal(await height(0),160);
  const stored=await page.evaluate(()=>{const c=JSON.parse(document.getElementById('mg-config').textContent);return JSON.parse(localStorage.getItem(`kn-master:${c.user}:${c.table}`));});
  assert.equal(stored.rowHeights[id],160);assert(Object.entries(stored.rowHeights).every(([id,h])=>/^\d+$/.test(id)&&typeof h==='number'));
  // Cùng ID ở vị trí khác sau lọc; vị trí cũ không được truyền chiều cao.
  await open(base+'/bang-tinh/van_don_moi/?f_ma_don=MASTER-00001');assert.equal(await height(0),28);
  await open(base+'/bang-tinh/van_don_moi/?f_ma_don='+encodeURIComponent(firstCode));assert.equal(await height(0),160);
  await open(grid+'&chieu=giam');assert.equal(await height(0),28);
  const last=(await page.evaluate(()=>window.KNJSC_MASTER.diagnostics())).total-1;
  await page.locator('#mg-viewport').focus();await page.keyboard.press('Control+End');await page.locator(`.mg-cell[data-r="${last}"][data-id]`).first().waitFor();
  assert.equal(await page.locator(`.mg-cell[data-r="${last}"]`).first().getAttribute('data-id'),id);assert.equal(await height(last),160);
  // Chữ dài xuống dòng và còn cắt dọc vẫn mở vùng đọc.
  await open(base+'/bang-tinh/van_don_moi/?f_ma_don=MASTER-00001');await drag(0,92);
  await page.locator('#mg-viewport').evaluate(e=>e.scrollLeft=3000);
  const note=page.locator('.mg-cell[data-code="ghi_chu"][data-r="0"]');await note.waitFor();
  assert.equal(await note.evaluate(e=>getComputedStyle(e).whiteSpace),'pre-wrap');await note.click();await page.locator('#mg-reader').waitFor();await page.screenshot({path:require('path').resolve(__dirname,'../.agents/design-state/review/master/row-height-reader.png')});
  await page.keyboard.press('Escape');await note.dblclick({delay:120});await page.locator('#mg-editor textarea').waitFor();
  await page.locator('#mg-cancel').click();
  await page.locator('#mg-viewport').evaluate(e=>e.scrollLeft=0);
  await handle(0).focus();await page.keyboard.press('Home');assert.equal(await height(0),28);
  // Chiều cao không mất khi dữ liệu khối bị loại khỏi LRU.
  await open();for(let n=1;n<=12;n++){await page.locator('#mg-viewport').evaluate((e,n)=>e.scrollTop=n*2800,n);await page.locator(`.mg-cell[data-r="${n*100}"][data-id]`).first().waitFor();}
  assert((await page.evaluate(()=>window.KNJSC_MASTER.diagnostics())).cache<=10);
  await page.locator('#mg-viewport').evaluate(e=>e.scrollTop=0);await page.locator('.mg-cell[data-r="0"][data-id]').first().waitFor();assert.equal(await height(0),160);
  // Poll đổi phiên bản: giữ đúng hàng và chiều cao khi dựng lại cache.
  const refreshed=page.waitForResponse(r=>r.url().includes('/du-lieu/')&&r.status()===200,{timeout:18000});
  await page.route('**/moi-nhat/',async route=>{const response=await route.fetch();await route.fulfill({response,json:{...await response.json(),rowHeightCheck:1}});});
  await refreshed;await page.locator('.mg-cell[data-r="0"][data-id]').first().waitFor();assert.equal(await height(0),160);await page.unroute('**/moi-nhat/');
  // Zoom: khoảng kéo màn hình được đổi về px CSS.
  await page.evaluate(()=>document.documentElement.style.zoom='1.25');await drag(0,50);
  assert(Math.abs(await height(0)-250)<2);await page.evaluate(()=>document.documentElement.style.zoom='');assert.equal(await height(0),200);
  await handle(0).focus();await page.keyboard.press('Home');assert.equal(await height(0),28);
  // Hàng cao với điều hướng, vùng chọn và lưu/undo dữ liệu trên fixture.
  await drag(0,132);await drag(1,92);
  await page.locator('.mg-cell[data-r="0"][data-code="bang"]').click();await page.keyboard.press('Shift+ArrowDown');
  await page.keyboard.press('Control+c');await page.getByText('Đã sao chép 2 ô.',{exact:true}).waitFor();assert.equal((await page.evaluate(()=>navigator.clipboard.readText())).split('\r\n').length,2);
  await page.keyboard.press('PageDown');await page.waitForFunction(()=>Number(document.querySelector('.mg-current')?.dataset.r)>1);const paged=await page.locator('.mg-current').getAttribute('data-r');assert(Number(paged)>1);
  await page.keyboard.press('Control+Home');await page.locator('.mg-cell[data-r="0"][data-code="bang"]').click();
  await page.evaluate(()=>navigator.clipboard.writeText('00120'));await page.keyboard.press('Control+v');
  await page.keyboard.press('Control+s');await page.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đã lưu');await page.locator('.mg-cell[data-r="0"][data-id]').first().waitFor();
  assert.equal(await height(0),160);await page.locator('.mg-cell[data-r="0"][data-code="bang"]').click();await page.keyboard.press('Delete');
  await page.keyboard.press('Control+s');await page.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đã lưu');await page.locator('#mg-undo:not([disabled])').click();
  await page.keyboard.press('Control+s');await page.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đã lưu');await page.locator('.mg-cell[data-code="bang"][data-r="0"]').filter({hasText:'00120'}).waitFor();
  // Mở ô chưa đổi không chặn kéo hàng trong chế độ lưu thủ công.
  await page.locator('.mg-cell[data-code="bang"][data-r="0"]').dblclick({delay:120});await page.locator('#mg-editor').waitFor();
  await drag(0,40);assert.equal(await height(0),200);assert(!await page.locator('#mg-editor').isVisible());await handle(0).focus();await page.keyboard.press('Home');await height(0);await drag(0,132);
  // Pointer bị hủy/mất focus không lưu lượt kéo dở.
  for(const event of ['blur','pointercancel']){
    const b=await handle(0).boundingBox();await page.mouse.move(b.x+20,b.y+3);await page.mouse.down();await page.mouse.move(b.x+20,b.y+50,{steps:4});
    await page.evaluate(event=>{if(event==='blur')window.dispatchEvent(new Event('blur'));else document.dispatchEvent(new PointerEvent('pointercancel',{bubbles:true}));},event);
    await page.mouse.up();assert.equal(await height(0),160);
  }
  // Lỗi localStorage báo đúng; không chặn việc chỉnh trong phiên.
  await page.evaluate(()=>{window.originalStorageSet=Storage.prototype.setItem;Storage.prototype.setItem=function(){throw new DOMException('quota','QuotaExceededError');};});
  await drag(0,20);assert.equal(await height(0),180);assert.match(await page.locator('#mg-message').textContent(),/Không ghi nhớ/);
  await page.evaluate(()=>{Storage.prototype.setItem=window.originalStorageSet;});await open();assert.equal(await height(0),160);
  // Cùng trình duyệt, đổi tài khoản: không kế thừa tùy chọn của admin.
  async function login(name){await context.clearCookies();await page.goto(base+'/dang-nhap/');await page.locator('[name=username]').fill(name);await page.locator('[name=password]').fill('matkhau-kiem-thu-1');await Promise.all([page.waitForURL(u=>!u.pathname.includes('dang-nhap')),page.locator('button[type=submit]').click()]);}
  await login('staff_sale_1');await open();assert.equal(await height(0),28);await login('quan_tri');await open();assert.equal(await height(0),160);
  // Dữ liệu tùy chọn hỏng/không hữu hạn không làm hỏng lưới.
  await page.evaluate(id=>{const c=JSON.parse(document.getElementById('mg-config').textContent),key=`kn-master:${c.user}:${c.table}`,p=JSON.parse(localStorage.getItem(key));p.rowHeights={[id]:999999,bad:'400','2':-20};localStorage.setItem(key,JSON.stringify(p));},id);
  await open();assert.equal(await height(0),400);await handle(0).focus();await page.keyboard.press('Home');assert.equal(await height(0),28);
  for(const width of [1280,390]){
    await page.setViewportSize({width,height:844});await open();await drag(0,60);assert.equal(await height(0),88);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    await handle(0).focus();await page.keyboard.press('Home');assert.equal(await height(0),28);
  }
  const cdp=await context.newCDPSession(page);await cdp.send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:1});
  const b=await handle(0).boundingBox(),touch=(type,x,y)=>cdp.send('Input.dispatchTouchEvent',{type,touchPoints:type==='touchEnd'?[]:[{x,y}]});
  await touch('touchStart',b.x+20,b.y+3);for(let i=1;i<=5;i++){await touch('touchMove',b.x+20,b.y+3+i*12);await page.waitForTimeout(20);}await touch('touchEnd');
  assert.equal(await height(0),88);await page.screenshot({path:require('path').resolve(__dirname,'../.agents/design-state/review/master/row-height-mobile.png')});
  const viewport=await page.locator('#mg-viewport').boundingBox();await touch('touchStart',200,viewport.y+viewport.height-80);
  for(let i=1;i<=6;i++){await touch('touchMove',200,viewport.y+viewport.height-80-i*30);await page.waitForTimeout(20);}await touch('touchEnd');
  await page.waitForFunction(()=>document.getElementById('mg-viewport').scrollTop>0);
  await cdp.send('Emulation.setTouchEmulationEnabled',{enabled:false});
  console.log('PASS row height: pointer, wrap, persistence, filters, cache, zoom');
};
