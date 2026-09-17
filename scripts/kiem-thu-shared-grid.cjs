const fs=require('fs'),path=require('path'),assert=require('assert'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'../storage/crm-update'),base='http://127.0.0.1:8854';
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});const contexts=[];const result={ok:false,cases:[],errors:[],timings:[],ime:'Mô phỏng sự kiện composition; chưa kiểm bộ gõ hệ điều hành'};
try{const ready=JSON.parse(fs.readFileSync(path.join(root,'shared-browser-ready.json'))),url='/bang-tinh/'+ready.table+'/';
for(const [width,zoom] of [[1440,1],[1280,1],[390,1],[1440,1.25]]){
 const ctx=zoom===1?await browser.newContext({viewport:{width,height:900},permissions:['clipboard-read','clipboard-write']}):await chromium.launchPersistentContext(path.join(root,'chrome-zoom-e2e'),{channel:'chrome',headless:true,viewport:{width,height:900},permissions:['clipboard-read','clipboard-write']});contexts.push(ctx);const p=await ctx.newPage();p.setDefaultTimeout(18000);p.on('pageerror',e=>result.errors.push(e.message));
 if(zoom!==1){await p.goto('chrome://settings/appearance');await p.locator('#zoomLevel').selectOption(String(zoom));}
 async function login(user){await p.goto(base+'/dang-nhap/');await p.locator('[name=username]').fill(user);await p.locator('[name=password]').fill('matkhau-kiem-thu-1');await Promise.all([p.waitForURL(u=>!u.pathname.includes('dang-nhap')),p.locator('button[type=submit]').click()]);}
 await login('staff_mkt');
 if(width===1440&&zoom===1){
  await p.goto(base+'/bang-tinh/'+ready.empty+'/');await p.locator('.mg-cell[data-id="-1"]').first().waitFor();
  await p.locator('.mg-cell[data-id="-1"]').first().dblclick({delay:120});await p.locator('#mg-input [name=value]').fill('Dòng đầu tiên');
  const first=p.waitForResponse(r=>r.url().includes('luu-json/')&&r.request().method()==='POST');await p.locator('#mg-input [name=value]').press('Enter');assert.equal((await first).status(),200);
  await p.waitForFunction(()=>[...document.querySelectorAll('.mg-cell[data-id]')].some(c=>Number(c.dataset.id)>0));
  assert.match(await p.locator('#mg-count').textContent(),/^1 dòng/);result.emptyTable=true;
 }
 await p.goto(base+url);await p.waitForFunction(()=>window.KNJSC_MASTER?.diagnostics().total>=2);
 const zoomEvidence=await p.evaluate(()=>({dpr:devicePixelRatio,css:getComputedStyle(document.documentElement).zoom,scale:visualViewport.scale}));if(zoom!==1)assert.equal(zoomEvidence.dpr,1.25);
 const before=(await (await ctx.request.get(base+url+'du-lieu/')).json()).total;
 if(width===1440&&zoom===1){
  await p.locator('#mg-viewport').evaluate(v=>v.scrollLeft=v.scrollWidth);
  await p.locator('#mg-'+ready.row+'-moment').dblclick({delay:120});const moment=await p.locator('#mg-input [name=value]').inputValue();await p.keyboard.press('Escape');
  await p.locator('#mg-'+ready.row+'-suggestion').dblclick({delay:120});const tag=await p.locator('#mg-input [name=value]').evaluate(e=>e.tagName),suggestion=await p.locator('#mg-input [name=value]').inputValue();
  assert.deepEqual({moment,tag,suggestion},{moment:'2026-09-12T10:33:00+07:00',tag:'INPUT',suggestion:'Người đã nghỉ'});
  await p.locator('#mg-input [name=value]').fill('Tên ngoài danh sách');const custom=p.waitForResponse(r=>r.url().includes('luu-json/')&&r.request().method()==='POST');await p.locator('#mg-input [name=value]').press('Enter');assert.equal((await custom).status(),200);
  result.fieldCompatibility=true;await p.locator('#mg-viewport').evaluate(v=>v.scrollLeft=0);
 }
 const draft=p.locator('.mg-cell[data-id="-1"]').first();await draft.dblclick({delay:120});await p.locator('#mg-input [name=value]').fill('Moi-'+width+'-'+zoom);
 const creation=p.waitForResponse(r=>r.url().includes('luu-json/')&&r.request().method()==='POST');await p.locator('#mg-input [name=value]').press('Enter');const created=await creation;assert.equal(created.status(),200,await created.text());const payload=await created.json();assert(payload.id_map);
 await p.waitForTimeout(300);let data=await (await ctx.request.get(base+url+'du-lieu/')).json();assert.equal(data.total,before+1);
 await p.locator('#mg-viewport').focus();const undone=p.waitForResponse(r=>r.url().includes('luu-json/')&&r.request().method()==='POST');await p.keyboard.press('Control+z');assert.equal((await undone).status(),200);
 data=await (await ctx.request.get(base+url+'du-lieu/')).json();assert.equal(data.total,before);
 const redone=p.waitForResponse(r=>r.url().includes('luu-json/')&&r.request().method()==='POST');await p.keyboard.press('Control+y');assert.equal((await redone).status(),200);
 data=await (await ctx.request.get(base+url+'du-lieu/')).json();assert.equal(data.total,before+1);const id=Object.values(payload.id_map)[0];assert(data.rows.some(r=>r.id===id));
 await p.reload();await p.waitForFunction(()=>window.KNJSC_MASTER?.diagnostics().total>=2);
 const original=p.locator('#mg-'+ready.row+'-bill');await original.click();await p.keyboard.press('Escape');await p.evaluate(w=>navigator.clipboard.writeText('001234'+w),width+'-'+zoom);const pasted=p.waitForResponse(r=>r.url().includes('luu-json/')&&r.request().method()==='POST');await p.keyboard.press('Control+v');assert.equal((await pasted).status(),200);
 data=await (await ctx.request.get(base+url+'du-lieu/')).json();assert.equal(data.rows.find(r=>r.id===ready.row).cells.bill.value,'001234'+width+'-'+zoom);
 // Lựa chọn qua bàn phím: thời gian gồm một khung render, không giả lập bộ gõ thật.
 await original.click();for(let i=0;i<100;i++){const t=performance.now();await p.keyboard.press(i%2?'ArrowLeft':'ArrowRight');await p.evaluate(()=>new Promise(r=>requestAnimationFrame(r)));result.timings.push({width,action:'selection',ms:performance.now()-t});}
 // Kiểm công thức trên UI; nhấn Enter kết thúc nhập rồi server tính tổng.
 const x=46+data.columns.slice(0,data.columns.findIndex(c=>c.code==='a')).reduce((sum,c)=>sum+c.width,0);
 const frozen=await p.locator('.mg-heading.mg-pinned').evaluateAll(cols=>46+cols.reduce((sum,c)=>sum+c.getBoundingClientRect().width,0));
 await p.locator('#mg-viewport').evaluate((v,x)=>v.scrollLeft=Math.max(0,x),x-frozen);
 const a=p.locator('#mg-'+ready.row+'-a');await a.dblclick({delay:120});
 await p.locator('#mg-input [name=value]').fill(String(Math.round(width+zoom)));const calculated=p.waitForResponse(r=>r.url().includes('luu-json/')&&r.request().method()==='POST');await p.locator('#mg-input [name=value]').press('Enter');assert.equal((await calculated).status(),200);
 data=await (await ctx.request.get(base+url+'du-lieu/')).json();assert.equal(Number(data.rows.find(r=>r.id===ready.row).cells.total.value),Math.round(width+zoom)+2);
 // Bấm Escape bỏ nội dung đang gõ. Composition dưới đây là mô phỏng.
 await a.dblclick({delay:120});await p.locator('#mg-input [name=value]').fill('999');await p.keyboard.press('Escape');
 await p.locator('#mg-viewport').evaluate(v=>v.scrollLeft=0);
 await original.dblclick({delay:120});await p.locator('#mg-input [name=value]').dispatchEvent('compositionstart');await p.locator('#mg-input [name=value]').fill('Tiếng Việt');await p.locator('#mg-input [name=value]').dispatchEvent('compositionend');await p.keyboard.press('Escape');
 await p.screenshot({path:path.join(root,'shared-'+width+'-'+zoom+'.png'),fullPage:true});
 await p.locator('#mg-viewport').evaluate(v=>v.scrollLeft=0);await p.locator('[data-filter="bill"]').click();await p.locator('#mg-column-filter-body form').waitFor();
 // Manager xóa bảng; tab Staff đang nóng phải xóa nội dung sau request kế tiếp.
 const manager=await browser.newContext({viewport:{width,height:900}});const m=await manager.newPage();
 await m.goto(base+'/dang-nhap/');await m.locator('[name=username]').fill('manager_mkt');await m.locator('[name=password]').fill('matkhau-kiem-thu-1');await Promise.all([m.waitForURL(u=>!u.pathname.includes('dang-nhap')),m.locator('button[type=submit]').click()]);
 await m.goto(base+url+'xoa-bang/');await m.locator('[name=name]').fill(ready.name);await Promise.all([m.waitForURL('**/bang-da-xoa/'),m.getByRole('button',{name:'Xóa bảng',exact:true}).click()]);
 await p.waitForFunction(()=>document.querySelectorAll('.mg-cell').length===0&&document.querySelector('#mg-message').textContent.includes('Quyền'),null,{timeout:20000});
 assert.equal((await ctx.request.get(base+url+'du-lieu/')).status(),403);
 assert(await p.locator('#hop-loc').evaluate(e=>e.hidden),'Bảng bị xóa phải đóng popup chứa dữ liệu lọc');assert.equal(await p.locator('#mg-column-filter-body').textContent(),'');
 await m.screenshot({path:path.join(root,'deleted-'+width+'-'+zoom+'.png')});
 await m.getByRole('button',{name:'Khôi phục '+ready.name,exact:true}).click();await p.reload();await p.waitForFunction(()=>window.KNJSC_MASTER?.diagnostics().total>0);await manager.close();result.cases.push({width,zoom,zoomEvidence,create:true,undoRedo:true,clipboardLeadingZeros:true});await ctx.close();
}
assert.equal(result.errors.length,0);result.ok=true;
}catch(e){for(const c of contexts)for(const p of c.pages()){await p.screenshot({path:path.join(root,'shared-failure.png')}).catch(()=>{});result.errors.push(await p.locator('#mg-message').innerText().catch(()=>''));}result.errors.push(e.stack);process.exitCode=1;}finally{fs.writeFileSync(path.join(root,'shared-browser-result.json'),JSON.stringify(result,null,2));await Promise.all(contexts.map(c=>c.close().catch(()=>{})));await browser.close();console.log(JSON.stringify({ok:result.ok,cases:result.cases,errors:result.errors}));}})();
