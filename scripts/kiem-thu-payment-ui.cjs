/* Chỉ kết nối pytest live_server 8858 và dữ liệu synthetic. */
const {chromium}=require('playwright'), fs=require('fs'), path=require('path'), assert=require('assert/strict');
const root=path.resolve(__dirname,'..'), base='http://127.0.0.1:8858';
const output=path.join(root,'.agents/design-state/review/payment');
const resultFile=path.join(root,'app/.payment-result.json');
const png=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=','base64');
(async()=>{
 const report={ok:false,errors:[],requests:[],screens:[],metrics:{}};
 fs.mkdirSync(output,{recursive:true});
 const fixture=JSON.parse(fs.readFileSync(path.join(root,'app/.payment-ready.json')));
 report.metrics.serverBlock=fixture.metrics;
 const browser=await chromium.launch({channel:'chrome',headless:true});
 try{
  const context=await browser.newContext({viewport:{width:1440,height:900},permissions:['clipboard-read','clipboard-write']});
  const page=await context.newPage();page.setDefaultTimeout(15000);
  page.on('pageerror',e=>report.errors.push(e.message));
  page.on('request',r=>{if(r.url().includes('/chung-tu-thanh-toan/anh/'))report.requests.push(r.url());});
  await page.goto(base+'/dang-nhap/');await page.locator('[name=username]').fill('quan_tri');await page.locator('[name=password]').fill('matkhau-kiem-thu-1');
  await Promise.all([page.waitForURL(u=>!u.pathname.includes('dang-nhap')),page.locator('[type=submit]').click()]);
  await page.goto(base+'/bang-tinh/van_don_moi/');await page.locator('.mg-cell[data-id]').first().waitFor();
  const samples=[];
  for(let i=0;i<12;i++){
   const start=Date.now();const r=await page.request.get(base+'/bang-tinh/van_don_moi/du-lieu/?offset='+(i*700));
   assert.equal(r.status(),200);const data=await r.json();assert.equal(data.total,10000);assert.equal(data.rows.length,100);
   samples.push(Date.now()-start);
  }
  report.metrics.blockMs=samples;
  report.metrics.dom=[];
  for(const row of [500,2000,9500,0,1200,3000,4400,6100,7300,8300,9500,0]){
   await page.locator('#mg-viewport').evaluate((v,r)=>{v.scrollTop=r*28;v.scrollLeft=2200;},row);
   await page.locator(`.mg-cell[data-r="${row}"][data-id]`).first().waitFor();
   const diagnostics=await page.evaluate(()=>window.KNJSC_MASTER.diagnostics());
   assert.ok(diagnostics.cache<=10);report.metrics.dom.push(diagnostics);
  }
  assert.equal(report.requests.length,0,'Không được tải ảnh khi mở/cuộn lưới');
  // Đưa Bill vào vùng nhìn theo tọa độ tiêu đề/cột, không thay dữ liệu.
  await page.locator('#mg-viewport').evaluate(v=>{v.scrollTop=0;v.scrollLeft=v.scrollWidth;});
  const link=page.locator(`[data-payment-id="${fixture.document}"]`).first();await link.waitFor();
  const start=Date.now();await link.click();await page.locator('.payment-image-stage img').waitFor();
  await page.waitForFunction(()=>{const i=document.querySelector('.payment-image-stage img');return i?.complete&&i.naturalWidth>0;});
  report.metrics.billOpenMs=Date.now()-start;assert.equal(report.requests.length,1);
  await page.keyboard.press('Escape');assert.equal(await page.locator('.payment-dialog[open]').count(),0);
  await page.goto(base+'/chung-tu-thanh-toan/');await page.getByRole('heading',{name:'Chứng từ thanh toán',exact:true}).waitFor();
  for(const width of [1440,1280,390]){
   await page.setViewportSize({width,height:900});
   await page.waitForTimeout(350); // Chờ transition sidebar khi đổi breakpoint.
   const heading=await page.getByRole('heading',{name:'Chứng từ thanh toán',exact:true}).boundingBox();
   assert.ok(heading.x+heading.width<=width+1,'Tiêu đề không vượt màn hình');
   await page.screenshot({path:path.join(output,`library-${width}.png`)});report.screens.push(`library-${width}.png`);
  }
  await page.setViewportSize({width:1280,height:900});
  await page.getByRole('button',{name:'Thêm chứng từ',exact:true}).click();
  await page.locator('#payment-record option').first().waitFor({state:'attached'});
  await page.locator('#payment-create [name=reference]').fill('REF-BROWSER-00001');
  await page.locator('#payment-create [name=images]').setInputFiles({name:'synthetic.png',mimeType:'image/png',buffer:png});
  await page.evaluate(async()=>{
   const canvas=document.createElement('canvas');canvas.width=10;canvas.height=10;
   canvas.getContext('2d').fillRect(0,0,10,10);
   const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));
   await navigator.clipboard.write([new ClipboardItem({'image/png':blob})]);
  });
  await page.locator('#payment-create [name=reference]').focus();await page.keyboard.press('Control+v');
  await page.waitForFunction(()=>document.querySelector('#payment-create [name=images]').files.length===2);
  await page.getByRole('button',{name:'Lưu chứng từ',exact:true}).click();
  await page.getByRole('heading',{name:'REF-BROWSER-00001',exact:true}).waitFor();
  await page.locator('.payment-image-stage img').waitFor();
  const beforeNext=report.requests.length;await page.getByRole('button',{name:'Ảnh 2',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('.payment-image-stage img')?.complete);
  assert.equal(report.requests.length,beforeNext+1,'Chỉ tải ảnh tiếp theo khi chọn');
  await page.screenshot({path:path.join(output,'viewer.png')});
  await page.getByText('Quản lý chứng từ',{exact:true}).click();
  await page.locator('.payment-dialog[open] [name=reference]').fill('REF-BROWSER-00002');
  await page.getByRole('button',{name:'Lưu thay đổi',exact:true}).click();
  await page.getByRole('heading',{name:'REF-BROWSER-00002',exact:true}).waitFor();
  await page.keyboard.press('Escape');
  assert.deepEqual(report.errors,[]);report.ok=true;
 }catch(e){report.failure=e.stack;}finally{
  await browser.close();fs.writeFileSync(path.join(output,'result.json'),JSON.stringify(report,null,2));
  fs.writeFileSync(resultFile,JSON.stringify(report));console.log(JSON.stringify(report,null,2));
 }
 if(!report.ok)process.exitCode=1;
})();
