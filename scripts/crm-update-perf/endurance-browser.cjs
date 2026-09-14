/* Một Chrome trong tổng 20 client của bài bền (19 Locust + 1 Chrome). */
const fs=require('fs'),path=require('path'),assert=require('assert'),{chromium}=require('playwright');
const dir=process.env.LOAD_DIR,base='http://127.0.0.1:8853',manifest=JSON.parse(fs.readFileSync(path.join(dir,'ready.json')));
assert.equal(manifest.database,'test_crm_update_load_300000');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});const result={samples:[],errors:[],requests:[],versionConflicts:[],recoveries:[],warmup:60};
 try{
  const ctx=await browser.newContext({viewport:{width:1440,height:900}});await ctx.addCookies([{name:'sessionid',value:manifest.actors[59].session,url:base},{name:'csrftoken',value:manifest.csrf,url:base}]);
  const page=await ctx.newPage();page.setDefaultTimeout(10000);page.on('pageerror',e=>result.errors.push(e.message));
  const pending=new Set(),consoleErrors=[],knownConflictURLs=new Set();let lastConflict=0,lastRecovery=0;
  page.on('console',message=>{if(message.type()==='error')consoleErrors.push({text:message.text(),url:message.location().url});});
  page.on('response',r=>{
   if(!r.url().startsWith(base))return;
   const url=new URL(r.url()),time=Date.now();
   if(!url.pathname.includes('/static/'))result.requests.push({t:time,status:r.status(),path:url.pathname});
   const check=(async()=>{
    if(r.status()===409&&url.pathname==='/bang-tinh/van_don/du-lieu/'&&url.searchParams.has('version')){
     const body=await r.json();
     if(body.error==='Dữ liệu đã thay đổi. Đang tải lại vùng đang xem.'){
      knownConflictURLs.add(r.url());lastConflict=time;result.versionConflicts.push({t:time,error:body.error});return;
     }
    }
    if(r.status()>=400)result.errors.push('HTTP '+r.status()+' '+url.pathname);
    if(r.status()===200&&url.pathname==='/bang-tinh/van_don/du-lieu/'&&lastConflict>lastRecovery){
     const body=await r.json();assert(body.version&&body.rows.length>0,'Phản hồi phục hồi phải có dữ liệu');
     lastRecovery=time;result.recoveries.push({t:time,afterConflict:lastConflict,ms:time-lastConflict});
    }
   })().catch(e=>result.errors.push('Response validation: '+e.message));
   pending.add(check);check.finally(()=>pending.delete(check));
  });
  async function verifyResponses(){
   await Promise.all([...pending]);
   for(const error of consoleErrors.splice(0)){
    // Chỉ bỏ qua cảnh báo mạng của đúng phản hồi đổi phiên bản đã đọc JSON.
    if(error.text==='Failed to load resource: the server responded with a status of 409 (Conflict)'&&knownConflictURLs.has(error.url))continue;
    result.errors.push('Console: '+error.text);
   }
   assert(!lastConflict||lastRecovery>=lastConflict||Date.now()-lastConflict<10000,'Đổi phiên bản không phục hồi trong 10 giây');
  }
  page.on('requestfailed',r=>{if(r.failure()?.errorText!=='net::ERR_ABORTED')result.errors.push(r.failure()?.errorText||'Network failure');});
  await page.goto(base+'/bang-tinh/van_don/');await page.locator('.mg-cell[data-id]').first().waitFor();
  const started=performance.now();let iteration=0;
  while(performance.now()-started<Number(process.env.LOAD_BROWSER_SECONDS||1865)*1000){
   if(fs.existsSync(path.join(dir,'stop-endurance')))break;
   const t=performance.now();await page.locator('#mg-viewport').evaluate((v,i)=>{v.scrollTop=(i%150)*2800;v.scrollLeft=i%2?400:0;},iteration++);
   await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));const ms=performance.now()-t;
   await page.locator('.mg-cell[data-id]').first().waitFor();
   const state=await page.evaluate(()=>({...window.KNJSC_MASTER.diagnostics(),heap:performance.memory?.usedJSHeapSize,dom:document.querySelectorAll('*').length}));
   assert(state.cache<=10&&state.cells<=1500,'DOM/cache vượt giới hạn');
   if(performance.now()-started>=60000)result.samples.push({t:(performance.now()-started)/1000,ms,...state});
   await verifyResponses();assert.equal(result.errors.length,0,result.errors.join(';'));
   if(iteration%20===0){fs.writeFileSync(path.join(dir,'endurance-browser-progress.json'),JSON.stringify(result));console.log(JSON.stringify({seconds:Math.round((performance.now()-started)/1000),samples:result.samples.length,cache:state.cache,heap:state.heap}));}
   await page.waitForTimeout(3000);
  }
  await verifyResponses();assert.equal(result.errors.length,0,result.errors.join(';'));
  result.elapsed=(performance.now()-started)/1000;await page.screenshot({path:path.join(dir,'endurance-browser.png')});
 }catch(error){result.errors.push(error.stack);process.exitCode=1;fs.writeFileSync(path.join(dir,'stop-endurance'),error.message);}
 finally{fs.writeFileSync(path.join(dir,'endurance-browser.json'),JSON.stringify(result,null,2));await browser.close();}
})();
