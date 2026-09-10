/* Chrome → pytest live_server, tuyệt đối không dùng DB dev. */
const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('assert/strict');
const root=path.resolve(__dirname,'..'),out=path.join(root,'.agents/design-state/review/master'),base='http://127.0.0.1:8031';
const delay=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
  const signal=path.join(root,'app/.master-browser-ready.json'),result=path.join(root,'app/.master-browser-result.json');
  for(let i=0;i<120&&!fs.existsSync(signal);i++)await delay(500);if(!fs.existsSync(signal))throw Error('Thiếu database test/browser server');
  fs.mkdirSync(out,{recursive:true});const fixture=JSON.parse(fs.readFileSync(signal));
  const browser=await chromium.launch({channel:'chrome',headless:true});
  const context=await browser.newContext({viewport:{width:1440,height:900},permissions:['clipboard-read','clipboard-write']});
  const page=await context.newPage(),errors=[],metrics={};page.on('pageerror',e=>errors.push(e.message));
  const grid='/bang-tinh/van_don_moi/?sap=ma_don';
  async function open(url=grid){await page.goto(base+url);await page.locator('.mg-cell[data-id]').first().waitFor();}
  async function saved(){await page.keyboard.press('Control+s');await page.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đã lưu');await page.locator('.mg-cell[data-id]').first().waitFor();}
  async function cell(code,r=0){const c=page.locator(`.mg-cell[data-r="${r}"][data-code="${code}"]`);if(!await c.count())await page.locator('#mg-viewport').evaluate((e,code)=>{const names=JSON.parse(document.getElementById('mg-config').textContent);e.scrollLeft=code==='ghi_chu'?3000:0;},code);await c.waitFor();return c;}
  try{
    await page.goto(base+'/dang-nhap/');await page.locator('[name=username]').fill('quan_tri');await page.locator('[name=password]').fill('matkhau-kiem-thu-1');
    await Promise.all([page.waitForURL(u=>!u.pathname.includes('dang-nhap')),page.locator('button[type=submit]').click()]);
    await open();
    const dimensions=()=>page.evaluate(()=>({width:document.documentElement.scrollWidth,viewport:innerWidth,grid:document.getElementById('mg-viewport').getBoundingClientRect().toJSON()}));
    // Khoảng cách giữa hai lần bấm phải qua một nhịp render như chuột thật.
    const interactionFailures=[];
    await (await cell('bang')).dblclick({delay:120});
    await page.waitForTimeout(160);
    if(!await page.locator('#mg-editor').isVisible())interactionFailures.push('Bấm đúp 120ms không mở ô nhập');
    else await page.locator('#mg-cancel').click();
    const edge=await page.locator('[data-resize="ma_don"]').boundingBox();
    const widthBefore=await page.locator('[data-column="0"]').evaluate(e=>e.getBoundingClientRect().width);
    await page.mouse.move(edge.x+edge.width-1,edge.y+8);await page.mouse.down();
    await page.mouse.move(edge.x+edge.width+95,edge.y+8,{steps:12});await page.mouse.up();
    await page.waitForTimeout(100);
    const widthAfter=await page.locator('[data-column="0"]').evaluate(e=>e.getBoundingClientRect().width);
    if(widthAfter<widthBefore+80)interactionFailures.push('Kéo cạnh phải tay nắm không mở rộng cột');
    metrics.pointer={widthBefore,widthAfter};
    assert.deepEqual(interactionFailures,[]);
    metrics.initial=await dimensions();await (await cell('ma_don')).click();await page.keyboard.press('Control+a');
    await page.waitForFunction(()=>/32.550|32,550/.test(document.getElementById('mg-selection').textContent));
    assert.deepEqual(await dimensions(),metrics.initial);
    await page.keyboard.press('Control+c');await page.getByText(/Vùng chọn vượt 2000 ô/).waitFor();
    await page.keyboard.press('Delete');assert.match(await page.locator('#mg-message').textContent(),/2000/);
    const handle=page.locator('[data-resize="ma_don"]');const b=await handle.evaluate(e=>e.getBoundingClientRect().toJSON());await page.mouse.move(b.x+3,b.y+8);await page.mouse.down();await page.mouse.move(b.x+130,b.y+8,{steps:10});await page.mouse.up();
    const widths=await page.evaluate(()=>({h:document.querySelector('[data-column="0"]').getBoundingClientRect().width,c:document.querySelector('.mg-cell[data-c="0"]').getBoundingClientRect().width}));assert.equal(widths.h,widths.c);
    await page.screenshot({path:path.join(out,'grid-desktop.png')});
    await page.locator('#mg-viewport').focus();await page.keyboard.press('Control+End');await page.locator('.mg-cell[data-r="1301"][data-id]').first().waitFor();
    metrics.deep=await page.evaluate(()=>window.KNJSC_MASTER.diagnostics());
    const rowOrder=await page.locator('.mg-body .mg-row').evaluateAll(rows=>rows.map(r=>Number(r.getAttribute('aria-rowindex'))));
    assert.deepEqual(rowOrder,[...rowOrder].sort((a,b)=>a-b));assert(metrics.deep.cache<=10);assert(metrics.deep.cells<1500);
    // Chọn/copy xuyên biên khối 99→100, với định danh lấy từ server.
    await open();await page.locator('#mg-viewport').evaluate(e=>e.scrollTop=98*28);
    await page.locator('.mg-cell[data-r="98"][data-code="bang"]').click();
    for(let i=0;i<5;i++)await page.keyboard.press('Shift+ArrowDown');
    await page.keyboard.press('Control+c');await page.getByText('Đã sao chép 6 ô.',{exact:true}).waitFor();
    assert.equal((await page.evaluate(()=>navigator.clipboard.readText())).split('\r\n').length,6);
    await open('/bang-tinh/van_don_moi/?f_ma_don=MASTER-00000');
    const note=await cell('ghi_chu');await note.click();await page.locator('#mg-reader').waitFor();assert.match(await page.locator('#mg-reader').textContent(),/Nội dung dài/);
    await page.keyboard.press('Escape');await note.dblclick({delay:120});await page.locator('#mg-editor textarea').waitFor();
    const before=await dimensions(),textarea=page.locator('#mg-editor textarea');await textarea.fill('Ghi chú tiếng Việt\nDòng thứ hai');
    await textarea.dispatchEvent('keydown',{key:'Enter',ctrlKey:true,isComposing:true});assert(await page.locator('#mg-editor').isVisible());
    await page.keyboard.press('Control+a');assert.equal(await textarea.evaluate(e=>e.selectionEnd-e.selectionStart),await textarea.inputValue().then(s=>s.length));
    const eb=await page.locator('#mg-editor').boundingBox();await page.mouse.move(eb.x+eb.width-3,eb.y+eb.height-3);await page.mouse.down();await page.mouse.move(eb.x+eb.width+150,eb.y+eb.height+100,{steps:8});await page.mouse.up();assert.deepEqual(await dimensions(),before);
    const expandedEditor=await page.locator('#mg-editor').boundingBox();assert(expandedEditor.width>eb.width+80,'Khung nhập phải thật sự mở rộng');
    await page.screenshot({path:path.join(out,'editor-desktop.png')});await textarea.focus();await page.keyboard.press('Control+Enter');await saved();
    await page.locator('#mg-undo').click();await saved();await page.locator('#mg-redo').click();await saved();
    await (await cell('ghi_chu')).dblclick({delay:120});assert.equal(await page.locator('#mg-editor textarea').inputValue(),'Ghi chú tiếng Việt\nDòng thứ hai');await page.keyboard.press('Escape');
    // Cùng ô thay đổi giữa lúc đọc và lưu → không ghi đè.
    await (await cell('ghi_chu')).dblclick({delay:120});await page.locator('#mg-editor textarea').fill('Bản nháp của tôi');
    const snapshot=await context.request.get(base+'/bang-tinh/van_don_moi/du-lieu/?f_ma_don=MASTER-00000').then(r=>r.json());const row=snapshot.rows[0];
    const token=await page.locator('[name=csrfmiddlewaretoken]').first().inputValue();
    const changed=await context.request.post(base+'/bang-tinh/van_don_moi/luu-json/',{headers:{'X-CSRFToken':token,Referer:base+grid},data:{operation:require('crypto').randomUUID(),cells:[{id:row.id,column:'ghi_chu',old:row.cells.ghi_chu.value,value:'Đồng nghiệp đã sửa'}]}});assert.equal(changed.status(),200);
    await page.locator('#mg-editor button[type=submit]').click();await page.keyboard.press('Control+s');await page.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Xung đột');assert.equal(await page.locator('#mg-editor textarea').inputValue(),'Bản nháp của tôi');
    await page.getByRole('button',{name:'Bỏ bản nháp',exact:true}).click();
    // Server đã lưu nhưng mất phản hồi: giữ nháp và gửi lại đúng UUID.
    await (await cell('ghi_chu')).dblclick({delay:120});await page.locator('#mg-editor textarea').fill('Lưu lại sau mất phản hồi');
    const operations=[];const capture=r=>{if(r.url().endsWith('/luu-json/')&&r.method()==='POST')operations.push(JSON.parse(r.postData()).operation);};page.on('request',capture);
    await page.route('**/luu-json/',async route=>{await route.fetch();await route.abort('failed');await page.unroute('**/luu-json/');});
    await page.locator('#mg-editor button[type=submit]').click();await page.keyboard.press('Control+s');await page.getByRole('button',{name:'Thử lại',exact:true}).waitFor();
    assert.equal(await page.locator('#mg-editor textarea').inputValue(),'Lưu lại sau mất phản hồi');
    await page.getByRole('button',{name:'Thử lại',exact:true}).click();await saved();page.off('request',capture);
    assert.equal(operations.length,2);assert.equal(operations[0],operations[1]);
    // Clipboard ghi thật vào hai ô liền kề, kèm số 0 đầu và tiếng Việt.
    await open('/bang-tinh/van_don_moi/?f_ma_don=MASTER-00000');
    await (await cell('bang')).click();
    await page.evaluate(()=>navigator.clipboard.writeText('00123\tThành phố Việt Nam'));
    await page.keyboard.press('Control+v');await page.locator('.mg-cell[data-code="bang"][data-r="0"]').filter({hasText:'00123'}).waitFor();await saved();
    const pasted=await context.request.get(base+'/bang-tinh/van_don_moi/du-lieu/?f_ma_don=MASTER-00000').then(r=>r.json());
    assert.equal(pasted.rows[0].cells.bang.value,'00123');assert.equal(pasted.rows[0].cells.thanh_pho.value,'Thành phố Việt Nam');
    await (await cell('bang')).click();await page.keyboard.press('Control+c');await page.getByText('Đã sao chép 1 ô.',{exact:true}).waitFor();
    assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),'00123');
    const clipboardHtml=await page.evaluate(async()=>{const items=await navigator.clipboard.read();const item=items.find(i=>i.types.includes('text/html'));return item?await (await item.getType('text/html')).text():'';});
    assert.match(clipboardHtml,/mso-number-format/);assert.match(clipboardHtml,/00123/);

    // Phân công và chi tiết giữ đường ghi chuyên dụng.
    await open('/bang-tinh/van_don_moi/?f_ma_don=MASTER-00000');await (await cell('ma_don')).click();await page.locator('#mg-more-button').click();await page.locator('#mg-assign').click();
    await page.locator('#vd-assignment [name=delivery]').selectOption(String(fixture.delivery));
    await page.locator('#vd-assignment-save').click();await page.waitForFunction(()=>!document.getElementById('vd-assignment').open);
    // Thu quyền ngay trước poll đầu tiên: editor và dòng phải bị gỡ.
    const staffContext=await browser.newContext({viewport:{width:1440,height:900}}),staffPage=await staffContext.newPage();
    try{
      await staffPage.goto(base+'/dang-nhap/');await staffPage.locator('[name=username]').fill('staff_vd');await staffPage.locator('[name=password]').fill('matkhau-kiem-thu-1');
      await Promise.all([staffPage.waitForURL(u=>!u.pathname.includes('dang-nhap')),staffPage.locator('button[type=submit]').click()]);
      await staffPage.goto(base+'/bang-tinh/van_don_moi/?f_ma_don=MASTER-00000');await staffPage.locator('.mg-cell[data-id]').first().waitFor();
      await staffPage.locator('#mg-viewport').evaluate(e=>e.scrollLeft=3000);await staffPage.locator('.mg-cell[data-code="ghi_chu"][data-id]').first().dblclick({delay:120});await staffPage.locator('#mg-editor textarea').fill('Nháp trước chuyển giao');
      const assignment=await context.request.get(base+'/van-don/phan-cong/?row='+pasted.rows[0].id).then(r=>r.json());
      const revoked=await context.request.post(base+'/van-don/phan-cong/',{headers:{'X-CSRFToken':token,Referer:base+grid},data:{versions:{[pasted.rows[0].id]:assignment.rows[0].version},changes:{delivery:null}}});assert.equal(revoked.status(),200);
      await staffPage.waitForFunction(()=>document.getElementById('mg-editor').hidden,{},{timeout:12000});
      await staffPage.waitForFunction(()=>document.getElementById('mg-count').textContent.startsWith('0 dòng'),{},{timeout:12000});
      assert.equal(await staffPage.locator('.mg-cell[data-id]').count(),0);
    }finally{await staffContext.close();}
    await open('/bang-tinh/van_don_moi/?f_ma_don=MASTER-00000');await (await cell('san_pham')).dblclick({delay:120});await page.locator('#vd-detail form').waitFor();await page.keyboard.press('Escape');
    await open();await page.locator('#mg-filters-button').click();await page.locator('#mg-filters input[name="tim"]').fill('Khách kiểm thử 0');await page.locator('#mg-filters form button').first().click();await page.waitForURL(u=>u.searchParams.get("tim")==="Khách kiểm thử 0");await page.waitForFunction(()=>document.getElementById('mg-count').textContent.startsWith('1 dòng'));
    await page.reload();await page.locator('.mg-cell[data-id]').first().waitFor();assert.match(await page.locator('#mg-count').textContent(),/^1 dòng/);
    // Hai truy vấn liên tiếp: phản hồi tìm kiếm cũ về trễ không đè kết quả mới.
    await open();await page.route('**/du-lieu/**',async route=>{if(new URL(route.request().url()).searchParams.get('tim')==='Khách kiểm thử 1')await delay(700);await route.continue().catch(()=>{});});
    await page.locator('#mg-search input').fill('Khách kiểm thử 1');await page.locator('#mg-search button').click();
    await page.locator('#mg-search input').fill('Khách kiểm thử 0');await page.locator('#mg-search button').click();
    await page.waitForFunction(()=>document.getElementById('mg-count').textContent.startsWith('1 dòng'));await delay(800);
    assert.equal(new URL(page.url()).searchParams.get('tim'),'Khách kiểm thử 0');assert.match(await page.locator('#mg-count').textContent(),/^1 dòng/);await page.unroute('**/du-lieu/**');
    for(const width of [1280,390]){await page.setViewportSize({width,height:844});await open();assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await page.screenshot({path:path.join(out,`grid-${width}.png`)});}
    await page.setViewportSize({width:1440,height:900});await page.evaluate(()=>document.documentElement.style.zoom='1.25');assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await page.evaluate(()=>document.documentElement.style.zoom='');
    await page.goto(base+'/thong-ke/');await page.locator('.ms-charts').waitFor();assert.equal(await page.locator('.ms-chart').count(),4);await page.screenshot({path:path.join(out,'statistics-desktop.png')});
    await page.setViewportSize({width:390,height:844});await page.waitForTimeout(300);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await page.screenshot({path:path.join(out,'statistics-mobile.png'),fullPage:true});
    await open();
    const samples=[];
    for(let i=0;i<12;i++){await page.locator('#mg-viewport').evaluate((e,i)=>{e.scrollTop=i*2800;},i);await page.locator(`.mg-cell[data-r="${i*100}"][data-id]`).first().waitFor();
      samples.push(await page.evaluate(()=>({...window.KNJSC_MASTER.diagnostics(),heap:performance.memory?.usedJSHeapSize})));}
    assert(samples.every(s=>s.cache<=10&&s.cells<1500));metrics.scroll=samples;
    await require('./kiem-thu-master-row-height.cjs')({page,context,base});
    assert.deepEqual(errors,[]);fs.writeFileSync(path.join(out,'ui-results.json'),JSON.stringify(metrics,null,2));fs.writeFileSync(result,JSON.stringify({ok:true}));console.log('PASS master grid UI',JSON.stringify(metrics));
  }catch(e){console.log(await page.evaluate(()=>[...document.querySelectorAll('body *')].map(e=>({tag:e.tagName,cl:e.className,left:e.getBoundingClientRect().left,right:e.getBoundingClientRect().right})).filter(e=>e.right>innerWidth+2&&e.left>=0).slice(0,15)));await page.screenshot({path:path.join(out,'failure.png')}).catch(()=>{});fs.writeFileSync(result,JSON.stringify({ok:false,error:e.stack,errors}));throw e;}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
