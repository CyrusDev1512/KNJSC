/* Chỉ kiểm đọc local; kiểm ghi dùng master-ui cùng pytest DB test. */
const {chromium}=require('playwright'),path=require('path'),fs=require('fs'),assert=require('assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'chrome'});
 const page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];
 const base=process.env.KN_CRM_URL||'http://127.0.0.1:8021';
 const out=path.resolve(__dirname,'../.agents/design-state/review/waybill');fs.mkdirSync(out,{recursive:true});
 page.on('pageerror',e=>errors.push(e.message));
 try{
   await page.goto(base+'/dang-nhap/');
   await page.locator('[name=username]').fill(process.env.KN_TEST_USER||'quantri');
   await page.locator('[name=password]').fill(process.env.KN_TEST_PASSWORD||'matkhaucuatoi');
   await Promise.all([page.waitForURL(u=>!u.pathname.includes('dang-nhap')),page.locator('button[type=submit]').click()]);
   await page.goto(base+'/van-don/len-don/');
   await page.getByRole('button',{name:'Thêm sản phẩm',exact:true}).click();
   assert.equal(await page.locator('.vd-items tbody tr').count(),2);
   await page.locator('.vd-items tbody tr').last().getByRole('button',{name:'Bỏ dòng'}).click();
   assert.equal(await page.locator('.vd-items tbody tr').count(),1);
   for(const width of [1440,390]){
     await page.setViewportSize({width,height:900});
     await page.goto(base+'/bang-tinh/van_don_moi/');await page.locator('#mg-count').filter({hasText:/dòng/}).waitFor();
     assert.equal(await page.locator('#vd-entry,#vd-statistics').count(),0);
     assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
     await page.screenshot({path:path.join(out,`grid-${width}.png`)});
     await page.goto(base+'/thong-ke/');await page.getByRole('heading',{name:'Thống kê Vận đơn',exact:true}).waitFor();
     assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
     await page.screenshot({path:path.join(out,`statistics-${width}.png`)});
   }
   assert.deepEqual(errors,[]);console.log('PASS: Lên đơn, lưới master và Thống kê desktop/mobile; chỉ kiểm đọc.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
