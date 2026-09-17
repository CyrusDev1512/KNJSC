/* Chrome + API/PostgreSQL thật trên network test. Không dùng tài khoản/dữ liệu VPS. */
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'../../storage/grid-flags-20260916');
const ready=JSON.parse(fs.readFileSync(path.join(root,'ready.json')));
assert.equal(ready.database,'test_knjsc_gridflags_load');
const base='http://127.0.0.1:18641',stage=process.argv[2];
assert(/^[a-z0-9-]+$/.test(stage));
const stats=a=>{const b=[...a].sort((a,b)=>a-b);return {n:b.length,p50:b[Math.ceil(b.length*.5)-1],p95:b[Math.ceil(b.length*.95)-1],max:b.at(-1)}};

async function scroll(page,row){
  return page.evaluate(async row=>{
    const v=document.getElementById('mg-viewport'),t=performance.now();v.scrollTop=row*28;
    return new Promise((resolve,reject)=>{
      function check(){
        const last=Math.floor((v.scrollTop+v.clientHeight-55)/28);
        const complete=Array.from({length:last-row+1},(_,i)=>document.querySelector(`.mg-cell[data-r="${row+i}"][data-id]`)).every(Boolean);
        if(complete)return requestAnimationFrame(()=>resolve(performance.now()-t));
        if(performance.now()-t>15000)return reject(Error('Timeout hiển thị vùng đích'));requestAnimationFrame(check);
      }requestAnimationFrame(check);
    });
  },row);
}

(async()=>{
  const browser=await chromium.launch({channel:'chrome',headless:true});const results=[];
  try{for(const width of [1440,390]){
    const context=await browser.newContext({viewport:{width,height:900}}),page=await context.newPage();
    const errors=[],requests=[];let release;
    const actor=ready.users.find(u=>u.role==='admin');
    await context.addCookies([{name:'sessionid',value:actor.session,url:base}]);
    page.on('pageerror',e=>errors.push(e.message));
    page.on('request',r=>{if(r.url().includes('/du-lieu/'))requests.push(new URL(r.url()).searchParams.get('offset')||'0')});
    const result={stage,width,errors};results.push(result);
    try{
      await page.goto(base+'/bang-tinh/van_don_moi/');await page.locator('.mg-cell[data-r="0"][data-id]').first().waitFor();
      await scroll(page,110);await scroll(page,0);await page.waitForTimeout(400);
      const cached=[];for(let i=0;i<40;i++)cached.push(await scroll(page,i%2?18:19));
      result.cached=stats(cached);
      await page.reload();await page.locator('.mg-cell[data-r="0"][data-id]').first().waitFor();await page.waitForTimeout(400);
      const continuous=[],networkStart=requests.length;
      for(let i=1;i<=55;i++){continuous.push(await scroll(page,i*12));await page.waitForTimeout(25)}
      result.continuous=stats(continuous);result.continuousRequests=requests.length-networkStart;
      const jumps=[];
      for(const destination of [12000,26000,38000]){
        const before=requests.length;
        for(let i=1;i<=12;i++){await page.locator('#mg-viewport').evaluate((v,row)=>v.scrollTop=row*28,destination-1200+i*100);await page.waitForTimeout(25)}
        jumps.push({waitAfterLastScrollMs:await scroll(page,destination),requests:requests.length-before});
      }
      result.farJumps=jumps;
      await scroll(page,0);await page.locator('#mg-mode').click();
      await page.locator('#mg-viewport').evaluate(v=>v.scrollLeft=v.scrollWidth);
      const cell=page.locator('.mg-cell[data-r="0"][data-code="ghi_chu"]');await cell.waitFor();
      const id=Number(await cell.getAttribute('data-id')),value='GRID-FLAGS-'+stage+'-'+width;
      let entered=false;
      const held=new Promise(r=>release=r);
      await page.route('**/luu-json/',async route=>{const response=await route.fetch();entered=true;await held;await route.fulfill({response})});
      await cell.dblclick();const input=page.locator('#mg-input [name=value]');await input.fill(value);await input.press('Control+Enter');
      const deadline=Date.now()+15000;while(!entered&&Date.now()<deadline)await page.waitForTimeout(30);assert(entered,'Chưa có request lưu thật');
      result.pendingInteraction=await page.evaluate(async()=>{
        const v=document.getElementById('mg-viewport'),samples={select:[],open:[],type:[]};
        const frame=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
        const key=(el,key)=>el.dispatchEvent(new KeyboardEvent('keydown',{key,bubbles:true,cancelable:true}));
        for(let i=0;i<20;i++){
          let t=performance.now();key(v,i%2?'ArrowUp':'ArrowDown');await frame();samples.select.push(performance.now()-t);
          t=performance.now();key(v,'F2');await frame();samples.open.push(performance.now()-t);
          const input=document.querySelector('#mg-input [name=value]');if(!input)throw Error('Editor không mở khi đang lưu');
          t=performance.now();input.value='Nhập tiếng Việt '+i;input.dispatchEvent(new Event('input',{bubbles:true}));await frame();samples.type.push(performance.now()-t);
          if(input.value!=='Nhập tiếng Việt '+i)throw Error('Mất nội dung nhập');key(input,'Escape');await frame();
        }
        return samples;
      });
      result.pendingInteraction=Object.fromEntries(Object.entries(result.pendingInteraction).map(([k,v])=>[k,stats(v)]));
      const saved=page.waitForResponse(r=>r.url().includes('/luu-json/'));release();release=null;assert.equal((await saved).status(),200);
      await page.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent!=='Đang lưu');
      await page.unroute('**/luu-json/');await page.reload();await page.locator('.mg-cell[data-r="0"][data-id]').first().waitFor();
      const response=await page.request.get(base+'/bang-tinh/van_don_moi/du-lieu/');const body=await response.json();
      assert.equal(body.rows.find(r=>r.id===id).cells.ghi_chu.value,value,'Lưu thật không khớp');
      result.savedAndReloaded=true;result.diagnostics=await page.evaluate(()=>KNJSC_MASTER.diagnostics());
      assert(result.diagnostics.cache<=10);assert.equal(errors.length,0);
      await page.screenshot({path:path.join(root,'results',stage+'-'+width+'.png')});
    }finally{release?.();await context.close()}
  }}finally{await browser.close();fs.writeFileSync(path.join(root,'results',stage+'-real-browser.json'),JSON.stringify(results,null,2))}
  console.log(JSON.stringify(results));
})().catch(e=>{console.error(e.stack);process.exitCode=1});
