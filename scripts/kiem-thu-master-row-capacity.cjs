const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('assert/strict');
const out=path.resolve(__dirname,'../.agents/design-state/review/master'),sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});try{
for(const count of [100000,300000]){
 const marker=path.join(out,'row-capacity-ready.json'),result=path.join(out,'row-capacity-result.json');
 for(let i=0;i<600&&(!fs.existsSync(marker)||fs.existsSync(result));i++)await sleep(500);
 const m=JSON.parse(fs.readFileSync(marker));assert.equal(m.rows,count);const base='http://127.0.0.1:'+m.port;
 const context=await browser.newContext({viewport:{width:1440,height:900}});await context.addCookies([{name:'sessionid',value:m.session,url:base}]);
 const page=await context.newPage(),cdp=await context.newCDPSession(page),errors=[],requests=[];let writes=0;
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.url().includes('/du-lieu/'))requests.push(r.url());if(r.url().includes('luu-json'))writes++;});
 try{
  await page.goto(base+'/bang-tinh/van_don_moi/');await page.locator('.mg-cell[data-id]').first().waitFor();
  assert.equal((await page.evaluate(()=>window.KNJSC_MASTER.diagnostics())).total,count);
  await page.evaluate(()=>{window.rowTimings=[];document.addEventListener('pointermove',e=>{if(!(e.buttons&1)||!document.querySelector('.mg-resizing-row'))return;const start=performance.now();requestAnimationFrame(()=>requestAnimationFrame(()=>requestAnimationFrame(()=>rowTimings.push(performance.now()-start))));},true);});
  const before=requests.length,b=await page.locator('[data-row-resize="0"]').boundingBox();
  await page.mouse.move(b.x+20,b.y+3);await page.mouse.down();
  for(let i=0;i<30;i++){await page.mouse.move(b.x+20,b.y+3+(i%2?100:132));await page.evaluate(()=>new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(()=>requestAnimationFrame(done)))));}
  await page.mouse.up();await sleep(100);
  const timings=await page.evaluate(()=>rowTimings);assert(timings.length>=30);const sorted=[...timings].sort((a,b)=>a-b),p95=sorted[Math.ceil(sorted.length*.95)-1];
  assert(p95<=100,'Kéo hàng p95 vượt 100 ms');assert(requests.length-before<=1,'Kéo hàng không được phát request theo mỗi pointermove');assert.equal(writes,0);
  const scroll=[];
  for(let i=0;i<35;i++){
   const target=i===34?count-100:i*100;
   await page.locator('#mg-viewport').evaluate((e,r)=>e.scrollTop=r*28,target);await page.locator(`.mg-cell[data-r="${target}"][data-id]`).first().waitFor();
   if(i<5||i===34){
    const h=page.locator(`[data-row-resize="${target}"]`),hb=await h.boundingBox();
    if(hb&&hb.y>152&&hb.y<860){await page.mouse.move(hb.x+20,hb.y+3);await page.mouse.down();await page.mouse.move(hb.x+20,hb.y+63,{steps:3});await page.mouse.up();}
   }
   await cdp.send('HeapProfiler.collectGarbage');scroll.push(await page.evaluate(()=>({...window.KNJSC_MASTER.diagnostics(),heap:performance.memory.usedJSHeapSize,rows:document.querySelectorAll('.mg-row').length})));
  }
  assert(scroll.every(s=>s.cache<=10&&s.cells<1500));
  const tail=scroll.slice(15,34).map(s=>s.heap);assert(Math.max(...tail)-Math.min(...tail)<8*1024*1024,'Heap sau GC chưa ổn định');
  await page.locator('#mg-viewport').evaluate(e=>e.scrollTop=0);await page.locator('.mg-cell[data-r="0"][data-id]').first().waitFor();assert((await page.locator('.mg-row').first().boundingBox()).height>28);
  assert.deepEqual(errors,[]);const data={rows:count,viewport:[1440,900],samples:timings,p95,requests:requests.length,writes,scroll,errors};
  fs.writeFileSync(path.join(out,`row-height-${count}.json`),JSON.stringify(data,null,2));await page.screenshot({path:path.join(out,`row-height-${count}.png`)});
  fs.writeFileSync(result,JSON.stringify({ok:true}));console.log('PASS row capacity',count,'p95',p95,'cache',Math.max(...scroll.map(s=>s.cache)));
 }catch(error){fs.writeFileSync(result,JSON.stringify({ok:false,error:error.stack}));throw error;}finally{await context.close();}
}
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
