/* AC-24.5: Chrome riêng trên DB test; không thao tác máy đang dùng. */
const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),out=path.join(root,'.agents/design-state/review/optimization',process.env.OPT_BROWSER_STAGE?'browser-final':'browser');
const cases=[['before',100000,8038],['after',100000,8042],['before',300000,8040],['after',300000,8043]].filter(c=>!process.env.OPT_BROWSER_STAGE||c[0]===process.env.OPT_BROWSER_STAGE);
const frame=page=>page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
(async()=>{
 fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({channel:'chrome',headless:true});
 try{for(const [stage,count,port] of cases){
  const marker=JSON.parse(fs.readFileSync(path.join(root,`.test-runtime/${stage}${count/1000}/ready.json`)));
  assert(marker.database.startsWith('test_knjsc_opt_'));
  const base=`http://127.0.0.1:${port}`,context=await browser.newContext({viewport:{width:1440,height:900},recordVideo:{dir:out,size:{width:1440,height:900}},permissions:['clipboard-read','clipboard-write']});
  await context.addCookies([{name:'sessionid',value:marker.actors[0].session,url:base}]);
  const page=await context.newPage(),cdp=await context.newCDPSession(page),errors=[],requests=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.url().includes('/du-lieu/'))requests.push(r.url());});
  const source=fs.readFileSync(stage==='before'?'C:/KNJSC/CRM-Optimization-baseline/app/static/js/master-grid.js':path.join(root,'app/static/js/master-grid.js'),'utf8');
  assert(source.includes('scheduled = false; render();'));
  await page.route('**/master-grid.js*',route=>route.fulfill({contentType:'text/javascript',body:source.replace('scheduled = false; render();','scheduled = false; const start=performance.now(); render(); (window.renderSamples ||= []).push(performance.now()-start);')}));
  const result={stage,count,sourceSHA256:require('crypto').createHash('sha256').update(source).digest('hex'),errors,checks:[],samples:{},responsive:[]};
  try{
   await page.goto(base+'/bang-tinh/van_don_moi/');await page.locator('.mg-cell[data-r="0"][data-id]').first().waitFor();
   await page.evaluate(()=>{
    window.measured=[];window.sampleType='';
    const mark=()=>{if(!window.sampleType)return;const type=window.sampleType,start=performance.now();window.sampleType='';requestAnimationFrame(()=>requestAnimationFrame(()=>window.measured.push({type,ms:performance.now()-start})));};
    document.addEventListener('pointerdown',()=>{if(window.sampleType==='select')mark();},true);
    document.addEventListener('pointermove',()=>{if(window.sampleType.startsWith('resize'))mark();},true);
    document.addEventListener('beforeinput',()=>{if(window.sampleType==='typing')mark();},true);
   });
   for(let i=0;i<100;i++){
    await page.evaluate(()=>window.sampleType='select');
    await page.locator(`.mg-cell[data-r="${i%2}"][data-code="ten_khach"]`).click();await page.keyboard.press('Escape');await frame(page);
   }
   const cell=code=>page.locator(`.mg-cell[data-r="0"][data-code="${code}"]`);
   let release,started=false;const held=new Promise(r=>release=r);
   await page.route('**/luu-json/',async route=>{if(!started){started=true;await held;}await route.continue();});
   await cell('bang').dblclick({delay:120});
   const edit=page.locator('#mg-editor input');await edit.fill((await edit.inputValue())==='Đo giao diện A'?'Đo giao diện B':'Đo giao diện A');
   await page.keyboard.press('Tab');await page.keyboard.press('Escape');
   for(let n=0;n<100&&!started;n++)await page.waitForTimeout(50);assert(started);
   await cell('thanh_pho').dblclick({delay:120});
   for(let i=0;i<100;i++){await page.evaluate(()=>window.sampleType='typing');await page.keyboard.insertText('ư');await frame(page);}
   await page.keyboard.press('Escape');release();
   await page.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đã lưu');await page.unroute('**/luu-json/');
   for(const kind of ['column','row']){
    const selector=kind==='column'?'.mg-head [data-code="ten_khach"] [data-resize]':'[data-row-resize="0"]';
    if(kind==='row'){await page.locator(selector).focus();for(let n=0;n<18;n++)await page.keyboard.press('ArrowDown');}
    for(let i=0;i<100;i++){
     const b=await page.locator(selector).boundingBox(),x=b.x+b.width/2,y=b.y+b.height/2,d=i%2?-4:4;
     await page.mouse.move(x,y);await page.mouse.down();await page.evaluate(kind=>window.sampleType='resize-'+kind,kind);
     await page.mouse.move(x+(kind==='column'?d:0),y+(kind==='row'?d:0));await page.mouse.up();await frame(page);
    }
    if(kind==='row'){await page.locator(selector).focus();await page.keyboard.press('Home');}
   }
   result.samples=await page.evaluate(()=>Object.fromEntries(['select','typing','resize-column','resize-row'].map(type=>[type,window.measured.filter(s=>s.type===type).map(s=>s.ms)])));
   for(const [name,values] of Object.entries(result.samples))assert.equal(values.length,100,name);
   result.scroll=await page.evaluate(async()=>{
    const v=document.getElementById('mg-viewport'),wait=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
    v.scrollLeft=v.scrollTop=0;await wait();window.renderSamples=[];
    const nodes=[...document.querySelectorAll('.mg-head .mg-corner,.mg-head .mg-pinned,.mg-row[aria-rowindex="2"] .mg-number,.mg-row[aria-rowindex="2"] .mg-pinned')];
    const x=nodes.map(n=>n.getBoundingClientRect().left),drift=[],long=[];
    const observer=new PerformanceObserver(list=>long.push(...list.getEntries().map(e=>e.duration)));observer.observe({type:'longtask'});
    for(let i=0;i<120;i++){const n=i%40,p=n<=20?n/20:(40-n)/20;v.scrollLeft=(v.scrollWidth-v.clientWidth)*p;v.scrollTop=i%2?28:0;
      drift.push(Math.max(...nodes.map((node,j)=>Math.abs(node.getBoundingClientRect().left-x[j]))));await wait();}
    observer.disconnect();return {drift,long,render:window.renderSamples};
   });
   assert(Math.max(...result.scroll.drift)<=1,'Ghim trong lúc cuộn');
   result.memory=[];
   for(let cycle=0;cycle<2;cycle++)for(let block=0;block<12;block++){
    const row=block*200;
    await page.locator('#mg-viewport').evaluate((v,row)=>{v.scrollTop=row*28;v.scrollLeft=0;},row);
    await page.locator(`.mg-cell[data-r="${row}"][data-id]`).first().waitFor();await cdp.send('HeapProfiler.collectGarbage');
    const metrics=await cdp.send('Performance.getMetrics');
    result.memory.push({...await page.evaluate(()=>({...KNJSC_MASTER.diagnostics(),dom:document.getElementById('mg-canvas').querySelectorAll('*').length,heap:performance.memory.usedJSHeapSize})),cdpHeap:metrics.metrics.find(m=>m.name==='JSHeapUsedSize')?.value});
   }
   assert(result.memory.every(m=>m.cache<=10&&m.cells<1500),'Cache/DOM hữu hạn');
   for(const [width,zoom] of [[1440,1],[1280,1],[390,1],[1440,1.25]]){
    await page.setViewportSize({width,height:900});await page.evaluate(zoom=>{document.documentElement.style.zoom=String(zoom);const v=document.getElementById('mg-viewport');v.scrollTop=v.scrollLeft=0;},zoom);await frame(page);
    const check=await page.evaluate(async()=>{const v=document.getElementById('mg-viewport'),nodes=[...document.querySelectorAll('.mg-head .mg-pinned')],x=nodes.map(n=>n.getBoundingClientRect().left),drift=[];
      for(let i=0;i<10;i++){v.scrollLeft=i%2?v.scrollWidth:0;drift.push(Math.max(0,...nodes.map((n,j)=>Math.abs(n.getBoundingClientRect().left-x[j]))));await new Promise(r=>requestAnimationFrame(r));}
      return {drift,pinned:nodes.length,overflow:document.documentElement.scrollWidth>innerWidth};});
    assert(Math.max(...check.drift)<=1&&!check.overflow);result.responsive.push({width,cssZoom:zoom,...check});
    await page.screenshot({path:path.join(out,`${stage}-${count}-${width}-${zoom}.png`)});
   }
   result.requests=requests.length;result.ok=true;assert.deepEqual(errors,[]);
  }catch(e){result.ok=false;result.error=e.stack;await page.screenshot({path:path.join(out,`${stage}-${count}-failure.png`)});throw e;}
  finally{await context.close();result.video=await page.video()?.path();fs.writeFileSync(path.join(out,`${stage}-${count}.json`),JSON.stringify(result,null,2));}
  console.log('BROWSER',stage,count,'đạt');
 }}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
