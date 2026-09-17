/* Chỉ đọc trên preview riêng: ảnh, tràn bố cục và các vai trò. */
const {chromium}=require('./solarpunk-browser.cjs');
const fs=require('node:fs');
const out='artifacts/solarpunk';fs.mkdirSync(out,{recursive:true});
(async()=>{
 const b=await chromium.launch({channel:'chrome',headless:true});const results=[];
 for(const role of ['quantri','sale.manager','sale.leader','sale.staff']){
  const context=await b.newContext({viewport:{width:1440,height:900}});const p=await context.newPage();
  const errors=[];p.on('pageerror',e=>errors.push(e.message));
  await p.goto('http://localhost:18020/dang-nhap/');
  if(role==='quantri')await p.screenshot({path:out+'/login.png'});
  await p.locator('[name=username]').fill(role);await p.locator('[name=password]').fill('matkhaucuatoi');
  await Promise.all([p.waitForURL(u=>!u.pathname.includes('dang-nhap')),p.locator('button[type=submit]').click()]);
  const erpLinks=await p.locator('.sp-dock a').evaluateAll(a=>a.map(x=>x.href));
  await p.goto('http://localhost:18021/');
  const crmLinks=await p.locator('.crm-nav a').evaluateAll(a=>a.map(x=>x.href));
  const urls=[...new Set([...erpLinks,...crmLinks,'http://localhost:18021/bang-tinh/van_don_moi/','http://localhost:18021/bang-tinh/bao_cao_mkt/'])].filter(x=>x.startsWith('http://localhost:1802'));
  for(const url of urls){
   const r=await p.goto(url);await p.waitForTimeout(200);
   const overflow=await p.evaluate(()=>({body:document.documentElement.scrollWidth>innerWidth+2,main:!!document.querySelector('.noi-dung')&&document.querySelector('.noi-dung').scrollWidth>document.querySelector('.noi-dung').clientWidth+2}));
   results.push({role,url,status:r.status(),overflow,errors:errors.splice(0)});
   if(role==='quantri'&&r.status()===200){
    const name=url.replace('http://localhost:','').replace(/[^a-z0-9]+/gi,'-');
    await p.screenshot({path:out+'/'+name+'.png'});
    await p.setViewportSize({width:390,height:844});await p.waitForTimeout(100);
    results.push({role,url,size:390,overflow:await p.evaluate(()=>({body:document.documentElement.scrollWidth>innerWidth+2,main:!!document.querySelector('.noi-dung')&&document.querySelector('.noi-dung').scrollWidth>document.querySelector('.noi-dung').clientWidth+2}))});
    await p.screenshot({path:out+'/'+name+'mobile.png'});await p.setViewportSize({width:1440,height:900});
   }
  }
  await context.close();
 }
 fs.writeFileSync(out+'/audit.json',JSON.stringify(results,null,2));
 console.log(JSON.stringify(results.filter(x=>x.status>=400||x.errors?.length||x.overflow.body||x.overflow.main),null,2));
 await b.close();
})().catch(e=>{console.error(e);process.exit(1)});
