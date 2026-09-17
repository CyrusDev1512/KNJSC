/* Chrome đo riêng từng snapshot/dataset do pytest test_master_capacity cấp. */
const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('assert/strict');
const out=path.resolve(__dirname,'../.agents/design-state/review/master'),sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 try{for(let run=0;run<Number(process.env.MASTER_BROWSER_RUNS||4);run++){
   const marker=path.join(out,'capacity-browser-ready.json'),result=path.join(out,'capacity-browser-result.json');
   for(let n=0;n<900&&(!fs.existsSync(marker)||fs.existsSync(result));n++)await sleep(500);
   assert(fs.existsSync(marker),'Thiếu server capacity trên DB test');
   const m=JSON.parse(fs.readFileSync(marker)),base='http://127.0.0.1:'+m.port;
   const context=await browser.newContext({viewport:{width:1440,height:900}});
   await context.addCookies([{name:'sessionid',value:m.session,url:base}]);const page=await context.newPage(),errors=[];
   page.on('pageerror',e=>errors.push(e.message));
   const cdp=await context.newCDPSession(page);
   try{
     await page.addInitScript(()=>{window.longTasks=[];new PerformanceObserver(list=>window.longTasks.push(...list.getEntries().map(e=>e.duration))).observe({type:'longtask',buffered:true});});
     const start=Date.now();await page.goto(base+'/bang-tinh/van_don_moi/?moi_trang=100');
     const selector=m.stage==='after'?'.mg-cell[data-id]':'#luoi-vd td[id]';await page.locator(selector).first().waitFor();
     const metrics={stage:m.stage,rows:m.rows,readyMs:Date.now()-start,interactions:[],scroll:[]};
     for(let i=0;i<30;i++){
       metrics.interactions.push(await page.evaluate(async stage=>{
         const begin=performance.now(),el=document.querySelector(stage==='after'?'.mg-cell[data-id]':'#luoi-vd td[id]');
         if(stage==='after'){
           el.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,button:0,clientX:60,clientY:180}));
           document.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,button:0}));
           document.getElementById('mg-viewport').dispatchEvent(new KeyboardEvent('keydown',{bubbles:true,key:'a',ctrlKey:true}));
         }else{el.click();el.dispatchEvent(new KeyboardEvent('keydown',{bubbles:true,key:'a',ctrlKey:true}));}
         await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return performance.now()-begin;
       },m.stage));
     }
     if(m.stage==='after'){
       await page.locator('#mg-viewport').evaluate(e=>e.scrollLeft=3000);
       await page.locator('.mg-cell[data-code="ghi_chu"]').first().waitFor();
       metrics.reader=[];metrics.resize=[];
       for(let i=0;i<30;i++){
         for(const kind of ['reader','resize'])metrics[kind].push(await page.evaluate(async ({kind,i})=>{
           const begin=performance.now(),el=document.querySelector(kind==='reader'?'.mg-cell[data-code="ghi_chu"][data-r="22"]':'[data-resize="ma_don"]'),r=el.getBoundingClientRect();
           const x=r.left+3,y=r.top+5;
           el.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,button:0,clientX:x,clientY:y}));
           if(kind==='resize')el.dispatchEvent(new PointerEvent('pointermove',{bubbles:true,clientX:x+(i%2?2:-2),clientY:y}));
           el.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,button:0,clientX:x,clientY:y}));
           await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
           if(kind==='reader'&&document.getElementById('mg-reader').hidden)throw Error('Reader chưa mở');
           return performance.now()-begin;
         },{kind,i}));
       }
       await page.locator('#mg-viewport').evaluate(e=>e.scrollLeft=0);
       for(let i=0;i<35;i++){
         const row=i===34?m.rows-100:i*100;
         await page.locator('#mg-viewport').evaluate((e,row)=>e.scrollTop=row*28,row);
         await page.locator(`.mg-cell[data-r="${row}"][data-id]`).first().waitFor();
         await cdp.send('HeapProfiler.collectGarbage');
         metrics.scroll.push(await page.evaluate(()=>({...window.KNJSC_MASTER.diagnostics(),heap:performance.memory.usedJSHeapSize})));
       }
       assert(metrics.scroll.every(s=>s.cache<=10&&s.cells<1500));
     }
     metrics.dom=await page.locator('*').count();metrics.longTasks=await page.evaluate(()=>window.longTasks);
     metrics.errors=errors;assert.deepEqual(errors,[]);
     fs.writeFileSync(path.join(out,`browser-${m.stage}-${m.rows}.json`),JSON.stringify(metrics,null,2));
     await page.screenshot({path:path.join(out,`capacity-${m.stage}-${m.rows}.png`)});
     fs.writeFileSync(result,JSON.stringify({ok:true}));console.log('PASS',m.stage,m.rows,'ready',metrics.readyMs);
   }catch(e){fs.writeFileSync(result,JSON.stringify({ok:false,error:e.stack}));throw e;}
   finally{await context.close();}
 }}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
