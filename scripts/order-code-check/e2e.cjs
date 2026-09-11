const fs=require('fs'),path=require('path'),assert=require('assert'),{spawn}=require('child_process'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),manifest=JSON.parse(fs.readFileSync(path.join(root,'ready.json'))),base='http://127.0.0.1:8851',sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});const results={cases:[],orders:[],errors:[]};
try{for(const width of [1440,390]){for(const role of ['sale','admin']){
 const actor=manifest.users.find(u=>u.role===role&&u.index===0);const ctx=await browser.newContext({viewport:{width,height:900}});await ctx.addCookies([{name:'sessionid',value:actor.session,url:base}]);const p=await ctx.newPage();p.setDefaultTimeout(15000);p.on('pageerror',e=>results.errors.push(e.message));
 await p.goto(base+'/van-don/len-don/');assert(await p.locator('#vd-entry').innerText().then(t=>t.includes(actor.username)));
 const phone='E2E-'+width+'-'+role+'-'+Date.now();await p.locator('[name="customer_name"]').fill('Khach TEST E2E');await p.locator('[name="phone"]').fill(phone);
 for(const key of ['market','currency','payment_method'])assert.equal(await p.locator('[name="'+key+'"]').inputValue(),'');
 await p.locator('[name="market"]').selectOption(manifest.market);await p.locator('[name="currency"]').selectOption('USD');await p.locator('[name="payment_method"]').selectOption(manifest.payment);
 await p.locator('[data-add-item]').click();
 for(let i=0;i<2;i++){await p.locator('[name="product"]').nth(i).selectOption(manifest.products[i]);await p.locator('[name="unit"]').nth(i).selectOption(i?'túi':'hộp');await p.locator('[name="quantity"]').nth(i).fill(i?'1':'2');await p.locator('[name="unit_price"]').nth(i).fill(i?'20.20':'10.10');}
 if(role==='sale'){
  const holder=spawn('docker',['exec','knjsc-code-app','python','/harness/hold_lock.py'],{stdio:'ignore',windowsHide:true});const heldExit=new Promise(r=>holder.once('exit',r));
  try{for(let i=0;i<100&&!fs.existsSync(path.join(root,'lock-ready'));i++)await sleep(100);assert(fs.existsSync(path.join(root,'lock-ready')),'Holder ready');
   const start=Date.now();const rejected=p.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname==='/van-don/len-don/');await p.getByRole('button',{name:'Lưu đơn',exact:true}).click();assert.equal((await rejected).status(),400);
   await p.getByRole('alert').filter({hasText:'Hệ thống đang bận cấp mã đơn. Vui lòng thử lại.'}).waitFor();assert.equal(await p.locator('[name="phone"]').inputValue(),phone);assert.equal(await p.locator('[name="product"]').nth(1).inputValue(),manifest.products[1]);assert.equal(await p.locator('[name="unit_price"]').nth(1).inputValue(),'20.20');
   results.cases.push({width,role,case:'timeout-keeps-form',ms:Date.now()-start});
  }finally{fs.writeFileSync(path.join(root,'release-lock'),'release');assert.equal(await heldExit,0);}
 }
 const saved=p.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname==='/van-don/len-don/');await p.getByRole('button',{name:'Lưu đơn',exact:true}).click();assert.equal((await saved).status(),200);const link=p.getByRole('link',{name:'Xem đơn gốc',exact:true});await link.waitFor();const href=await link.getAttribute('href'),code=href.split('/').filter(Boolean).at(-1);results.orders.push({code,actor:actor.id,phone});
 assert.equal(await p.locator('[name="phone"]').inputValue(),'');await link.click();await p.waitForURL('**'+href);assert((await p.locator('body').innerText()).includes(code));assert((await p.locator('body').innerText()).includes(phone));
 await p.screenshot({path:path.join(root,'results',`e2e-${width}-${role}.png`),fullPage:true});results.cases.push({width,role,case:'save-two-products-and-original',code});
 const other=manifest.users.find(u=>u.role==='sale'&&u.index===1);const outsider=await browser.newContext();await outsider.addCookies([{name:'sessionid',value:other.session,url:base}]);assert.equal((await outsider.request.get(base+href)).status(),404);await outsider.close();
 const vd=manifest.users.find(u=>u.role==='delivery'&&u.index===9);const vc=await browser.newContext();await vc.addCookies([{name:'sessionid',value:vd.session,url:base}]);const rows=await vc.request.get(base+'/bang-tinh/van_don_moi/du-lieu/?tim='+encodeURIComponent(phone));assert.equal(rows.status(),200);assert.equal((await rows.json()).rows.length,0);await vc.close();results.cases.push({width,role,case:'outside-scope-hidden'});await ctx.close();
}}
}catch(e){results.errors.push(e.stack);process.exitCode=1;}finally{fs.writeFileSync(path.join(root,'results/e2e.json'),JSON.stringify(results,null,2));await browser.close();console.log(JSON.stringify(results));}})();
