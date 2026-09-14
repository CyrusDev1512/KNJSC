const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const kind=process.env.ERP_BROWSER_KIND||'sale';
if(!['sale','mkt'].includes(kind))throw Error('Only Sale/MKT report scenarios');
const base='http://127.0.0.1:8135',out=path.resolve('storage/erp-verification/browser-'+kind);
fs.mkdirSync(out,{recursive:true});
(async()=>{
 for(let attempt=0;attempt<20;attempt++){
  try{const r=await fetch(base+'/dang-nhap/',{signal:AbortSignal.timeout(2000)});if(r.ok)break}catch(e){if(attempt===19)throw e}
  await new Promise(r=>setTimeout(r,500));
 }
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const results=[],errors=[];
 for(const width of [1440,390])for(const role of ['staff','leader','manager','admin']){
  const username={staff:`erp_${kind}_0`,leader:`erp_${kind}_19`,manager:`erp_${kind}_manager`,admin:'erp_admin'}[role];
  const ctx=await browser.newContext({viewport:{width,height:900},acceptDownloads:true});
  const page=await ctx.newPage();
  page.on('pageerror',e=>errors.push({role,width,error:e.message}));
  page.on('console',m=>{if(m.type()==='error')errors.push({role,width,error:m.text()})});
  await page.goto(base+'/dang-nhap/');await page.locator('[name=username]').fill(username);await page.locator('[name=password]').fill('erp-test-only-2026');
  await Promise.all([page.waitForURL(base+'/'),page.locator('button[type=submit]').click()]);
  assert.equal(await page.locator('a[href="/bao-cao/hoat-dong/"]').count(),0);
  await page.goto(base+`/bao-cao/hoat-dong/?nguon=bao_cao_${kind}&nhom=market&tu=2026-09-01&den=2026-09-10&thi_truong=Canada`);
  assert.equal(new URL(page.url()).pathname,'/bao-cao/tong-hop/');
  assert.equal(new URL(page.url()).searchParams.get('thi_truong'),'Canada');
  await page.getByRole('heading',{name:'Báo cáo tổng hợp',exact:true}).waitFor();
  let formsLoadMs=null;
  if(['manager','admin'].includes(role)){
   const formsResponse=await page.goto(base+'/bieu-mau/');
   assert.equal(formsResponse.status(),200);
   await page.getByRole('heading',{name:'Quản lý biểu mẫu và bảng',exact:true}).waitFor();
   formsLoadMs=await page.evaluate(()=>performance.getEntriesByType('navigation')[0].loadEventEnd);
  }else{
   assert.equal((await ctx.request.get(base+'/bieu-mau/')).status(),403);
  }
  const day=`${process.env.ERP_BROWSER_YEAR||2038}-${String(Number(process.env.ERP_BROWSER_MONTH||3)+(width===1440?0:1)).padStart(2,'0')}-0${['staff','leader','manager','admin'].indexOf(role)+1}`;
  await page.goto(base+`/bao-cao/?bieu_mau=bc_${kind}_ngay&ngay=${day}`);
  assert.equal(await page.locator(`#o-${kind}_${kind==='mkt'?'marketer':'sale'}`).inputValue(),username);
  const dailyLoadMs=await page.evaluate(()=>performance.getEntriesByType('navigation')[0].loadEventEnd);
  for(const [name,value] of Object.entries({ngay:day,so_mess:'100',so_don:'5',doanh_so:'1000',...(kind==='mkt'?{cpqc:'200'}:{})}))await page.locator(`[name=${kind}_${name}]`).fill(value);
  await page.locator(`[name=${kind}_san_pham]`).selectOption({label:'ERP product 0'});
  await page.locator(`[name=${kind}_thi_truong]`).selectOption({label:'Canada'});
  await Promise.all([page.waitForURL('**/bao-cao/lich-su/'),page.getByRole('button',{name:'Nộp báo cáo',exact:true}).click()]);
  await page.locator('#tu').fill(day);await page.locator('#den').fill(day);
  await Promise.all([page.waitForURL(u=>u.searchParams.get('tu')===day),page.getByRole('button',{name:'Lọc',exact:true}).click()]);
  await page.locator('a[href^="/bao-cao/tong-hop/?"]').filter({hasText:'Báo cáo tổng hợp'}).first().click();
  assert.equal(new URL(page.url()).searchParams.get('tu'),day);
  assert.match(await page.locator('tfoot').innerText(),kind==='sale'?/100\s+5\s+1\.000\s+0,05/:/100\s+200\s+5\s+1\.000/);
  for(const group of ['person','product','market','department']){
   await page.locator('#nhom').selectOption(group);
   await Promise.all([page.waitForURL(u=>u.searchParams.get('nhom')===group),page.getByRole('button',{name:'Áp dụng',exact:true}).click()]);
   assert.match(await page.locator('tfoot').innerText(),kind==='sale'?/100\s+5\s+1\.000\s+0,05/:/100\s+200\s+5\s+1\.000/);
  }
  await page.locator('#thi-truong').selectOption({label:'Canada'});
  await Promise.all([page.waitForURL(u=>u.searchParams.get('thi_truong')==='Canada'),page.getByRole('button',{name:'Áp dụng',exact:true}).click()]);
  const downloaded=page.waitForEvent('download');await page.getByRole('link',{name:'Xuất Excel',exact:true}).click();
  await (await downloaded).saveAs(path.join(out,`${role}-${width}.xlsx`));
  await page.screenshot({path:path.join(out,`${role}-${width}.png`),fullPage:true});
  const layout=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));
  assert(layout.scroll<=width+1,JSON.stringify(layout));
  await page.locator('.bang-cuon').first().evaluate(e=>e.scrollLeft=e.scrollWidth);
  await page.goto(base+`/?tu=${day}&den=${day}&${kind}_nguon=bao_cao_${kind}`);
  const saleBlock=page.locator('section.the').filter({has:page.getByRole('heading',{name:kind==='mkt'?'Marketing':'Sale',exact:true})}).last();
  assert.match(await saleBlock.innerText(),/1\.000/);
  // Giả mạo nguồn khác phòng: Staff/Leader/Manager không nhận số liệu.
  if(role!=='admin'){
   const denied=await ctx.request.get(base+`/bao-cao/tong-hop/?nguon=bao_cao_${kind==='sale'?'mkt':'sale'}`);assert.equal(denied.status(),403);
   const exported=await ctx.request.get(base+`/bao-cao/tong-hop/xuat/?nguon=bao_cao_${kind==='sale'?'mkt':'sale'}`);assert.equal(exported.status(),403);
  }
  await page.goto(base+`/bao-cao/tong-hop/?nguon=bao_cao_${kind}&tu=2030-01-01&den=2030-01-02`);
  await page.getByText('Chưa có dữ liệu trong bộ lọc này.',{exact:true}).waitFor();
  await page.goto(base+`/?${kind}_nguon=does-not-exist`);await page.getByRole('alert').filter({hasText:'Không tải được số liệu'}).waitFor();
  results.push({role,width,day,layout,formsLoadMs,dailyLoadMs,passed:true});await ctx.close();
 }
 await browser.close();fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({results,errors},null,2));assert.equal(errors.length,0,JSON.stringify(errors.slice(0,5)));console.log(JSON.stringify({passed:results.length,errors}));
})().catch(e=>{console.error(e);process.exit(1)});
