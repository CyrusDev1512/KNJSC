/* Database test do pytest dựng; không dùng dữ liệu vận hành. */
const {chromium}=require('playwright'), fs=require('fs'), path=require('path'), assert=require('assert/strict');
const root=path.resolve(__dirname,'..');
const ready=JSON.parse(fs.readFileSync(path.join(root,'app/.order-hub-ready.json')));
assert(ready.database.startsWith('test_'));
const base='http://127.0.0.1:8812', results=[], errors=[];
async function login(page,user){
 await page.context().clearCookies();await page.goto(base+'/dang-nhap/');
 await page.locator('[name=username]').fill(user);
 await page.locator('[name=password]').fill('matkhau-kiem-thu-1');
 await Promise.all([page.waitForURL(u=>!u.pathname.includes('dang-nhap')),page.locator('button[type=submit]').click()]);
}
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 try {
  for(const width of [1440,390]){
   const context=await browser.newContext({viewport:{width,height:900}}),page=await context.newPage();
   page.on('pageerror',e=>errors.push(e.message));
   await page.clock.install();
   await login(page,'staff_sale_1');
   const started=Date.now();await page.goto(base+'/van-don/len-don/');
   results.push({width,operation:'entry_load',ms:Date.now()-started});
   assert(await page.locator('#order-date').getAttribute('readonly')!==null);
   const stamp=await page.locator('#order-date').inputValue();
   assert.match(stamp,/^\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}$/);
   await page.clock.fastForward(61000);
   assert.notEqual(await page.locator('#order-date').inputValue(),stamp,'Giờ phải cập nhật khi vẫn mở form');
   assert((await page.locator('.vd-note').textContent()).includes('Sale đứng đơn: staff_sale_1'));
   await page.locator('[name=customer_name]').fill('Test đơn vị '+width);
   await page.locator('[name=phone]').fill('091'+width);
   await page.locator('[name=product]').selectOption(ready.products[0]);
   assert.equal(await page.locator('[name=unit]').inputValue(),'cái');
   await page.locator('[name=unit]').selectOption('hộp');
   await page.locator('[name=quantity]').fill('2');
   await page.locator('[name=unit_price]').fill('10.10');
   await page.getByRole('button',{name:'Thêm sản phẩm',exact:true}).click();
   assert.equal(await page.locator('[name=unit]').last().inputValue(),'');
   await page.locator('[name=product]').last().selectOption(ready.products[1]);
   await page.locator('[name=unit]').last().selectOption('túi');
   await page.locator('[name=unit_price]').last().fill('5.20');
   for(const [name,value] of [['market','us'],['currency','USD'],['payment_method','card']]){
    const select=page.locator(`[name=${name}]`);
    assert.equal(await select.inputValue(),'');
    assert(await select.evaluate(el=>el.required&&el.validity.valueMissing));
    await page.getByRole('button',{name:'Lưu đơn',exact:true}).click();
    assert.equal(await page.getByRole('link',{name:'Xem đơn gốc',exact:true}).count(),0);
    await select.selectOption(value);
   }
   await page.locator('[data-order-summary]').filter({hasText:/25.40/}).waitFor();
   // Lưu lỗi phải giữ đơn vị và mọi dòng đã nhập.
   await page.locator('[name=unit_price]').last().fill('-1');
   await page.getByRole('button',{name:'Lưu đơn',exact:true}).click();
   await page.locator('#vd-entry [role=alert]').waitFor();
   assert.deepEqual(await page.locator('[name=unit]').evaluateAll(els=>els.map(e=>e.value)),['hộp','túi']);
   await page.locator('[name=unit_price]').last().fill('5.20');
   const saved=Date.now();await page.getByRole('button',{name:'Lưu đơn',exact:true}).click();
   await page.getByRole('link',{name:'Xem đơn gốc',exact:true}).waitFor();
   results.push({width,operation:'order_save',ms:Date.now()-saved});
   assert.match(await page.locator('#vd-entry [role=status]').first().textContent(),/lúc \d{2}:\d{2} ngày/);
   const original=await page.getByRole('link',{name:'Xem đơn gốc',exact:true}).getAttribute('href');
   assert.equal(await page.locator('[name=unit]').count(),1);
   for(const name of ['market','currency','payment_method']) assert.equal(await page.locator(`[name=${name}]`).inputValue(),'');
   await page.goto(base+original);
   assert(await page.getByRole('cell',{name:'hộp',exact:true}).count());
   assert(await page.getByRole('cell',{name:'túi',exact:true}).count());
   assert(await page.getByText(/^25[,.]40 USD$/).count());
   assert((await page.locator('.trang-dau').textContent()).includes('staff_sale_1'));
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   fs.mkdirSync(path.join(root,'storage/order-entry-screens'),{recursive:true});
   await page.screenshot({path:path.join(root,'storage/order-entry-screens',`original-${width}.png`)});
   await login(page,'quan_tri');await page.goto(base+'/van-don/len-don/');
   assert.equal(await page.locator('[name=seller]').count(),0);
   assert((await page.locator('.vd-note').textContent()).includes('Sale đứng đơn: quan_tri'));
   await page.locator('[name=customer_name]').fill('Admin thử '+width);
   await page.locator('[name=phone]').fill('092'+width);
   await page.locator('[name=product]').selectOption(ready.products[0]);
   await page.locator('[name=unit]').selectOption('chiếc');
   for(const [name,value] of [['market','us'],['currency','USD'],['payment_method','card']]){
    assert.equal(await page.locator(`[name=${name}]`).inputValue(),'');
    await page.locator(`[name=${name}]`).selectOption(value);
   }
   await page.getByRole('button',{name:'Lưu đơn',exact:true}).click();
   await page.getByRole('link',{name:'Xem đơn gốc',exact:true}).click();
   assert((await page.locator('.trang-dau').textContent()).includes('quan_tri'));
   assert((await page.getByRole('row').filter({hasText:'Sale đứng đơn'}).textContent()).includes('quan_tri'));
   await page.goto(base+'/bang-tinh/van_don_moi/?f_ma_don='+ready.order);
   await page.locator('#mg-count').filter({hasText:/dòng/}).waitFor();
   for(let i=0;i<30&&!(await page.locator('.mg-cell[data-code="san_pham"]').count());i++){
    await page.locator('#mg-viewport').evaluate(el=>el.scrollLeft+=250);await page.waitForTimeout(80);
   }
   await page.locator('.mg-cell[data-code="san_pham"]').first().dblclick();
   await page.locator('#vd-detail-body [name=unit]').first().selectOption('hộp');
   await page.getByRole('button',{name:'Lưu chi tiết',exact:true}).click();
   await page.locator('#vd-detail').waitFor({state:'hidden'});
   await page.locator('.mg-cell[data-code="san_pham"]').first().dblclick();
   assert.equal(await page.locator('#vd-detail-body [name=unit]').first().inputValue(),'hộp');
   const [originalTab]=await Promise.all([page.waitForEvent('popup'),page.locator('#vd-detail-body').getByRole('link',{name:'Xem đơn gốc',exact:true}).click()]);
   await originalTab.waitForLoadState();
   assert(await originalTab.getByRole('cell',{name:'cái',exact:true}).count());
   await originalTab.close();
   results.push({width,operation:'waybill_unit_edit_preserves_original',ok:true});
   await context.close();
  }
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(root,'storage/order-required-choices-browser.json'),JSON.stringify({ok:true,results,errors},null,2));
  console.log(JSON.stringify({ok:true,results}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
