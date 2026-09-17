/* Chỉ dùng với fixture STAT_LABEL_BROWSER trên database test. */
const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('assert/strict');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'storage');
assert(JSON.parse(fs.readFileSync(path.join(dir,'statistics-label-ready.json'))).database.startsWith('test_'));
const base='http://127.0.0.1:8812',results=[],errors=[];
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 try{
  for(const width of [1440,390])for(const role of ['quan_tri','staff_sale_1']){
   const context=await browser.newContext({viewport:{width,height:900}}),page=await context.newPage();
   page.on('pageerror',e=>errors.push(e.message));
   await page.goto(base+'/dang-nhap/');
   await page.locator('[name=username]').fill(role);
   await page.locator('[name=password]').fill('matkhau-kiem-thu-1');
   await Promise.all([page.waitForURL(u=>!u.pathname.includes('dang-nhap')),page.locator('button[type=submit]').click()]);
   const start=Date.now();await page.goto(base+'/thong-ke/');
   assert.equal(await page.locator('.exec-controls').evaluate(el=>getComputedStyle(el).display),'flex');
   assert(await page.evaluate(()=>Array.from(document.styleSheets).some(sheet=>sheet.href?.includes('/css/executive-statistics.css')&&sheet.cssRules.length>0)));
   for(const name of ['Nguồn phân tích','Từ ngày','Đến ngày','Marketing','Sale','Vận đơn']){
    const field=page.getByLabel(new RegExp('^'+name+'(?:\\s|$)'));
    assert.equal(await field.count(),1,`Không tìm thấy nhãn ${name}`);
    assert(await field.evaluate(el=>Array.from(el.labels).some(label=>label.htmlFor===el.id)));
   }
   results.push({width,role,operation:'overview_load',ms:Date.now()-start});
   await page.getByLabel(/^Nguồn phân tích(?:\s|$)/).selectOption('van_don_moi');
   await page.getByLabel(/^Từ ngày(?:\s|$)/).fill('2026-09-01');
   await page.getByLabel(/^Đến ngày(?:\s|$)/).fill('2026-09-30');
   await page.getByRole('button',{name:'Áp dụng',exact:true}).click();
   await page.getByLabel(/^Cách nhóm(?:\s|$)/).waitFor();
   await page.locator('label[for="exec-group"]').click();
   assert(await page.getByLabel(/^Cách nhóm(?:\s|$)/).evaluate(el=>document.activeElement===el));
   await page.getByLabel(/^Cách nhóm(?:\s|$)/).selectOption('product');
   const filtered=Date.now();await page.getByRole('button',{name:'Áp dụng',exact:true}).click();
   await page.waitForURL(/group=product/);
   assert.equal(new URL(page.url()).searchParams.get('tu'),'2026-09-01');
   assert.equal(await page.getByLabel(/^Cách nhóm(?:\s|$)/).inputValue(),'product');
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   results.push({width,role,operation:'filter_group',ms:Date.now()-filtered});
   await page.screenshot({path:path.join(dir,`statistics-label-${role}-${width}.png`)});
   await context.close();
  }
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(dir,'statistics-label-browser.json'),JSON.stringify({ok:true,results,errors},null,2));
  fs.writeFileSync(path.join(dir,'statistics-label-result.json'),JSON.stringify({ok:true}));
  console.log(JSON.stringify({ok:true,results}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);fs.writeFileSync(path.join(dir,'statistics-label-result.json'),JSON.stringify({ok:false}));process.exitCode=1;});
