// Đo browser trên server test riêng đã có 100.000 bản ghi; không ghi dữ liệu.
const {chromium}=require('playwright'),fs=require('fs'),path=require('path');
const base='http://127.0.0.1:8135',out=path.resolve('storage/erp-verification/browser-perf');
fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true}),all=[];
 for(const width of [1440,390])for(const source of ['bao_cao_mkt','bao_cao_sale','van_don']){
  const ctx=await browser.newContext({viewport:{width,height:900}}),page=await ctx.newPage();
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+'/dang-nhap/');await page.locator('[name=username]').fill('erp_admin');await page.locator('[name=password]').fill('erp-test-only-2026');
  await Promise.all([page.waitForURL(base+'/'),page.locator('button[type=submit]').click()]);
  await page.addInitScript(()=>{window.erpLongTasks=[];new PerformanceObserver(list=>{for(const e of list.getEntries())window.erpLongTasks.push({start:e.startTime,duration:e.duration})}).observe({type:'longtask',buffered:true})});
  const cdp=await ctx.newCDPSession(page);
  await cdp.send('Tracing.start',{categories:'devtools.timeline,blink.user_timing',transferMode:'ReturnAsStream'});
  await page.goto(base+`/bao-cao/tong-hop/?nguon=${source}&tu=2020-01-01&den=2025-12-31`);
  await page.locator('tbody tr').first().waitFor();
  const navigation=await page.evaluate(()=>{const n=performance.getEntriesByType('navigation')[0];return {ttfb:n.responseStart,dom:n.domContentLoadedEventEnd,load:n.loadEventEnd,bytes:n.decodedBodySize,rows:document.querySelectorAll('tbody tr').length,domNodes:document.querySelectorAll('*').length,longTasks:window.erpLongTasks}});
  const frames=await page.locator('.bang-cuon').first().evaluate(e=>new Promise(resolve=>{const gaps=[];let before=performance.now(),i=0;function step(now){gaps.push(now-before);before=now;e.scrollLeft=(i%60)/59*(e.scrollWidth-e.clientWidth);if(++i<180)requestAnimationFrame(step);else resolve(gaps)}requestAnimationFrame(step)}));
  await page.locator('#report-multi-sp summary').click();await page.locator('#report-multi-sp .report-multi-tim').pressSequentially('sample',{delay:25});await page.locator('#report-multi-sp .report-multi-tim').fill('');
  const begin=Date.now();await page.locator('#thi-truong').selectOption({label:'Canada'});
  await Promise.all([page.waitForURL(u=>u.searchParams.get('thi_truong')==='Canada'),page.getByRole('button',{name:'Áp dụng',exact:true}).click()]);
  const filterMs=Date.now()-begin;
  const done=new Promise(resolve=>cdp.once('Tracing.tracingComplete',resolve));await cdp.send('Tracing.end');const {stream}=await done;
  let trace='';while(true){const part=await cdp.send('IO.read',{handle:stream});trace+=part.data;if(part.eof)break}await cdp.send('IO.close',{handle:stream});
  fs.writeFileSync(path.join(out,`${source}-${width}-trace.json`),trace);
  frames.sort((a,b)=>a-b);all.push({source,width,navigation,filterMs,frameP95:frames[Math.floor(frames.length*.95)],frameMax:Math.max(...frames),errors});
  await ctx.close();
 }
 await browser.close();fs.writeFileSync(path.join(out,'metrics.json'),JSON.stringify(all,null,2));console.log(JSON.stringify(all));
})().catch(e=>{console.error(e);process.exit(1)});
