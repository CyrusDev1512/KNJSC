/* Chạy sau test_master_browser_server.py trên DB test cổng 8035. */
const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const out=path.resolve('.agents/design-state/review/pinned-20260911'),base='http://127.0.0.1:8035';
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true}),context=await browser.newContext({viewport:{width:1440,height:900},permissions:['clipboard-read','clipboard-write']}),page=await context.newPage(),errors=[],checks=[];
 page.on('pageerror',e=>errors.push(e.message));
 try{
  await page.goto(base+'/dang-nhap/');await page.locator('[name=username]').fill('quan_tri');await page.locator('[name=password]').fill('matkhau-kiem-thu-1');
  await Promise.all([page.waitForURL(u=>!u.pathname.includes('dang-nhap')),page.locator('button[type=submit]').click()]);
  await page.goto(base+'/bang-tinh/van_don_moi/?f_ma_don=MASTER-00000');await page.locator('.mg-cell[data-id]').first().waitFor();
  const frames=()=>page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
  const cell=code=>page.locator(`.mg-cell[data-r="0"][data-code="${code}"]`);
  const head=code=>page.locator(`.mg-heading[data-code="${code}"]`);
  const alignment=async()=>assert(await page.evaluate(()=>[...document.querySelectorAll('.mg-row:first-child .mg-cell')].every(c=>{const h=document.querySelector('.mg-heading[data-code="'+c.dataset.code+'"]');return h&&Math.abs(c.getBoundingClientRect().left-h.getBoundingClientRect().left)<1&&Math.abs(c.getBoundingClientRect().width-h.getBoundingClientRect().width)<1;})),'Tiêu đề và dữ liệu phải thẳng cột');
  await page.locator('#mg-viewport').evaluate(e=>e.scrollLeft=620);await frames();await alignment();
  assert(await cell('ten_khach').evaluate(e=>{const r=e.getBoundingClientRect();return document.elementFromPoint(r.x+20,r.y+10)===e;}),'Ô cuộn không được xuyên vùng ghim');
  const grip=head('ten_khach').locator('[data-resize]'),b=await grip.boundingBox(),before=(await cell('ten_khach').boundingBox()).width;
  await page.mouse.move(b.x+4,b.y+15);await page.mouse.down();await page.mouse.move(b.x+64,b.y+15,{steps:8});await page.mouse.up();await frames();
  assert.equal((await cell('ten_khach').boundingBox()).width,before+60);await alignment();checks.push('Kéo rộng cột ghim khi đã cuộn; tiêu đề/ô thẳng nhau, nền che kín');
  await page.locator('#mg-viewport').evaluate(e=>e.scrollLeft=0);await frames();await cell('ma_don').click();await cell('bang').click({modifiers:['Shift']});await frames();
  assert(await page.locator('.mg-selected:not(.mg-pinned)').count());assert(await page.locator('.mg-selected.mg-pinned').count());checks.push('Chọn vùng xuyên ranh giới ghim');
  await cell('ten_khach').dblclick({delay:120});await page.locator('#mg-editor input').waitFor();
  const original=await page.locator('#mg-editor input').inputValue();await page.locator('#mg-editor input').fill('Nháp kiểm ghim');
  await page.locator('#mg-viewport').evaluate(e=>e.scrollLeft=500);await frames();
  const input=await page.locator('#mg-editor').boundingBox(),box=await cell('ten_khach').boundingBox();assert(Math.abs(input.x-box.x)<1);assert.equal(await page.locator('#mg-editor input').inputValue(),'Nháp kiểm ghim');
  await page.keyboard.press('Escape');assert.equal(await cell('ten_khach').textContent(),original);checks.push('Bấm đúp 120ms, input/draft bám ô ghim khi cuộn, Escape hủy');
  await page.locator('#mg-viewport').evaluate(e=>e.scrollLeft=0);await frames();await cell('bang').click();await page.keyboard.press('F2');await page.locator('#mg-editor input').fill('Kiểm ghim');await page.keyboard.press('Tab');await page.keyboard.press('Escape');
  await page.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đã lưu');await page.reload();await cell('bang').waitFor();assert.equal(await cell('bang').textContent(),'Kiểm ghim');checks.push('F2/Tab/autosave, đọc lại sau reload');
  await page.locator('#mg-columns-button').click();const label=page.locator('#mg-column-list label').filter({hasText:'Tên khách'});await label.locator('input').uncheck();await page.keyboard.press('Escape');await frames();assert.equal(await cell('ten_khach').count(),0);await alignment();
  await page.locator('#mg-columns-button').click();await label.locator('input').check();await page.getByRole('button',{name:'↓ Tên khách',exact:true}).click();await page.keyboard.press('Escape');await frames();await alignment();assert.equal(await cell('ten_khach').count(),1);checks.push('Ẩn/hiện/đổi thứ tự cột; một node mỗi ô');
  await page.evaluate(()=>localStorage.clear());
  await require('./kiem-thu-master-row-height.cjs')({page,context,base});checks.push('Hồi quy chiều cao: 28–400, Escape, focus, touch, cache, polling, copy/paste/Delete/Undo, CSS zoom');
  assert.deepEqual(errors,[]);fs.writeFileSync(path.join(out,'ui.json'),JSON.stringify({ok:true,checks,errors},null,2));console.log(checks);
  fs.writeFileSync('app/.master-browser-result.json',JSON.stringify({ok:true}));
 }catch(e){await page.screenshot({path:path.join(out,'ui-failure.png')});fs.writeFileSync(path.join(out,'ui.json'),JSON.stringify({ok:false,checks,errors,error:e.stack},null,2));throw e;}
 finally{await context.close();await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
