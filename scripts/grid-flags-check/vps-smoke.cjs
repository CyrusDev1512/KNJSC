/* Kiểm đọc trên domain thật; không tạo đơn, sửa ô hoặc xuất dữ liệu khách. */
const {chromium}=require('playwright');
const {execFileSync}=require('child_process');
const fs=require('fs'),crypto=require('crypto'),assert=require('node:assert/strict');
const ssh=['-p','24700','-i','C:/Users/PC/.ssh/knjsc_vps_pc_ed25519','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','deploy@103.57.221.52'];
const privateText=execFileSync('ssh',[...ssh,'cat /opt/knjsc-runtime/initial-admin.txt'],{encoding:'utf8'});
const username=privateText.match(/^Username:\s*(.+)$/m)?.[1]?.trim();
const password=privateText.match(/^Password:\s*(.+)$/m)?.[1]?.trim();
if(!username||!password)throw Error('Không đọc được tài khoản kiểm');
const expected=process.argv[2];assert.match(expected||'',/^[0-9a-f]{64}$/);
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const result={errors:[],viewports:[]};
 try{
  const anonymous=await browser.newContext(),anon=await anonymous.newPage();
  await anon.goto('https://crm.thnsolution.io.vn/bang-tinh/van_don/');
  assert(new URL(anon.url()).pathname.includes('dang-nhap'));result.anonymousBlocked=true;
  await anonymous.close();
  const context=await browser.newContext(),page=await context.newPage();
  page.on('pageerror',e=>result.errors.push(e.message));
  page.on('response',r=>{if(r.status()>=500)result.errors.push(`HTTP ${r.status()} ${new URL(r.url()).pathname}`);});
  await page.goto('https://crm.thnsolution.io.vn/dang-nhap/');
  await page.locator('[name=username]').fill(username);
  await page.locator('[name=password]').fill(password);
  await Promise.all([page.waitForURL(u=>!u.pathname.includes('dang-nhap')),page.locator('button[type=submit]').click()]);
  for(const width of [1440,390]){
   await page.setViewportSize({width,height:900});
   assert.equal((await page.goto('https://crm.thnsolution.io.vn/bang-tinh/van_don/')).status(),200);
   await page.locator('.mg-cell').first().waitFor({timeout:30000});
   const src=await page.locator('script[src*="/master-grid.js"]').getAttribute('src');
   const script=await page.request.get(new URL(src,page.url()).href);assert.equal(script.status(),200);
   const hash=crypto.createHash('sha256').update(await script.body()).digest('hex');assert.equal(hash,expected);
   const flags=await page.evaluate(()=>{const c=JSON.parse(document.getElementById('mg-config').textContent);return {render:!!c.renderOptimized,protocol:c.protocol};});
   assert.equal(flags.render,false);
   await page.locator('#mg-viewport').evaluate(el=>{el.scrollTop=280;el.scrollLeft=200;});
   await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
   await page.locator('.mg-cell').first().click();
   await page.waitForFunction(()=>!!document.getElementById('mg-selection').textContent);
   const state=await page.evaluate(()=>({grid:KNJSC_MASTER.diagnostics(),selection:!!document.getElementById('mg-selection').textContent}));
   assert(state.selection);assert(state.grid.cache<=10);assert(state.grid.cells>0);
   result.viewports.push({width,hash,flags,...state});
  }
  await page.goto('https://erp.thnsolution.io.vn/');
  assert(!new URL(page.url()).pathname.includes('dang-nhap'));result.sharedSession=true;
  assert.deepEqual(result.errors,[]);
  result.ok=true;
  fs.writeFileSync('storage/grid-flags-20260916/results/vps-smoke.json',JSON.stringify(result,null,2));
  console.log(JSON.stringify(result));
  await context.close();
 }catch(error){console.error(String(error.message).replaceAll(password,'[REDACTED]'));process.exitCode=1;}
 finally{await browser.close();}
})();
