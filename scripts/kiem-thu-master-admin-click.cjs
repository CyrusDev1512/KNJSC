/* Hồi quy click Admin; chỉ dùng server fixture DB test cổng 8035. */
const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),out=path.join(root,'.agents/design-state/review/master-admin-20260911');
(async()=>{
  fs.mkdirSync(out,{recursive:true});const browser=await chromium.launch({channel:'chrome',headless:true});
  const page=await browser.newPage({viewport:{width:1440,height:900}}),result={checks:[]};
  try{
    await page.goto('http://127.0.0.1:8035/dang-nhap/');await page.locator('[name=username]').fill('quan_tri');await page.locator('[name=password]').fill('matkhau-kiem-thu-1');
    await Promise.all([page.waitForURL(u=>!u.pathname.includes('dang-nhap')),page.locator('button[type=submit]').click()]);
    await page.goto('http://127.0.0.1:8035/bang-tinh/van_don_moi/?f_ma_don=MASTER-00000');
    const cell=page.locator('.mg-cell[data-r="0"][data-code="bang"]');await cell.waitFor();
    await page.locator('#mg-mode').click();await cell.click();await page.locator('#mg-editor input').waitFor();
    result.checks.push('Admin click đứng yên mở ô sửa');await page.keyboard.press('Escape');
    const box=await cell.boundingBox();await page.mouse.move(box.x+30,box.y+12);await page.mouse.down();
    await page.mouse.move(box.x+37,box.y+12,{steps:3});await page.mouse.up();
    await page.waitForTimeout(150);assert(await page.locator('#mg-editor').isVisible(),'Rê nhẹ 7px trong cùng ô không được làm mất thao tác sửa');
    result.checks.push('Admin click lệch nhẹ trong cùng ô vẫn mở sửa');
    const inputBox=await page.locator('#mg-editor').boundingBox(),cellBox=await cell.boundingBox();
    result.geometry={inputBox,cellBox,classes:await page.locator('#mg-editor').getAttribute('class')};
    assert(Math.abs(inputBox.x-cellBox.x)<2&&Math.abs(inputBox.y-cellBox.y)<2&&inputBox.height<=cellBox.height+1,'Trình sửa phải nằm trong ô, không che hàng phía dưới');
    result.checks.push('Nhập ngay trong ô, không che hàng bên dưới');await page.keyboard.press('Escape');
    async function findCell(code){
      await page.evaluate(async code=>{const config=JSON.parse(document.getElementById('mg-config').textContent),data=await fetch(config.dataUrl+location.search).then(r=>r.json());document.getElementById('mg-viewport').scrollLeft=Math.max(0,data.columns.findIndex(c=>c.code===code)*160-600);},code);
      const target=page.locator(`.mg-cell[data-r="0"][data-code="${code}"]`);await target.waitFor();return target;
    }
    for(const code of ['trang_thai_vc','ngay_tt']){
      await (await findCell(code)).click();const input=page.locator(code==='ngay_tt'?'#mg-editor input[type=date]':'#mg-editor select');await input.waitFor();
      const before=await input.inputValue();
      const value=code==='ngay_tt'?(before==='2026-09-10'?'2026-09-11':'2026-09-10'):await input.locator('option').evaluateAll((options,old)=>options.find(o=>o.value&&o.value!==old).value,before);
      if(code==='ngay_tt')await input.fill(value);else await input.selectOption(value);
      await page.keyboard.press('Enter');await page.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đã lưu');
      const actual=await page.evaluate(async code=>{const c=JSON.parse(document.getElementById('mg-config').textContent),data=await fetch(c.dataUrl+location.search).then(r=>r.json());return data.rows[0].cells[code].value;},code);
      assert.equal(actual,value);
      const history=await page.evaluate(async code=>{const c=JSON.parse(document.getElementById('mg-config').textContent),data=await fetch(c.dataUrl+location.search).then(r=>r.json());return fetch(c.historyUrl+'?record='+data.rows[0].id+'&column='+code).then(r=>r.json());},code);
      assert.equal(history.items[0].after,value);assert.equal(history.items[0].actor,'quan_tri');
      result.checks.push('Admin sửa, lưu và ghi lịch sử '+code);
    }
    await (await findCell('bang')).click();await page.locator('#mg-editor input').fill('Ô 1');await page.keyboard.press('Tab');
    await page.locator('#mg-editor input[aria-label="Thành phố"]').fill('Ô 2');await page.keyboard.press('Enter');await page.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đã lưu');
    result.checks.push('Tab nhập liên tiếp, autosave không khóa lưới');
    await (await findCell('bang')).click();await page.evaluate(()=>{const transfer=new DataTransfer();transfer.setData('text/plain','00123\tHà Nội');document.querySelector('#mg-editor input').dispatchEvent(new ClipboardEvent('paste',{bubbles:true,cancelable:true,clipboardData:transfer}));});
    await page.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đã lưu');
    const pasted=await page.evaluate(async()=>{const c=JSON.parse(document.getElementById('mg-config').textContent),data=await fetch(c.dataUrl+location.search).then(r=>r.json());return [data.rows[0].cells.bang.value,data.rows[0].cells.thanh_pho.value];});
    assert.deepEqual(pasted,['00123','Hà Nội']);result.checks.push('Dán TSV từ ô đang sửa giữ số 0 đầu và ghi cả vùng');
    await page.locator('#mg-mode').click();
    await (await findCell('trang_thai_vc')).dblclick({delay:120});await page.locator('#mg-editor select').waitFor();await page.keyboard.press('Escape');
    await (await findCell('ngay_tt')).click();await page.keyboard.press('F2');await page.locator('#mg-editor input[type=date]').waitFor();await page.keyboard.press('Escape');
    result.checks.push('Chế độ Xem: bấm đúp 120ms mở trạng thái; F2 mở ngày');
    // Metadata lỗi không được để lại draft ma chặn mọi ô sau đó.
    await page.route('**/du-lieu/**',async route=>{const response=await route.fetch(),body=await response.json();body.columns.find(c=>c.code==='trang_thai_vc').options=null;await route.fulfill({response,json:body});});
    await page.reload();await cell.waitFor();await page.locator('#mg-mode').click();
    await (await findCell('trang_thai_vc')).click();assert.equal(await page.locator('#mg-editor').isVisible(),false);
    await (await findCell('bang')).click();await page.locator('#mg-editor input').waitFor();await page.keyboard.press('Escape');
    result.checks.push('Danh sách chọn lỗi không khóa các ô khác hoặc tạo bản nháp ma');
    await page.unrouteAll({behavior:'wait'});await page.reload();await cell.waitFor();
    await page.locator('#mg-mode').click();
    await (await findCell('bang')).click();
    // Hình học trình nhập: cột ghim, màn hình hẹp và CSS zoom.
    await page.keyboard.press('Escape');
    for(const width of [1440,1280,390]){
      await page.setViewportSize({width,height:900});await page.locator('#mg-viewport').evaluate(e=>e.scrollLeft=0);
      const target=page.locator('.mg-cell[data-r="0"][data-code="ma_don"]');await target.click();await page.locator('#mg-editor input').waitFor();
      const a=await target.boundingBox(),b=await page.locator('#mg-editor').boundingBox();assert(Math.abs(a.x-b.x)<2&&Math.abs(a.y-b.y)<2&&Math.abs(a.height-b.height)<2);
      await page.screenshot({path:path.join(out,`inline-${width}.png`)});await page.keyboard.press('Escape');
    }
    await page.setViewportSize({width:1280,height:900});await page.evaluate(()=>document.body.style.zoom='1.25');
    await page.locator('.mg-cell[data-r="0"][data-code="ma_don"]').click();await page.locator('#mg-editor input').waitFor();
    const zoom=await page.locator('#mg-editor').boundingBox(),zoomCell=await page.locator('.mg-cell[data-r="0"][data-code="ma_don"]').boundingBox();assert(Math.abs(zoom.x-zoomCell.x)<2&&Math.abs(zoom.y-zoomCell.y)<2&&Math.abs(zoom.height-zoomCell.height)<2);
    await page.screenshot({path:path.join(out,'inline-zoom125.png')});await page.keyboard.press('Escape');await page.evaluate(()=>document.body.style.zoom='');
    result.checks.push('Trình nhập bám cột ghim ở 1440/1280/390 và CSS zoom 125%');
    await page.setViewportSize({width:1440,height:900});await (await findCell('bang')).click();
    if(process.env.MASTER_INLINE_PERF==='1'){
      await page.locator('#mg-editor input').fill('Kiểm nhập khi lưu '+Date.now());
      let release;const gate=new Promise(resolve=>release=resolve);
      await page.route('**/luu-json/',async route=>{const response=await route.fetch();await gate;await route.fulfill({response});});
      await page.keyboard.press('Enter');await page.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đang lưu');
      await page.evaluate(()=>{
        window.__inlineTiming={open:[],input:[]};
        for(const [id,event,key] of [['mg-viewport','pointerup','open'],['mg-editor','input','input']]){
          document.getElementById(id).addEventListener(event,()=>{const start=performance.now();requestAnimationFrame(()=>requestAnimationFrame(()=>window.__inlineTiming[key].push(performance.now()-start)));});
        }
      });
      const samples=[];
      try{for(let i=0;i<100;i++){
        const start=Date.now();await cell.click();await page.locator('#mg-editor input').waitFor();await page.keyboard.insertText('Tiếng Việt');
        await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));samples.push(Date.now()-start);
        assert.equal(await page.locator('#bt-trang-thai').textContent(),'Đang lưu');await page.keyboard.press('Escape');
      }}finally{release();}
      await page.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đã lưu');await page.unrouteAll({behavior:'wait'});
      samples.sort((a,b)=>a-b);result.performance={samples:100,p50:samples[49],p95:samples[94],p99:samples[98],unit:'ms',method:'Playwright real click + insertText tới hai frame; 1 dòng lọc trên fixture 1300 dòng, phản hồi lưu bị giữ; không phải IME thực tế'};
      result.performance.events=await page.evaluate(()=>Object.fromEntries(Object.entries(window.__inlineTiming).map(([key,values])=>{values.sort((a,b)=>a-b);return [key,{samples:values.length,p50:values[49],p95:values[94],p99:values[98]}];})));
      await cell.click();
    }
    await page.screenshot({path:path.join(out,'inline-grid.png')});result.ok=true;
  }catch(e){result.ok=false;result.error=e.stack;await page.screenshot({path:path.join(out,'admin-click.png')}).catch(()=>{});process.exitCode=1;}
  finally{fs.writeFileSync(path.join(out,'click-result.json'),JSON.stringify(result,null,2));await browser.close();console.log(JSON.stringify(result));}
})();
