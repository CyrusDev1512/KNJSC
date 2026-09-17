/* Chỉ chạy khi pytest đã dựng database test và hai server riêng. */
const {chromium}=require('playwright'), fs=require('fs'), path=require('path'), assert=require('assert/strict');
const root=path.resolve(__dirname,'..'), ready=JSON.parse(fs.readFileSync(path.join(root,'app/.order-hub-ready.json')));
assert(ready.database.startsWith('test_'));
const erp='http://127.0.0.1:8811', crm='http://127.0.0.1:8812';
const results=[], errors=[];
async function login(page,base,user){
  await page.context().clearCookies();
  await page.goto(base+'/dang-nhap/');
  await page.locator('[name=username]').fill(user);
  await page.locator('[name=password]').fill('matkhau-kiem-thu-1');
  await Promise.all([page.waitForURL(u=>!u.pathname.includes('dang-nhap')),page.locator('button[type=submit]').click()]);
}
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 try {
  for(const width of [1440,390]){
   const context=await browser.newContext({viewport:{width,height:900}}), page=await context.newPage();
   page.on('pageerror',e=>errors.push(e.message));
   await login(page,erp,'quan_tri');
   let start=Date.now();await page.goto(erp+'/bieu-mau/');
   await page.getByRole('heading',{name:'Biểu mẫu & tài liệu',exact:true}).waitFor();
   results.push({width,operation:'forms_load',ms:Date.now()-start});
   assert(await page.getByText('Biểu mẫu thử 0000',{exact:true}).count());
   assert.equal(await page.locator('.nav-than').getByText('KN CRM',{exact:true}).count(),0);
   assert(await page.locator('.nav-than').getByText('Bảng dữ liệu',{exact:true}).count());
   const crmLink=page.getByRole('link',{name:'Mở KN CRM trong tab mới'});
   assert.equal(await crmLink.getAttribute('href'),crm+'/');
   const [popup]=await Promise.all([page.waitForEvent('popup'),crmLink.click()]);
   await popup.waitForLoadState();assert(popup.url().startsWith(crm));await popup.close();
   await page.getByRole('navigation',{name:'Biểu mẫu và tài liệu'}).getByRole('link',{name:'Tài liệu',exact:true}).click();
   await page.locator('[name=tim]').fill('Tài liệu thử');
   start=Date.now();await page.getByRole('button',{name:'Lọc',exact:true}).click();
   await page.waitForURL(/tim=/);results.push({width,operation:'documents_filter',ms:Date.now()-start});
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'Trang ERP tràn ngang');
   await page.goto(erp+'/bieu-mau/?tab=documents&trang=2');assert(await page.locator('.phan-trang').count());
   await page.goto(erp+'/bang/');assert.equal(await page.getByText('Bảng E2E',{exact:true}).count()>0,true);
   await login(page,crm,'staff_sale_1');
   await page.goto(crm+'/van-don/len-don/');
   await page.locator('[name=customer_name]').fill('Khách E2E '+width);
   await page.locator('[name=phone]').fill('090'+width);
   await page.locator('[name=facebook]').fill('FB thử');
   await page.locator('[name=email]').fill('e2e@example.test');
   await page.locator('[name=market]').selectOption('us');
   await page.locator('[name=currency]').selectOption('USD');
   await page.locator('[name=payment_method]').selectOption('card');
   await page.locator('[name=product]').selectOption(ready.products[0]);
   await page.locator('[name=quantity]').fill('2');
   await page.locator('[name=unit_price]').fill('10.10');
   await page.getByRole('button',{name:'Thêm sản phẩm',exact:true}).click();
   await page.locator('[name=product]').last().selectOption(ready.products[1]);
   await page.locator('[name=unit_price]').last().fill('5.20');
   await page.locator('[data-order-summary]').filter({hasText:/25.40/}).waitFor();
   start=Date.now();await page.getByRole('button',{name:'Lưu đơn',exact:true}).click();
   await page.getByRole('link',{name:'Xem đơn gốc',exact:true}).waitFor();
   results.push({width,operation:'order_save',ms:Date.now()-start});
   await page.getByRole('link',{name:'Xem đơn gốc',exact:true}).click();
   await page.getByText('Đơn đã lưu không sửa được',{exact:true}).waitFor();
   assert(await page.getByText(/^25[,.]40 USD$/).count());
   await login(page,erp,'staff_sale_1');
   await page.goto(erp+'/bieu-mau/');
   assert.equal(await page.getByRole('navigation',{name:'Biểu mẫu và tài liệu'}).getByRole('link',{name:'Biểu mẫu',exact:true}).count(),0);
   assert.equal((await page.goto(erp+'/bieu-mau/?tab=forms')).status(),403);
   for(const role of ['leader_sale_1','manager_sale']) {
    await login(page,erp,role);await page.goto(erp+'/bieu-mau/');
    assert.equal(await page.getByRole('navigation',{name:'Biểu mẫu và tài liệu'}).getByRole('link',{name:'Biểu mẫu',exact:true}).count(),role==='manager_sale'?1:0);
   }
   await login(page,crm,'quan_tri');await page.goto(crm+'/van-don/len-don/');
   await page.locator('[data-product-name]').fill('Sản phẩm E2E '+width+' '+Date.now());
   await page.getByRole('button',{name:'Tạo sản phẩm',exact:true}).click();
   await page.locator('[data-product-result]').filter({hasText:'Đã tạo sản phẩm'}).waitFor();
   await page.goto(crm+'/bang-tinh/van_don_moi/?f_ma_don='+ready.order);
   await page.locator('#mg-count').filter({hasText:/dòng/}).waitFor();
   const cell=page.locator('.mg-cell[data-r="0"][data-code="bang"]');
   for(let i=0;i<30&&!(await cell.count());i++){await page.locator('#mg-viewport').evaluate(el=>el.scrollLeft+=150);await page.waitForTimeout(80);}
   await cell.waitFor();
   await page.route('**/luu-json/',route=>route.abort());
   await cell.dblclick();await page.locator('#mg-editor input').fill('Nháp E2E');await page.keyboard.press('Enter');
   const viewport=page.locator('#mg-viewport');
   for(let i=0;i<20&&!(await page.locator('.mg-cell[data-code="san_pham"]').count());i++) {
    await viewport.evaluate(el=>el.scrollLeft+=300);await page.waitForTimeout(80);
   }
   await page.locator('.mg-cell[data-code="san_pham"]').first().dblclick();
   const link=page.locator('#vd-detail-body').getByRole('link',{name:'Xem đơn gốc',exact:true});
   const [original]=await Promise.all([page.waitForEvent('popup'),link.click()]);
   await original.waitForLoadState();assert(original.url().includes(ready.order));await original.close();
   assert(!['Đã lưu',''].includes(await page.locator('#bt-trang-thai').textContent()),'Mở đơn gốc không được xóa nháp chưa gửi');
   await page.getByRole('button',{name:'Đóng chi tiết sản phẩm',exact:true}).click();
   fs.mkdirSync(path.join(root,'storage/erp-hub-screens'),{recursive:true});
   await page.screenshot({path:path.join(root,'storage/erp-hub-screens','grid-'+width+'.png')});
   results.push({width,operation:'original_order_keeps_draft',ok:true});
   await context.close();
  }
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(root,'storage/erp-hub-browser.json'),JSON.stringify({ok:true,results,errors},null,2));
  console.log(JSON.stringify({ok:true,results}));
 } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
