const fs=require('fs'),path=require('path'),assert=require('assert'),{chromium}=require('playwright');
const dir=process.env.LOAD_DIR,stage=process.env.LOAD_STAGE,base='http://127.0.0.1:8853',manifest=JSON.parse(fs.readFileSync(path.join(dir,'ready.json')));
(async()=>{const evidence=process.env.LOAD_RESUME==='1'?JSON.parse(fs.readFileSync(path.join(dir,`browser-${stage}.json`))):{stage,rows:manifest.rows,cases:[],errors:[]},contexts=[];try{
 for(const [width,zoom] of JSON.parse(process.env.LOAD_CASES||'[[1440,1],[1280,1],[390,1],[1440,1.25]]')){
  const ctx=await chromium.launchPersistentContext(path.join(dir,`chrome-${stage}-${width}-${zoom}`),{channel:'chrome',headless:true,viewport:{width,height:900}});contexts.push(ctx);
  const page=await ctx.newPage();page.setDefaultTimeout(20000);page.on('pageerror',e=>evidence.errors.push(e.message));page.on('console',m=>{if(m.type()==='error')evidence.errors.push('Console: '+m.text());});page.on('response',r=>{if(r.url().includes('/static/')&&r.status()>=400)evidence.errors.push('Static '+r.status()+' '+r.url());});
  if(zoom!==1){await page.goto('chrome://settings/appearance');await page.locator('#zoomLevel').selectOption(String(zoom));}
  await ctx.addCookies([{name:'sessionid',value:manifest.actors[59].session,url:base},{name:'csrftoken',value:manifest.csrf,url:base}]);
  const begin=performance.now();await page.goto(base+'/bang-tinh/van_don/');await page.waitForFunction(()=>window.htmx);
  if(stage==='after')await page.waitForFunction(()=>window.KNJSC_MASTER?.diagnostics().total>0);else await page.locator('#luoi-vd td[data-dong]').first().waitFor();
  const sample={width,zoom,load:performance.now()-begin,selection:[],scroll:[],input:[],pin:[],checkpoints:[]};
  const selector=stage==='after'?'#mg-viewport':'#luoi-vd',view=page.locator(selector);
  const first=stage==='after'?page.locator('.mg-cell[data-code="ma_don"]').first():page.locator('#luoi-vd td[data-cot="ma_don"]').first();await first.click();
  for(let i=0;i<100;i++){const t=performance.now();await page.keyboard.press(i%2?'ArrowLeft':'ArrowRight');await page.evaluate(()=>new Promise(r=>requestAnimationFrame(r)));sample.selection.push(performance.now()-t);}
  const pinSelector=stage==='after'?'.mg-heading.mg-pinned':'#luoi-vd thead .co-dinh';
  const pinned=await page.locator(pinSelector).first().boundingBox();
  for(let i=0;i<100;i++){
   const t=performance.now();await view.evaluate((v,i)=>{v.scrollTop=100+i*420;v.scrollLeft=i%2?180:0;},i);await page.evaluate(()=>new Promise(r=>requestAnimationFrame(r)));sample.scroll.push(performance.now()-t);
   const current=await page.locator(pinSelector).first().boundingBox();sample.pin.push(Math.abs(current.x-pinned.x));
   if(stage==='after'&&i%10===0)sample.checkpoints.push(await page.evaluate(()=>({...window.KNJSC_MASTER.diagnostics(),heap:performance.memory?.usedJSHeapSize,dom:document.querySelectorAll('*').length})));
  }
  await view.evaluate(v=>{v.scrollTop=0;v.scrollLeft=v.scrollWidth});await page.waitForTimeout(500);
  if(stage==='after'){
   const columns=await page.evaluate(async()=>{const config=JSON.parse(document.getElementById('mg-config').textContent);return (await fetch(config.dataUrl).then(r=>r.json())).columns;});
   const x=46+columns.slice(0,columns.findIndex(c=>c.code==='ghi_chu')).reduce((sum,c)=>sum+c.width,0);
   const frozen=await page.locator('.mg-heading.mg-pinned').evaluateAll(cols=>46+cols.reduce((sum,c)=>sum+c.getBoundingClientRect().width,0));
   await view.evaluate((v,x)=>v.scrollLeft=Math.max(0,x),x-frozen);await page.waitForTimeout(100);
  }
  const target=stage==='after'?page.locator('.mg-cell[data-r="0"][data-code="ghi_chu"]'):page.locator('#luoi-vd tbody td[data-cot="ghi_chu"]').first();
  for(let i=0;i<100;i++){
   await target.dblclick({delay:120});const input=stage==='after'?page.locator('#mg-input [name=value]'):page.locator('#luoi-vd td.dang-sua textarea, #luoi-vd td.dang-sua input[name=gia_tri]');await input.waitFor();
   const t=performance.now();await input.press('x');await page.evaluate(()=>new Promise(r=>requestAnimationFrame(r)));sample.input.push(performance.now()-t);await input.press('Escape');await target.waitFor();
  }
  sample.memory=await page.evaluate(()=>performance.memory?{used:performance.memory.usedJSHeapSize,total:performance.memory.totalJSHeapSize}:null);
  if(stage==='after'){sample.final=await page.evaluate(()=>window.KNJSC_MASTER.diagnostics());assert(sample.checkpoints.every(v=>v.cache<=10&&v.cells<=1500));}
  sample.zoomEvidence=await page.evaluate(()=>({dpr:devicePixelRatio,css:getComputedStyle(document.documentElement).zoom,scale:visualViewport.scale}));if(zoom!==1)assert.equal(sample.zoomEvidence.dpr,1.25);
  await page.screenshot({path:path.join(dir,`browser-${stage}-${width}-${zoom}.png`)});evidence.cases.push(sample);fs.writeFileSync(path.join(dir,`browser-${stage}-progress.json`),JSON.stringify(evidence,null,2));console.log(JSON.stringify({stage,width,zoom,completed:true}));await ctx.close();
 }
}catch(error){evidence.errors.push(error.stack);for(const c of contexts)for(const p of c.pages())await p.screenshot({path:path.join(dir,`browser-${stage}-failure.png`)}).catch(()=>{});process.exitCode=1;
}finally{fs.writeFileSync(path.join(dir,`browser-${stage}.json`),JSON.stringify(evidence,null,2));await Promise.all(contexts.map(c=>c.close().catch(()=>{})));console.log(JSON.stringify({stage,cases:evidence.cases.length,errors:evidence.errors}));}})();
