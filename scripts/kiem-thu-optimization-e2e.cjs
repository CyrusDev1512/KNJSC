/* E2E/UI chỉ chạy với fixture pytest, không đăng nhập database đang dùng. */
const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),base='http://127.0.0.1:8035',out=path.join(root,'.agents/design-state/review/optimization/e2e');
const signal=path.join(root,'app/.master-browser-ready.json'),result=path.join(root,'app/.master-browser-result.json');
const pause=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
  for(let i=0;i<100&&!fs.existsSync(signal);i++)await pause(200);
  assert(fs.existsSync(signal),'Cần fixture DB test');fs.mkdirSync(out,{recursive:true});
  const browser=await chromium.launch({channel:'chrome',headless:true});
  const context=await browser.newContext({viewport:{width:1440,height:900},permissions:['clipboard-read','clipboard-write']});
  const page=await context.newPage(),errors=[],evidence={checks:[]};page.on('pageerror',e=>errors.push(e.message));
  async function open(){await page.goto(base+'/bang-tinh/van_don_moi/?f_ma_don=MASTER-00000');await page.locator('.mg-cell[data-id]').first().waitFor();}
  async function cell(code){
    await page.evaluate(async code=>{const config=JSON.parse(document.getElementById('mg-config').textContent),data=await fetch(config.dataUrl+location.search).then(r=>r.json());document.getElementById('mg-viewport').scrollLeft=Math.max(0,data.columns.findIndex(c=>c.code===code)*160-520);},code);
    const locator=page.locator(`.mg-cell[data-r="0"][data-code="${code}"]`);await locator.waitFor();return locator;
  }
  const saved=()=>page.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đã lưu');
  const read=()=>page.evaluate(async()=>{const c=JSON.parse(document.getElementById('mg-config').textContent);return (await fetch(c.dataUrl+location.search).then(r=>r.json())).rows[0];});
  try{
    await page.goto(base+'/dang-nhap/');await page.locator('[name=username]').fill('quan_tri');await page.locator('[name=password]').fill('matkhau-kiem-thu-1');
    await Promise.all([page.waitForURL(u=>!u.pathname.includes('dang-nhap')),page.locator('button[type=submit]').click()]);
    // Hợp đồng trong snapshot: người đăng nhập đứng đơn, không còn chọn Sale thay.
    const entryActor=await actor('staff_sale_1'),entry=entryActor.p;
    await entry.goto(base+'/van-don/len-don/');await entry.locator('[name=customer_name]').fill('Khách E2E chín hạng mục');await entry.locator('[name=phone]').fill('0912345999');
    for(const name of ['market','currency','payment_method']){const value=await entry.locator('[name='+name+'] option').evaluateAll(opts=>opts.find(o=>o.value).value);await entry.locator('[name='+name+']').selectOption(value);}
    await entry.locator('[name=product]').selectOption('feedback-0');await entry.locator('[name=unit_price]').fill('1');
    await entry.getByRole('button',{name:'Lưu đơn',exact:true}).click();await entry.locator('.vd-success').waitFor();await entryActor.ctx.close();
    const created=await page.evaluate(async()=>{const url='/bang-tinh/van_don_moi/du-lieu/';const first=await fetch(url).then(r=>r.json());return (await fetch(url+'?offset='+(first.total-1)).then(r=>r.json())).rows[0];});
    assert.equal(created.cells.ten_khach.value,'Khách E2E chín hạng mục');const createdUrl=base+'/bang-tinh/van_don_moi/?f_ma_don='+encodeURIComponent(created.cells.ma_don.value);
    async function actor(username){const ctx=await browser.newContext({viewport:{width:1440,height:900}}),p=await ctx.newPage();await p.goto(base+'/dang-nhap/');await p.locator('[name=username]').fill(username);await p.locator('[name=password]').fill('matkhau-kiem-thu-1');await Promise.all([p.waitForURL(u=>!u.pathname.includes('dang-nhap')),p.locator('button[type=submit]').click()]);return {ctx,p};}
    const leader=await actor('vd_leader');await leader.p.goto(createdUrl);await leader.p.locator('.mg-number').first().click();await leader.p.locator('#mg-more-button').click();await leader.p.locator('#mg-assign').click();
    await leader.p.locator('#vd-assignment-fields select[name=delivery]').selectOption(String(JSON.parse(fs.readFileSync(signal)).delivery));await leader.p.locator('#vd-assignment-save').click();await leader.p.locator('#vd-assignment').waitFor({state:'hidden'});
    const staff=await actor('staff_vd');await staff.p.goto(createdUrl);await staff.p.locator('.mg-cell[data-code=bang]').dblclick({delay:120});await staff.p.locator('#mg-editor input').fill('Staff E2E');await staff.p.keyboard.press('Enter');await staff.p.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đã lưu');
    const sale=await actor('staff_sale_1');await sale.p.goto(createdUrl);await sale.p.locator('.mg-cell[data-code=bang]').waitFor();assert.equal(await sale.p.locator('.mg-cell[data-code=bang]').textContent(),'Staff E2E');
    await sale.p.locator('.mg-cell[data-code=bang]').click();await sale.p.locator('#mg-more-button').click();await sale.p.locator('#mg-history-button').click();await sale.p.locator('#mg-history .mg-history-item').first().waitFor();assert.match(await sale.p.locator('#mg-history-body').textContent(),/staff_vd/);
    await staff.p.locator('.mg-cell[data-code=bang]').dblclick({delay:120});await staff.p.locator('#mg-editor input').fill('Nháp khi bị thu quyền');
    await leader.p.evaluate(async id=>{const url='/van-don/phan-cong/',snapshot=await fetch(url+'?row='+id).then(r=>r.json());const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':document.querySelector('[name=csrfmiddlewaretoken]').value},body:JSON.stringify({versions:{[id]:snapshot.rows[0].version},changes:{delivery:null}})});if(!r.ok)throw Error('Thu phân công thất bại');},created.id);
    await staff.p.bringToFront();await staff.p.waitForFunction(()=>document.getElementById('mg-editor').hidden&&!document.querySelector('.mg-cell[data-id]'),{},{timeout:18000});assert.equal(await staff.p.locator('#mg-input').textContent(),'');
    await require('./kiem-thu-master-revoked-batch.cjs')({admin:page,leader:leader.p,staff:staff.p,context:staff.ctx,base,delivery:JSON.parse(fs.readFileSync(signal)).delivery});
    evidence.checks.push('Thu quyền một dòng trong lượt dán: rollback cả lượt, gỡ dòng mất quyền, giữ nháp còn quyền, chỉ gửi lại khi bấm Thử lại');
    await sale.ctx.close();await staff.ctx.close();await leader.ctx.close();evidence.checks.push('E2E Sale lên đơn → cuối bảng → Leader phân công → Staff autosave → Sale xem lịch sử; thu quyền gỡ cả nháp');
    await open();assert.equal(await page.locator('.mg-number').first().textContent(),'1');
    await page.locator('.mg-number').first().click();await page.waitForFunction(()=>document.querySelector('.mg-number').getAttribute('aria-selected')==='true');
    assert.equal(await page.locator('.mg-number').first().evaluate(e=>getComputedStyle(e).backgroundColor),'rgb(37, 99, 235)');
    evidence.checks.push('Số 1 và chọn hàng xanh');
    await page.screenshot({path:path.join(out,'row-selected.png')});
    await (await cell('ghi_chu')).dblclick({delay:120});await page.locator('#mg-editor textarea').fill('Tiếng Việt\nTự lưu');await page.keyboard.press('Control+Enter');await saved();
    assert.equal((await read()).cells.ghi_chu.value,'Tiếng Việt\nTự lưu');evidence.checks.push('Bấm đúp 120ms, nội dung nhiều dòng, autosave');
    await page.locator('#mg-mode').click();await (await cell('bang')).click();await page.locator('#mg-editor input').fill('CA');
    await page.keyboard.press('Tab');await page.locator('#mg-editor input').waitFor();assert.equal(await page.locator('#mg-editor input').getAttribute('aria-label'),'Thành phố');
    await page.locator('#mg-editor input').fill('Hà Nội');await page.keyboard.press('Escape');await saved();assert.equal((await read()).cells.bang.value,'CA');
    evidence.checks.push('Chế độ Chỉnh sửa và Tab mở ô tiếp theo');
    await page.locator('#mg-mode').click();await (await cell('bang')).click();await page.locator('#mg-format-button').click();await page.getByLabel('Cỡ chữ',{exact:true}).selectOption('18');await saved();
    assert.equal((await read()).cells.bang.style.fs,18);await page.locator('#mg-undo').click();await saved();assert.equal((await read()).cells.bang.style.fs,undefined);await page.locator('#mg-redo').click();await saved();
    evidence.checks.push('Định dạng, Undo/Redo qua server');
    // Giữ phản hồi đầu tiên, tiếp tục sửa cùng ô và xác nhận nháp mới không bị mất.
    let held=false;await page.route('**/luu-json/',async route=>{if(!held){held=true;const response=await route.fetch();await pause(1400);await route.fulfill({response});}else await route.continue();});
    await (await cell('bang')).dblclick({delay:120});await page.locator('#mg-editor input').fill('A');await page.keyboard.press('Enter');await page.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đang lưu');
    await (await cell('bang')).dblclick({delay:120});await page.locator('#mg-editor input').fill('B');await page.keyboard.press('Enter');await saved();assert.equal((await read()).cells.bang.value,'B');await page.unroute('**/luu-json/');
    evidence.checks.push('Sửa tiếp trong khi phản hồi bị trễ');
    let lostPayload=null,replayed=false;await page.route('**/luu-json/',async route=>{
      if(!lostPayload){lostPayload=route.request().postDataJSON();await route.fetch();await route.abort('connectionreset');}
      else{assert.deepEqual(route.request().postDataJSON(),lostPayload);const response=await route.fetch();replayed=(await response.json()).replayed;await route.fulfill({response});}
    });
    await (await cell('bang')).dblclick({delay:120});await page.locator('#mg-editor input').fill('Gửi lại an toàn');await page.keyboard.press('Enter');await page.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Lỗi lưu');await saved();assert(replayed);await page.unroute('**/luu-json/');
    evidence.checks.push('Mất phản hồi sau commit → cùng ID/nội dung → replay không ghi lần hai');
    // Một request khác thay đổi server trong khi editor giữ giá trị cũ.
    await (await cell('bang')).dblclick({delay:120});await page.locator('#mg-editor input').fill('Của tôi');
    await page.evaluate(async()=>{const c=JSON.parse(document.getElementById('mg-config').textContent),row=(await fetch(c.dataUrl+location.search).then(r=>r.json())).rows[0];const response=await fetch(c.saveUrl,{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':document.querySelector('[name=csrfmiddlewaretoken]').value},body:JSON.stringify({operation:crypto.randomUUID(),cells:[{id:row.id,column:'bang',old:row.cells.bang.value,value:'Đồng nghiệp'}]})});if(response.status!==200)throw Error('Không tạo được fixture xung đột');});
    await page.keyboard.press('Enter');await page.getByRole('button',{name:'Đối chiếu xung đột',exact:true}).click();await page.locator('#mg-conflict select').selectOption('mine');await page.getByRole('button',{name:'Áp dụng lựa chọn và lưu'}).click();await saved();assert.equal((await read()).cells.bang.value,'Của tôi');
    evidence.checks.push('409, đối chiếu và gửi lại có CAS');
    await (await cell('bang')).dblclick({delay:120});await page.locator('#mg-editor input').fill('Bỏ phần của tôi');
    await page.evaluate(async()=>{const c=JSON.parse(document.getElementById('mg-config').textContent),row=(await fetch(c.dataUrl+location.search).then(r=>r.json())).rows[0];const r=await fetch(c.saveUrl,{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':document.querySelector('[name=csrfmiddlewaretoken]').value},body:JSON.stringify({operation:crypto.randomUUID(),cells:[{id:row.id,column:'bang',old:row.cells.bang.value,value:'Hiện tại được giữ'}]})});if(!r.ok)throw Error('Tạo xung đột thứ hai thất bại');});
    await page.keyboard.press('Enter');await page.getByRole('button',{name:'Đối chiếu xung đột',exact:true}).click();await page.locator('#mg-conflict select').selectOption('server');await page.getByRole('button',{name:'Áp dụng lựa chọn và lưu'}).click();
    await page.waitForFunction(()=>document.querySelector('.mg-cell[data-code="bang"][data-r="0"]').textContent==='Hiện tại được giữ',{}, {timeout:1000});await saved();
    evidence.checks.push('Dùng giá trị hiện tại cập nhật ô ngay, không đợi polling');
    assert.equal(await page.locator('#mg-message').textContent(),'');
    await page.locator('#mg-more-button').click();await page.locator('#mg-history-button').click();await page.locator('#mg-history .mg-history-item').first().waitFor();assert.match(await page.locator('#mg-history-body').textContent(),/Của tôi/);await page.screenshot({path:path.join(out,'history.png')});await page.keyboard.press('Escape');
    evidence.checks.push('Lịch sử có trước/sau và nút đóng');
    // Kéo hàng không làm lệch các ô; số hàng và ô dữ liệu dùng chung chiều cao.
    const handle=page.locator('[data-row-resize="0"]'),box=await handle.boundingBox();await page.mouse.move(box.x+20,box.y+3);await page.mouse.down();await page.mouse.move(box.x+20,box.y+90,{steps:8});await page.mouse.up();
    const heights=await page.locator('.mg-row').first().evaluate(e=>[...e.querySelectorAll('.mg-cell,.mg-number')].map(c=>c.getBoundingClientRect().height));assert(heights[0]>100&&heights.every(h=>h===heights[0]));
    evidence.checks.push('Kéo chiều cao hàng đồng bộ');
    await page.locator('#mg-viewport').evaluate(e=>e.scrollLeft+=300);await pause(100);
    assert.equal(await page.locator('.mg-cell[data-r="0"][data-code="ten_khach"]').evaluate(e=>{const r=e.getBoundingClientRect();return document.elementFromPoint(r.x+r.width/2,r.y+10).dataset.code;}),'ten_khach');
    evidence.checks.push('Ô hiện hành không đè cột cố định khi cuộn ngang');
    for(const width of [1440,1280,390]){await page.setViewportSize({width,height:900});await pause(150);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:path.join(out,`grid-${width}.png`)});}
    await page.setViewportSize({width:1280,height:900});await page.evaluate(()=>document.body.style.zoom='1.25');await pause(150);await page.screenshot({path:path.join(out,'zoom125.png')});
    evidence.checks.push('Desktop/laptop/mobile/zoom');
    await page.evaluate(()=>document.body.style.zoom='');
    await page.goto(base+'/bang-tinh/van_don_moi/');await page.locator('.mg-cell[data-id]').first().waitFor();await page.locator('#mg-viewport').focus();await page.keyboard.press('Control+a');await page.keyboard.press('Control+c');await page.waitForFunction(()=>document.getElementById('mg-message').textContent.includes('vượt 2000'));
    await page.keyboard.press('Delete');assert.match(await page.locator('#mg-message').textContent(),/vượt 2000/);
    evidence.checks.push('Ctrl+A chọn cả kết quả, copy/Delete vượt 2.000 ô bị chặn');
    await require('./kiem-thu-master-row-height.cjs')({page,context,base});evidence.checks.push('Hồi quy hàng/cột, cache, copy/paste số 0 đầu, phím, cảm ứng, localStorage');
    assert.deepEqual(errors,[]);evidence.ok=true;
  }catch(error){evidence.ok=false;evidence.error=error.stack;await page.screenshot({path:path.join(out,'failure.png')}).catch(()=>{});process.exitCode=1;}
  finally{fs.writeFileSync(path.join(out,'ui-result.json'),JSON.stringify(evidence,null,2));fs.writeFileSync(result,JSON.stringify(evidence));await browser.close();console.log(JSON.stringify(evidence));}
})();
