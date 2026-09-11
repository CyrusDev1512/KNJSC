/* So sánh snapshot trước sửa và working tree trên cùng fixture; không thay runtime server. */
const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const out=path.resolve(process.env.PINNED_EVIDENCE||'.agents/design-state/review/pinned-20260911'),sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});try{
 for(const count of [100000,300000]){
  const marker=path.join(out,'row-capacity-ready.json'),done=path.join(out,'row-capacity-result.json');let m;
  for(let i=0;i<600;i++){if(fs.existsSync(marker)&&!fs.existsSync(done)){m=JSON.parse(fs.readFileSync(marker));if(m.rows===count)break;}await sleep(500);}assert.equal(m?.rows,count);
  for(const phase of ['before','after']){
   const base='http://127.0.0.1:'+m.port,context=await browser.newContext({viewport:{width:1440,height:900}});await context.addCookies([{name:'sessionid',value:m.session,url:base}]);
   const page=await context.newPage(),cdp=await context.newCDPSession(page),requests=[];
   await page.route('**/master-grid.js*',route=>{
    const source=fs.readFileSync(phase==='before'?path.join(out,'before.js'):'app/static/js/master-grid.js','utf8'),needle='scheduled = false; render();';assert(source.includes(needle));
    return route.fulfill({contentType:'text/javascript',body:source.replace(needle,'scheduled = false; const t=performance.now(); render(); (window.renderSamples ||= []).push(performance.now()-t);')});
   });
   if(phase==='before')await page.route('**/master-grid.css*',route=>route.fulfill({contentType:'text/css',body:fs.readFileSync(path.join(out,'before.css'),'utf8')}));
   page.on('request',r=>{if(r.url().includes('/du-lieu/'))requests.push(r.url());});
   await page.goto(base+'/bang-tinh/van_don_moi/');await page.locator('.mg-cell[data-r="0"][data-id]').first().waitFor();
   const measured=await page.evaluate(async()=>{
    const v=document.getElementById('mg-viewport'),frame=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))),long=[];
    await frame();window.renderSamples=[];const observer=new PerformanceObserver(l=>long.push(...l.getEntries().map(e=>e.duration)));observer.observe({type:'longtask'});
    const selectors=['.mg-corner','.mg-number','.mg-head [data-code="ma_don"]','.mg-head [data-code="ten_khach"]','.mg-head [data-code="so_dien_thoai"]',...['ma_don','ten_khach','so_dien_thoai'].map(c=>'.mg-cell[data-r="0"][data-code="'+c+'"]')];
    const x=selectors.map(s=>document.querySelector(s).getBoundingClientRect().left),drift=[];
    for(let i=0;i<120;i++){
     const n=i%40,p=n<=20?n/20:(40-n)/20;v.scrollLeft=(v.scrollWidth-v.clientWidth)*p;v.scrollTop=i%2?28:0;
     drift.push(Math.max(...selectors.map((s,j)=>Math.abs(document.querySelector(s).getBoundingClientRect().left-x[j]))));await frame();
    }
    observer.disconnect();return {render:window.renderSamples,long,drift};
   });
   const memory=[];
   for(let cycle=0;cycle<2;cycle++)for(let b=0;b<12;b++){
    const row=b*200;await page.locator('#mg-viewport').evaluate((v,r)=>{v.scrollTop=r*28;v.scrollLeft=0;},row);await page.locator(`.mg-cell[data-r="${row}"][data-id]`).first().waitFor();
    await cdp.send('HeapProfiler.collectGarbage');memory.push(await page.evaluate(()=>({...KNJSC_MASTER.diagnostics(),heap:performance.memory.usedJSHeapSize,dom:document.getElementById('mg-canvas').querySelectorAll('*').length})));
   }
   assert(memory.every(s=>s.cache<=10&&s.cells<1500));if(phase==='after')assert(Math.max(...measured.drift)<=1);
   fs.writeFileSync(path.join(out,`profile-${phase}-${count}.json`),JSON.stringify({count,phase,...measured,memory,requests:requests.length},null,2));console.log('PROFILE',phase,count,'drift',Math.max(...measured.drift),'requests',requests.length);await context.close();
  }
  fs.writeFileSync(done,JSON.stringify({ok:true}));
 }
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
