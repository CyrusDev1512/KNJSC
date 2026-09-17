// Ma trận UI và đo lịch sử trên dữ liệu test 100k; không tạo báo cáo.
const { chromium } = require('playwright');
const assert = require('assert/strict');
const fs = require('fs');
const base = 'http://127.0.0.1:8135';
(async () => {
  const browser = await chromium.launch({channel:'chrome',headless:true});
  const results=[];
  for (const width of [1440,390]) for (const role of ['staff','leader','manager','admin']) {
    const username={staff:'erp_mkt_0',leader:'erp_mkt_19',manager:'erp_mkt_manager',admin:'erp_admin'}[role];
    const context=await browser.newContext({viewport:{width,height:900}});
    const page=await context.newPage();
    const errors=[];
    page.on('pageerror',()=>errors.push('pageerror'));
    page.on('console',m=>{if(m.type()==='error')errors.push('console')});
    await page.goto(base+'/dang-nhap/');
    await page.locator('[name=username]').fill(username);
    await page.locator('[name=password]').fill('erp-test-only-2026');
    await Promise.all([page.waitForURL(base+'/'),page.locator('button[type=submit]').click()]);
    for(const [path,visible] of [['/nhan-su/',role!=='staff'],['/bieu-mau/',true]]) {
      assert.equal(await page.locator(`a[href="${path}"]`).count()>0,visible);
      assert.equal((await context.request.get(base+path)).status(),visible?200:403);
    }
    assert.equal((await context.request.get(base+'/bieu-mau/?tab=forms')).status(),['manager','admin'].includes(role)?200:403);
    assert.equal((await context.request.get(base+'/nhan-su/moi/')).status(),role==='admin'?200:403);
    for(const path of ['/bao-cao/','/bang/','/bao-cao/tong-hop/']) {
      assert.equal((await page.goto(base+path)).status(),200);
    }
    await page.goto(base+'/bao-cao/lich-su/?tu=2000-01-01&den=2025-12-31');
    const loadMs=await page.evaluate(()=>performance.getEntriesByType('navigation')[0].loadEventEnd);
    await page.evaluate(()=>{
      window.identityInputFrames=[];
      document.querySelector('#tim').addEventListener('input',event=>{
        const start=event.timeStamp;
        requestAnimationFrame(()=>window.identityInputFrames.push(performance.now()-start));
      });
    });
    await page.locator('#tim').pressSequentially('erp_mkt_0',{delay:30});
    const inputToFrameMaxMs=await page.evaluate(()=>Math.max(...window.identityInputFrames));
    const begin=Date.now();
    await Promise.all([page.waitForNavigation(),page.getByRole('button',{name:'Lọc',exact:true}).click()]);
    const filterMs=Date.now()-begin;
    const pageBegin=Date.now();
    await Promise.all([page.waitForNavigation(),page.getByRole('link',{name:'Trang sau',exact:true}).click()]);
    const paginationMs=Date.now()-pageBegin;
    assert.equal(new URL(page.url()).searchParams.get('tim'),'erp_mkt_0');
    assert.equal(new URL(page.url()).searchParams.get('trang'),'2');
    await page.getByRole('link',{name:'Xem',exact:true}).first().click();
    await page.getByRole('link',{name:'Quay lại',exact:true}).click();
    assert.equal(new URL(page.url()).searchParams.get('trang'),'2');
    assert.equal(new URL(page.url()).searchParams.get('tim'),'erp_mkt_0');
    await page.getByLabel('Số dòng mỗi trang').selectOption('50');
    await page.waitForURL(u=>u.searchParams.get('moi_trang')==='50');
    assert.equal(new URL(page.url()).searchParams.get('tim'),'erp_mkt_0');
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
    if(role!=='admin') {
      const denied=await context.request.get(base+'/bao-cao/tong-hop/xuat/?nguon=bao_cao_sale');
      assert.equal(denied.status(),403);
    }
    assert.equal(errors.length,0);
    results.push({role,width,loadMs,filterMs,paginationMs,inputToFrameMaxMs,passed:true});
    await context.close();
  }
  await browser.close();
  fs.writeFileSync('storage/erp-verification/identity-role-browser.json',JSON.stringify(results,null,2));
  console.log(JSON.stringify({passed:results.length,results}));
})().catch(e=>{console.error(e);process.exit(1)});
