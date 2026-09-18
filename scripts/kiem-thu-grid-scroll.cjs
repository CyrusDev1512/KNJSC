/* Chrome + template thật; API mô phỏng có độ trễ cố định để tách chi phí vẽ.
 * Xuất fixture bằng GRID_SCROLL_FIXTURE=1 trên database pytest riêng trước.
 * Không chứng minh thông lượng API/VPS; không đọc/ghi dữ liệu khách hàng. */
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('node:assert/strict');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),folder=path.join(root,'storage/grid-scroll');
const baseline=process.argv.includes('--baseline'),optimized=process.argv.includes('--render-flag');
const jump=process.argv.includes('--jump'),jumpBaseline=process.argv.includes('--jump-baseline');
const stage=jumpBaseline?'jump-before':jump?'jump-after':baseline?'before':optimized?'compat-render':'after';
const fixture=JSON.parse(fs.readFileSync(path.join(folder,'fixture.json')));
const source=fs.readFileSync(jumpBaseline?path.join(folder,'jump-baseline.js'):baseline?path.join(folder,'baseline.js'):path.join(root,'app/static/js/master-grid.js'),'utf8');
const html=fs.readFileSync(path.join(folder,'fixture.html'),'utf8').replace('"renderOptimized": false',`"renderOptimized": ${optimized}`);
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const percentile=(a,p)=>a.slice().sort((a,b)=>a-b)[Math.min(a.length-1,Math.floor(a.length*p))];
const summary=a=>({samples:a.length,p50:percentile(a,.5),p95:percentile(a,.95),max:Math.max(...a)});
const server=http.createServer((req,res)=>{
 const u=new URL(req.url,'http://localhost');
 if(u.pathname.startsWith('/static/')){
  const p=path.resolve(root,'app',u.pathname.slice(1));
  if(!p.startsWith(path.join(root,'app/static')+path.sep)||!fs.existsSync(p)){res.writeHead(404);return res.end();}
  res.setHeader('Content-Type',p.endsWith('.js')?'text/javascript':p.endsWith('.css')?'text/css':'image/svg+xml');
  return res.end(p.endsWith(path.sep+'master-grid.js')?source.replace(/scheduled = false; render\((scrollPaint)?\);/,(_,arg)=>`scheduled = false; const started=performance.now(); render(${arg||''}); (window.renderTimes ||= []).push(performance.now()-started);`):fs.readFileSync(p));
 }
 res.setHeader('Content-Type','text/html');res.end(html);
});
async function main(){
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const base=`http://127.0.0.1:${server.address().port}`;
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const results=[];
 try{for(const width of [1440,390]){
  const context=await browser.newContext({viewport:{width,height:900}}),page=await context.newPage();
  const errors=[],requests=[];let slowOffset=null,failOffset=null,scopeDenied=false;
  page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>{window.longTasks=[];new PerformanceObserver(l=>longTasks.push(...l.getEntries().map(e=>({start:e.startTime,ms:e.duration})))).observe({type:'longtask',buffered:true});});
  await page.route('**/*',async route=>{
   const url=new URL(route.request().url());
   if(url.origin!==base)return route.abort();
   if(url.pathname.endsWith('/du-lieu/')){
    const offset=Number(url.searchParams.get('offset')||0),entry={offset,start:Date.now(),end:null};requests.push(entry);
    await wait(offset===slowOffset?650:120);
    if(scopeDenied)return route.fulfill({status:403,contentType:'application/json',body:JSON.stringify({error:'Ngoài quyền test'})});
    if(offset===failOffset)return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:'Lỗi mạng test'})});
    const marker=url.searchParams.get('tim')==='new'?200000:0;
    const rows=Array.from({length:Math.min(100,100000-offset)},(_,i)=>{
     const row=structuredClone(fixture.rows[0]);row.id=offset+i+1+marker;
     row.cells.ma_don={...row.cells.ma_don,value:`QA-${row.id}`,display:`QA-${row.id}`};
     row.cells.ten_khach={...row.cells.ten_khach,value:`Khách thử ${row.id}`,display:`Khách thử ${row.id}`};return row;
    });
    entry.end=Date.now();return route.fulfill({contentType:'application/json',body:JSON.stringify({...fixture,total:100000,rows})});
   }
   if(url.pathname.endsWith('/moi-nhat/'))return route.fulfill({contentType:'application/json',body:'{}'});
   if(route.request().method()==='POST'){
    const input=route.request().postDataJSON();
    if(input.ids)return route.fulfill({contentType:'application/json',body:JSON.stringify({visible:input.ids})});
    return route.fulfill({status:503,contentType:'application/json',body:'{"error":"Không ghi dữ liệu trong phép đo cuộn"}'});
   }
   return route.continue();
  });
  await page.goto(base+'/bang-tinh/van_don/');await page.locator('.mg-cell[data-id="1"]').first().waitFor();
  const cdp=await context.newCDPSession(page);await cdp.send('Performance.enable');
  // Đợi toàn bộ vùng nhìn có dữ liệu; rAF chỉ là cơ hội trình duyệt paint,
  // không gọi đây là phép đo photon/display hardware.
  async function scroll(top){return page.evaluate(async top=>{
   const v=document.getElementById('mg-viewport'),start=performance.now();v.scrollTop=top;
   return await new Promise((resolve,reject)=>{
    const row=Math.floor(top/28),last=Math.min(99999,Math.floor((top+v.clientHeight-54-1)/28)),deadline=start+4000;
    function check(){
     const ready=Array.from({length:last-row+1},(_,i)=>document.querySelector(`.mg-cell[data-r="${row+i}"][data-id]`)).every(Boolean);
     if(ready)return requestAnimationFrame(()=>resolve(performance.now()-start));
     if(performance.now()>deadline)return reject(Error('Dòng đích chưa hiển thị'));requestAnimationFrame(check);
    }requestAnimationFrame(check);
   });
  },top);}
  if(jump||jumpBaseline){
   await page.waitForTimeout(350);const first=requests.length;
   // Mô phỏng kéo thumb qua 12 vùng xa, không đợi API từng vùng.
   for(let i=1;i<=12;i++){
    await page.locator('#mg-viewport').evaluate((v,i)=>v.scrollTop=i*1000*28,i);await page.waitForTimeout(25);
   }
   const latency=await scroll(12000*28);await page.waitForTimeout(250);
   const sent=requests.slice(first).map(r=>r.offset),cachedStart=requests.length;
   const cached=await scroll(12000*28+28);await page.waitForTimeout(130);
   const cachedRequests=requests.length-cachedStart;
   assert.equal(await page.locator('.mg-cell[data-r="12001"]').first().getAttribute('data-id'),'12002');
   const result={width,stage,requests:sent.length,offsets:sent,finalWaitMs:latency,cachedMs:cached,cachedRequests,errors};results.push(result);
   if(!jumpBaseline){assert(sent.length<=2,JSON.stringify(result));assert(sent.every(n=>n>=11900&&n<=12000));assert.equal(cachedRequests,0);}
   // Cache ở hai đầu không phải đợi timer gom nhảy và không phát request.
   await scroll(0);await page.waitForTimeout(250);await scroll(12000*28);await page.waitForTimeout(130);
   const warmStart=requests.length;const warmJump=await scroll(0);await page.waitForTimeout(130);
   result.warmJumpMs=warmJump;result.warmJumpRequests=requests.length-warmStart;
   if(!jumpBaseline)assert.equal(result.warmJumpRequests,0);
   // Sau nhảy, tải đón chỉ trở lại khi cuộn nhỏ liên tục cùng hướng.
   await scroll(50000*28);await page.waitForTimeout(150);const aheadStart=requests.length;
   await scroll(50012*28);await page.waitForTimeout(25);await scroll(50024*28);await page.waitForTimeout(250);
   result.resumedOffsets=requests.slice(aheadStart).map(r=>r.offset);
   if(!jumpBaseline)assert(result.resumedOffsets.includes(50100)&&result.resumedOffsets.includes(50200));
   // Đổi bộ lọc khi timer nhảy còn đang chờ: không được tải vị trí cũ.
   await page.locator('#mg-viewport').evaluate(v=>v.scrollTop=70000*28);
   await page.locator('#mg-search input').fill('new');await page.locator('#mg-search button').click();
   await page.locator('.mg-cell[data-id="200001"]').first().waitFor();await page.waitForTimeout(200);
   assert.equal(await page.locator('.mg-cell[data-id="70001"]').count(),0);
   result.filterReset=true;assert.equal(errors.length,0);
   await context.close();continue;
  }
  await scroll(110*28);await scroll(0);await page.waitForTimeout(250);
  // Hồi quy: header/ô vẫn là cùng node, cuộn cached không dựng lại cây ô cũ.
  await page.evaluate(()=>{
   window.created=0;const create=document.createElement.bind(document);document.createElement=(...args)=>{window.created++;return create(...args)};
   window.headerBefore=document.querySelector('.mg-head');window.cellBefore=document.querySelector('.mg-cell[data-r="20"]');
  });
  const cached=[];for(let i=0;i<40;i++)cached.push(await scroll((i%2?18:19)*28));
  const reuse=await page.evaluate(()=>({created,headerSame:headerBefore===document.querySelector('.mg-head'),cellSame:cellBefore===document.querySelector('.mg-cell[data-r="20"]')}));
  // Đo scrollTop cùng bước/cadence; kiểm wheel native riêng bên dưới.
  await page.reload();await page.locator('.mg-cell[data-id="1"]').first().waitFor();await page.waitForTimeout(300);
  await page.locator('#mg-viewport').hover();const continuous=[],networkBefore=requests.length,trace=[];
  cdp.on('Tracing.dataCollected',event=>trace.push(...event.value));
  await cdp.send('Tracing.start',{categories:'devtools.timeline,blink.user_timing',transferMode:'ReportEvents'});
  for(let i=1;i<=55;i++){continuous.push(await scroll(i*12*28));await page.waitForTimeout(25);}
  const traceDone=new Promise(resolve=>cdp.once('Tracing.tracingComplete',resolve));await cdp.send('Tracing.end');await traceDone;
  fs.writeFileSync(path.join(folder,`${stage}-${width}-trace.json`),JSON.stringify({traceEvents:trace}));
  const bounded=await page.evaluate(()=>KNJSC_MASTER.diagnostics());
  const sequential=requests.slice(networkBefore),prefetched=sequential.some(r=>r.offset>=700);
  // Đi xa/quay lại/đổi hướng, dữ liệu phải đúng ID; cache giữ trần 10.
  for(const r of [4000,2000,400,10,0]){await scroll(r*28);assert.equal(await page.locator(`.mg-cell[data-r="${r}"]`).first().getAttribute('data-id'),String(r+1));}
  const final=await page.evaluate(()=>({...KNJSC_MASTER.diagnostics(),longTasks,renderTimes:window.renderTimes||[]}));
  assert(final.cache<=10);assert(final.cells<2000);assert.equal(errors.length,0);
  const metrics=await cdp.send('Performance.getMetrics');
  // Cuộn wheel liên tục, không đợi từng request/khung hình hoàn thành.
  await page.reload();await page.locator('.mg-cell[data-id="1"]').first().waitFor();await page.waitForTimeout(300);
  await page.evaluate(()=>{
   window.wheelProbe={run:true,frames:0,missingFrames:0,gaps:[],start:null};
   function sample(now){const p=wheelProbe;if(!p.run)return;const v=document.getElementById('mg-viewport'),first=Math.floor(v.scrollTop/28),last=Math.floor((v.scrollTop+v.clientHeight-55)/28);
    const ready=Array.from({length:last-first+1},(_,i)=>document.querySelector(`.mg-cell[data-r="${first+i}"][data-id]`)).every(Boolean);
    p.frames++;if(!ready){p.missingFrames++;if(p.start===null)p.start=now;}else if(p.start!==null){p.gaps.push(now-p.start);p.start=null;}requestAnimationFrame(sample);
   }requestAnimationFrame(sample);
  });
  await page.locator('#mg-viewport').hover();
  for(let i=0;i<50;i++){await page.mouse.wheel(0,240);await page.waitForTimeout(35);}
  await page.waitForTimeout(250);
  const wheel=await page.evaluate(()=>{wheelProbe.run=false;return {...wheelProbe,top:document.getElementById('mg-viewport').scrollTop}});
  results.push({width,stage,apiDelayMs:120,total:100000,cached:summary(cached),continuous:summary(continuous),wheel,reuse,prefetched,bounded,final,requests:requests.map(r=>({offset:r.offset,ms:r.end===null?null:r.end-r.start})),metrics:metrics.metrics.filter(m=>['TaskDuration','LayoutDuration','RecalcStyleDuration','JSHeapUsedSize','Nodes'].includes(m.name)),errors});
  if(!baseline){
   assert(reuse.created<3000,`Cuộn cached dựng ${reuse.created} nodes`);assert(reuse.headerSame&&reuse.cellSame);assert(prefetched,'Chưa tải trước theo hướng cuộn');
   await scroll(0);await page.waitForTimeout(150);
   // Scroll thật + ngang: selection giữ nguyên và editor vẫn nhập được.
   await page.locator('.mg-cell[data-r="0"][data-code="ten_khach"]').click();
   await page.waitForFunction(()=>document.getElementById('mg-selection').textContent.includes('1 ô được chọn'));
   const selection=await page.locator('#mg-selection').textContent();
   await page.mouse.wheel(0,500);await page.waitForTimeout(100);assert((await page.locator('#mg-viewport').evaluate(e=>e.scrollTop))>0);
   await page.mouse.wheel(500,0);await page.waitForTimeout(100);
   assert.equal(await page.locator('#mg-selection').textContent(),selection);
   await page.locator('#mg-viewport').evaluate(e=>{e.scrollTop=0;e.scrollLeft=0});await page.waitForTimeout(100);
   await page.locator('.mg-cell[data-r="0"][data-code="ten_khach"]').dblclick({delay:100});
   await page.locator('#mg-input [name=value]').fill('Nháp cuộn');
   await page.mouse.wheel(0,300);await page.waitForTimeout(100);
   assert.equal(await page.locator('#mg-input [name=value]').inputValue(),'Nháp cuộn');await page.keyboard.press('Escape');
   await page.locator('#mg-viewport').evaluate(e=>{e.scrollTop=0;e.scrollLeft=0});await page.waitForTimeout(80);
   const heightHandle=page.locator('[data-row-resize="0"]');await heightHandle.focus();await heightHandle.press('ArrowDown');
   await page.waitForTimeout(80);assert.equal(await heightHandle.getAttribute('aria-valuenow'),'32');
   await page.mouse.wheel(0,50);await page.waitForTimeout(80);await page.mouse.wheel(0,-50);await page.waitForTimeout(80);
   assert.equal(await heightHandle.getAttribute('aria-valuenow'),'32');await heightHandle.focus();await heightHandle.press('Home');
   await page.waitForTimeout(80);assert.equal(await heightHandle.getAttribute('aria-valuenow'),'28');
   // Request cũ chậm không được trộn dữ liệu khi đổi lọc.
   slowOffset=100;await page.reload();await page.locator('.mg-cell[data-id="1"]').first().waitFor();
   await page.locator('#mg-search input').fill('new');await page.locator('#mg-search button').click();
   await page.locator('.mg-cell[data-id="200001"]').first().waitFor();await page.waitForTimeout(750);
   assert.equal(await page.locator('.mg-cell[data-id="1"]').count(),0);slowOffset=null;
   // Tải đón lỗi không chặn cache; khi thật sự xem vùng lỗi vẫn phải báo.
   failOffset=200;await page.goto(base+'/bang-tinh/van_don/');await page.locator('.mg-cell[data-id="1"]').first().waitFor();await page.waitForTimeout(350);
   assert(await page.locator('#mg-message').isHidden());
   await page.locator('#mg-viewport').evaluate(e=>e.scrollTop=220*28);
   await page.locator('#mg-message').filter({hasText:'Lỗi mạng test'}).waitFor();
   failOffset=null;await page.getByRole('button',{name:'Tải lại vùng đang xem',exact:true}).click();
   await page.locator('.mg-cell[data-r="220"][data-id]').first().waitFor();
   // 403 kể cả từ tải đón phải gỡ dữ liệu; không âm thầm giữ cache ngoài quyền.
   scopeDenied=true;await page.locator('#mg-viewport').evaluate(e=>e.scrollTop=5000*28);
   await page.locator('#mg-message').filter({hasText:'Ngoài quyền test'}).waitFor();
   assert.equal(await page.locator('.mg-cell[data-id]').count(),0);
   results.at(-1).regressions=['wheel/selection','editor draft','variable row height','stale filter response','speculative 503','visible retry','403 clears cache'];
  }
  await context.close();
 }}finally{await browser.close();server.close();fs.writeFileSync(path.join(folder,stage+'.json'),JSON.stringify(results,null,2));}
 console.log(JSON.stringify(jump||jumpBaseline?results:results.map(({width,cached,continuous,reuse,prefetched})=>({width,cached,continuous,reuse,prefetched}))));
}
main().catch(e=>{console.error(e);server.close();process.exitCode=1;});
