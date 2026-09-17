const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const out=path.resolve(__dirname,'../storage/order-destination');
const base=process.env.ORDER_DESTINATION_URL||'http://127.0.0.1:8862';
(async()=>{
 const ready=JSON.parse(fs.readFileSync(path.join(out,'browser-ready.json')));
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const result={ok:false,cases:[],errors:[]};
 try {
  for(const width of [1440,390]) {
   const context=await browser.newContext({viewport:{width,height:900}});
   const page=await context.newPage();
   page.on('pageerror',e=>result.errors.push(e.message));
   await page.goto(base+'/dang-nhap/');
   await page.locator('[name=username]').fill('quan_tri');
   await page.locator('[name=password]').fill('matkhau-kiem-thu-1');
   await Promise.all([page.waitForURL(u=>!u.pathname.includes('dang-nhap')),page.locator('button[type=submit]').click()]);
   await page.goto(base+'/cau-hinh/nhan-don/');
   await page.getByLabel('Bảng nhận đơn mới').selectOption(String(ready.destination));
   await Promise.all([page.waitForNavigation(),page.getByRole('button',{name:'Lưu bảng nhận đơn'}).click()]);
   assert.equal(await page.getByLabel('Bảng nhận đơn mới').inputValue(),String(ready.destination));
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));
   await page.screenshot({path:path.join(out,`destination-${width}.png`),fullPage:true});
   await page.goto(base+'/van-don/len-don/');
   await page.locator('[name=customer_name]').fill('Destination Chrome '+width);
   await page.locator('[name=phone]').fill('090901'+String(width).padStart(4,'0'));
   await page.locator('[name=market]').selectOption({label:'Hoa Kỳ'});
   await page.locator('[name=currency]').selectOption('USD');
   await page.locator('[name=payment_method]').selectOption({label:'Thẻ'});
   await page.locator('[name=product]').selectOption(ready.product);
   await page.locator('[name=quantity]').fill('2');
   await page.locator('[name=unit_price]').fill('12.50');
   await page.getByRole('button',{name:'Lưu đơn',exact:true}).click();
   await page.locator('.vd-success').waitFor();
   assert((await page.locator('.vd-success').innerText()).includes('Vận đơn DB'));
   await page.getByRole('link',{name:'Xem đơn gốc',exact:true}).click();
   assert((await page.locator('body').innerText()).includes('Destination Chrome '+width));
   await page.goto(base+'/bang-tinh/'+ready.code+'/');
   await page.waitForFunction(()=>window.KNJSC_MASTER?.diagnostics().total>0);
   const response=await context.request.get(base+'/bang-tinh/'+ready.code+'/du-lieu/');
   assert.equal(response.status(),200);
   assert((await response.json()).rows.length>0);
   await page.goto(base+'/cau-hinh/nhan-don/');
   await page.getByLabel('Bảng nhận đơn mới').selectOption(String(ready.old));
   await Promise.all([page.waitForNavigation(),page.getByRole('button',{name:'Lưu bảng nhận đơn'}).click()]);
   assert.equal(await page.getByLabel('Bảng nhận đơn mới').inputValue(),String(ready.old));
   result.cases.push({width,configured:true,created:true,originalOrder:true,grid:true,switchedBack:true});
   await context.close();
  }
  assert.equal(result.errors.length,0);result.ok=true;
 }catch(e){result.errors.push(e.stack);process.exitCode=1;}
 finally{fs.writeFileSync(path.join(out,'browser-result.json'),JSON.stringify(result,null,2));await browser.close();console.log(JSON.stringify(result));}
})();
