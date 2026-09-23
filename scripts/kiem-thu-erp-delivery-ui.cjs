const {chromium}=require('playwright'),assert=require('assert/strict'),fs=require('fs'),path=require('path');
const base='http://127.0.0.1:8135',out=path.resolve('storage/erp-verification/browser-delivery');fs.mkdirSync(out,{recursive:true});
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});const results=[];
for(const width of [1440,390])for(const role of ['staff','leader','manager','admin']){
 const ctx=await browser.newContext({viewport:{width,height:900}}),page=await ctx.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 await page.goto(base+'/dang-nhap/');await page.locator('[name=username]').fill({staff:'erp_vd_0',leader:'erp_vd_19',manager:'erp_vd_manager',admin:'erp_admin'}[role]);await page.locator('[name=password]').fill('erp-test-only-2026');
 await Promise.all([page.waitForURL(base+'/'),page.locator('button[type=submit]').click()]);
 await page.goto(base+'/bao-cao/tong-hop/?nguon=van_don&tu=2020-01-01&den=2025-12-31');
 const count=role==='staff'?2000:40000;
 const num=n=>String(n).replace(/\B(?=(\d{3})+(?!\d))/g,'.');
 assert.equal((await page.locator('tfoot td').allTextContents()).join('|'),[num(count),num(count*3)].join('|'));
 assert.deepEqual(await page.locator('thead th').allTextContents(),['Ngày','Số đơn','Số lượng sản phẩm']);
 for(const group of ['person','product','market','department']){
  await page.locator('#nhom').selectOption(group);await Promise.all([page.waitForURL(u=>u.searchParams.get('nhom')===group),page.getByRole('button',{name:'Áp dụng',exact:true}).click()]);
  assert.equal((await page.locator('tfoot td').allTextContents()).join('|'),[num(count),num(count*3)].join('|'));
 }
 await page.locator('#report-multi-sp summary').click();await page.locator('#report-multi-sp input[value="erp-p0"]').check();await page.locator('#thi-truong').selectOption({label:'Canada'});
 await Promise.all([page.waitForURL(u=>u.searchParams.get('sp')==='erp-p0'),page.getByRole('button',{name:'Áp dụng',exact:true}).click()]);
 const download=page.waitForEvent('download');await page.getByRole('link',{name:'Xuất Excel',exact:true}).click();await (await download).saveAs(path.join(out,`${role}-${width}.xlsx`));
 await page.screenshot({path:path.join(out,`${role}-${width}.png`),fullPage:true});
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
 await page.goto(base+'/?delivery_nguon=van_don&tu=2020-01-01&den=2025-12-31');
 const block=page.locator('section.the').filter({has:page.getByRole('heading',{name:'Hoạt động Vận đơn',exact:true})}).last();assert((await block.innerText()).includes(num(count*3)));
 assert.deepEqual(errors,[]);results.push({role,width,count,passed:true});await ctx.close();
}await browser.close();fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(results,null,2));console.log(JSON.stringify({passed:results.length}));})().catch(e=>{console.error(e);process.exit(1)});
