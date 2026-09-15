const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const out=path.resolve(__dirname,'../storage/order-destination');
const base='http://127.0.0.1:8862';
(async()=>{
 const ready=JSON.parse(fs.readFileSync(path.join(out,'staff-ready.json')));
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const result={ok:false,orders:[],cases:[],errors:[]};
 try {
  for(const width of [1440,390]) {
   const contexts=[];
   async function login(username){
    const context=await browser.newContext({viewport:{width,height:900}});contexts.push(context);
    const page=await context.newPage();page.on('pageerror',e=>result.errors.push(e.message));
    await page.goto(base+'/dang-nhap/');
    await page.locator('[name=username]').fill(username);
    await page.locator('[name=password]').fill('matkhau-kiem-thu-1');
    await Promise.all([page.waitForURL(u=>!u.pathname.includes('dang-nhap')),page.locator('button[type=submit]').click()]);
    return page;
   }
   const admin=await login('quan_tri'),sale1=await login('staff_sale_1'),sale2=await login('staff_sale_2');
   async function choose(id){
    await admin.goto(base+'/cau-hinh/nhan-don/');
    await admin.getByLabel('Bảng nhận đơn mới').selectOption(String(id));
    await Promise.all([admin.waitForNavigation(),admin.getByRole('button',{name:'Lưu bảng nhận đơn'}).click()]);
    assert.equal(await admin.getByLabel('Bảng nhận đơn mới').inputValue(),String(id));
   }
   async function fill(page,n){
    await page.goto(base+'/van-don/len-don/');
    await page.locator('[name=customer_name]').fill(`Staff Flow ${width} ${n}`);
    await page.locator('[name=phone]').fill(`091${width.toString().padStart(4,'0')}00${n}`);
    await page.locator('[name=market]').selectOption({label:'Hoa Kỳ'});
    await page.locator('[name=currency]').selectOption('USD');
    await page.locator('[name=payment_method]').selectOption({label:'Thẻ'});
    await page.locator('[name=product]').selectOption(ready.product);
    await page.locator('[name=quantity]').fill('2');
    await page.locator('[name=unit_price]').fill('12.50');
   }
   async function save(page,n,table,seller){
    const name=`Staff Flow ${width} ${n}`;
    await page.getByRole('button',{name:'Lưu đơn',exact:true}).click();
    await page.locator('.vd-success').waitFor();
    const message=await page.locator('.vd-success').innerText();
    assert(message.includes(table===ready.destination?'Vận đơn DB':'Vận đơn'));
    if(table===ready.old) assert(!message.includes('Vận đơn DB'));
    await page.screenshot({path:path.join(out,`staff-${width}-${n}-saved.png`),fullPage:true});
    await page.getByRole('link',{name:'Xem đơn gốc',exact:true}).click();
    const body=await page.locator('body').innerText();assert(body.includes(name));assert(body.includes(seller));
    result.orders.push({name,table,seller,message});
   }
   await choose(ready.old);
   await fill(sale1,1);await save(sale1,1,ready.old,'staff_sale_1');
   await choose(ready.destination);
   await fill(sale2,2);await save(sale2,2,ready.destination,'staff_sale_2');
   await fill(sale1,3); // Form mở khi đích còn là DB.
   await choose(ready.old);
   assert.equal(await sale1.locator('[name=customer_name]').inputValue(),`Staff Flow ${width} 3`);
   await save(sale1,3,ready.old,'staff_sale_1');
   await fill(sale2,4); // Form mở khi đích còn là bảng mặc định.
   await choose(ready.destination);
   await save(sale2,4,ready.destination,'staff_sale_2');
   for(const [code,ns] of [[ready.oldCode,[1,3]],[ready.code,[2,4]]]){
    await admin.goto(base+'/bang-tinh/'+code+'/');
    await admin.waitForFunction(()=>window.KNJSC_MASTER?.diagnostics().total>0);
    // Cột tên khách của DB nằm ngoài khung mobile; cuộn ngang như người dùng.
    await admin.locator('#mg-viewport').hover();
    for(let step=0;step<25 && !(await admin.getByText(`Staff Flow ${width} ${ns[0]}`,{exact:true}).first().isVisible());step++){
     await admin.mouse.wheel(180,0);await admin.waitForTimeout(120);
    }
    for(const n of ns) await admin.getByText(`Staff Flow ${width} ${n}`,{exact:true}).first().waitFor();
    const text=await admin.locator('body').innerText();
    for(const n of [1,2,3,4].filter(n=>!ns.includes(n))) assert(!text.includes(`Staff Flow ${width} ${n}`));
    await admin.screenshot({path:path.join(out,`staff-${width}-${code}-grid.png`),fullPage:true});
   }
   const forbidden=await sale1.goto(base+'/cau-hinh/nhan-don/');assert.equal(forbidden.status(),403);
   await choose(ready.old);
   result.cases.push({width,separateSessions:true,freshForms:true,staleFormsBothDirections:true,adminGridVerified:true,saleCannotConfigure:true});
   for(const context of contexts) await context.close();
  }
  assert.equal(result.errors.length,0);result.ok=true;
 }catch(e){result.errors.push(e.stack);process.exitCode=1;}
 finally{fs.writeFileSync(path.join(out,'staff-result.json'),JSON.stringify(result,null,2));await browser.close();console.log(JSON.stringify(result));}
})();
