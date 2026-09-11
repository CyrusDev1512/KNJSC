/* AC-21: đo ngay trong lượt cuộn, không đợi JS bù tọa độ. Chỉ dùng DB test row-capacity. */
const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const out=path.resolve(process.env.PINNED_EVIDENCE||'.agents/design-state/review/pinned-20260911');
const phase=process.env.PINNED_PHASE||'after',sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 fs.mkdirSync(out,{recursive:true});const browser=await chromium.launch({channel:'chrome',headless:true});let failed=false;
 try{for(const count of [100000,300000]){
  const marker=path.join(out,'row-capacity-ready.json'),done=path.join(out,'row-capacity-result.json');
  let m;for(let i=0;i<600;i++){if(fs.existsSync(marker)&&!fs.existsSync(done)){m=JSON.parse(fs.readFileSync(marker));if(m.rows===count)break;}await sleep(500);}
  assert.equal(m?.rows,count,'Fixture DB test chưa sẵn sàng');const base='http://127.0.0.1:'+m.port;
  const context=await browser.newContext({viewport:{width:1440,height:900},recordVideo:{dir:out,size:{width:1440,height:900}}});
  await context.addCookies([{name:'sessionid',value:m.session,url:base}]);const page=await context.newPage(),errors=[],requests=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.url().includes('/du-lieu/'))requests.push(r.url());});
  try{
   await page.goto(base+'/bang-tinh/van_don_moi/');await page.locator('.mg-cell[data-r="0"][data-id]').first().waitFor();
   assert.equal(await page.evaluate(()=>KNJSC_MASTER.diagnostics().total),count);
   const samples=[];
   for(const width of [1440,1280,390])for(const zoom of [1,1.25]){
    await page.setViewportSize({width,height:900});await page.evaluate(z=>{document.documentElement.style.zoom=z;document.getElementById('mg-viewport').scrollLeft=0;},zoom);await sleep(150);
    const sample=await page.evaluate(async()=>{
     const v=document.getElementById('mg-viewport'),next=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
     const nodes=[document.querySelector('.mg-corner'),...document.querySelectorAll('.mg-head .mg-pinned'),document.querySelector('.mg-number'),...document.querySelectorAll('.mg-row:first-child .mg-pinned')];
     const x=nodes.map(e=>e.getBoundingClientRect().left),header=document.querySelector('.mg-head'),hy=header.getBoundingClientRect().top;
     const drift=[],times=[],long=[];const observer=new PerformanceObserver(list=>long.push(...list.getEntries().map(e=>e.duration)));observer.observe({type:'longtask'});
     for(let i=0;i<40;i++){
      const start=performance.now();v.scrollLeft=(v.scrollWidth-v.clientWidth)*(i%20)/19;
      // Force layout avant rAF: phát hiện cột trượt ngay cả khi render sẽ sửa lại sau đó.
      drift.push(Math.max(...nodes.map((e,j)=>e.isConnected?Math.abs(e.getBoundingClientRect().left-x[j]):Infinity)));
      await next();times.push(performance.now()-start);
     }
     v.scrollTop=14;const vertical=Math.abs(header.getBoundingClientRect().top-hy);await next();v.scrollTop=0;v.scrollLeft=0;await next();
     observer.disconnect();return {drift,times,long,vertical,stableNodes:nodes.every(e=>e.isConnected),diagnostics:KNJSC_MASTER.diagnostics()};
    });
    samples.push({width,zoom,...sample});
   }
   await page.evaluate(()=>document.documentElement.style.zoom=1);await page.setViewportSize({width:1440,height:900});
   const deep=[];
   for(const r of [100,500,1500,2500,3500,4500,5500,6500,7500,8500,9500,count-100,0]){
    await page.locator('#mg-viewport').evaluate((v,r)=>{v.scrollTop=r*28;v.scrollLeft=0;},r);
    await page.locator(`.mg-cell[data-r="${r}"][data-id]`).first().waitFor();deep.push(await page.evaluate(()=>({...KNJSC_MASTER.diagnostics(),dom:document.getElementById('mg-canvas').querySelectorAll('*').length})));
   }
   const result={phase,count,browser:browser.version(),samples,deep,requests:requests.length,errors};
   fs.writeFileSync(path.join(out,`${phase}-${count}.json`),JSON.stringify(result,null,2));
   await page.screenshot({path:path.join(out,`${phase}-${count}.png`)});
   const maxDrift=Math.max(...samples.flatMap(s=>s.drift)),maxVertical=Math.max(...samples.map(s=>s.vertical));
   const passed=maxDrift<=1&&maxVertical<=1&&samples.every(s=>s.stableNodes)&&deep.every(s=>s.cache<=10&&s.cells<1500)&&!errors.length;
   failed ||= !passed;console.log(JSON.stringify({phase,count,passed,maxDrift,maxVertical,requests:requests.length,errors}));
   // Fixture chỉ báo đã hoàn tất đo; exit code riêng thể hiện hồi quy đỏ/xanh.
   fs.writeFileSync(done,JSON.stringify({ok:true}));
  }catch(e){fs.writeFileSync(done,JSON.stringify({ok:false,error:e.stack}));throw e;}
  finally{const video=page.video();await context.close();await video.saveAs(path.join(out,`${phase}-${count}.webm`));}
 }}finally{await browser.close();}assert(!failed,'Cột ghim lệch >1px hoặc node bị thay khi cuộn; xem bằng chứng JSON');
})().catch(e=>{console.error(e);process.exitCode=1;});
