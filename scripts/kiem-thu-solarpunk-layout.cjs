const {chromium}=require('./solarpunk-browser.cjs');
const assert=require('node:assert/strict'),fs=require('node:fs');
(async()=>{
 const b=await chromium.launch({channel:'chrome',headless:true});const results=[];
 const sizes=[[1920,1080,1],[1440,900,1],[1366,768,1],[768,1024,1],[390,844,1],[1152,720,1.25],[720,450,2]];
 for(const [width,height,scale]of sizes){
  const ctx=await b.newContext({viewport:{width,height},deviceScaleFactor:scale});const p=await ctx.newPage();
  await p.goto('http://localhost:18020/dang-nhap/');await p.locator('[name=username]').fill('quantri');await p.locator('[name=password]').fill('matkhaucuatoi');
  await Promise.all([p.waitForURL(u=>!u.pathname.includes('dang-nhap')),p.locator('button[type=submit]').click()]);
  for(const theme of ['light','dark']){
   await p.evaluate(t=>localStorage.setItem('knjsc-nen',t),theme);
   for(const [url,name]of [['http://localhost:18020/bao-cao/lich-su/','reports'],['http://localhost:18021/bang-tinh/van_don_moi/','grid']]){
    await p.goto(url);await p.evaluate(t=>localStorage.setItem('knjsc-nen',t),theme);await p.reload();await p.waitForTimeout(200);
    assert.equal(await p.locator('html').getAttribute('data-theme'),theme);
    const measure=await p.evaluate(()=>{const main=document.querySelector('.noi-dung'),dock=document.querySelector('.sp-dock');return {overflow:document.documentElement.scrollWidth>innerWidth+2,mainOverflow:!!main&&main.scrollWidth>main.clientWidth+2,overlap:!!main&&!!dock&&main.getBoundingClientRect().bottom>dock.getBoundingClientRect().top+1}});
    assert.equal(measure.overflow,false);assert.equal(measure.mainOverflow,false);assert.equal(measure.overlap,false);
    await p.screenshot({path:`artifacts/solarpunk/${name}-${width}-${scale}-${theme}.png`});
    if(name==='grid'){
      await p.locator('#bt-toan-man-nut').click();
      assert.equal(await p.locator('.mg-toolbar').isVisible(),false);
      const rect=await p.locator('#mg-viewport').boundingBox();assert.ok(rect.height>height-90);
      await p.screenshot({path:`artifacts/solarpunk/focus-${width}-${scale}-${theme}.png`});
    }
    results.push({width,height,scale,theme,name,...measure});
   }
  }
  await ctx.close();
 }
 fs.writeFileSync('artifacts/solarpunk/layout.json',JSON.stringify(results,null,2));await b.close();console.log('PASS: 7 viewport/density settings × light/dark × reports/grid/focus; no body overflow or dock overlap');
})().catch(e=>{console.error(e);process.exit(1)});
