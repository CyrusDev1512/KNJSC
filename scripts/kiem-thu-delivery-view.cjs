const fs=require('fs'),assert=require('assert'),path=require('path');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'../storage/delivery-view-verification');
const base=process.env.KN_VIEW_URL||'http://127.0.0.1:8852', grid='/bang-tinh/van_don_moi/', mode=grid+'che-do-xem/';
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});const out={ok:false,cases:[],errors:[],timings:[]};
try{
 const ready=JSON.parse(fs.readFileSync(path.join(root,'browser-ready.json'),'utf8'));
 for(const width of [1440,390]){
  const manager=await browser.newContext({viewport:{width,height:900}}),staff=await browser.newContext({viewport:{width,height:900}});
  const m=await manager.newPage(),s=await staff.newPage();
  for(const page of [m,s]){page.setDefaultTimeout(20000);page.on('pageerror',e=>out.errors.push(e.message));}
  async function login(page,user){await page.goto(base+'/dang-nhap/');await page.locator('[name=username]').fill(user);await page.locator('[name=password]').fill('matkhau-kiem-thu-1');await Promise.all([page.waitForURL(u=>!u.pathname.includes('dang-nhap')),page.locator('button[type=submit]').click()]);}
  await login(m,'view_manager');await login(s,'staff_vd');
  await m.goto(base+grid);await m.locator('#mg-more-button').click();await m.getByRole('link',{name:'Chế độ xem bảng',exact:true}).click();
  await m.locator('[name=mode][value=assigned]').check();await m.getByRole('button',{name:'Lưu thay đổi'}).click();
  await s.goto(base+grid);await s.waitForFunction(()=>window.KNJSC_MASTER?.diagnostics().total===1);
  let navigations=0;s.on('framenavigated',f=>{if(f===s.mainFrame())navigations++;});
  await m.locator('[name=mode][value=all]').check();await m.getByRole('button',{name:'Lưu thay đổi'}).click();
  await s.waitForFunction(()=>window.KNJSC_MASTER?.diagnostics().total===2);assert(navigations>0,'Trang nhân viên phải reload');
  const data=await (await staff.request.get(base+grid+'du-lieu/')).json();assert.equal(data.rows.find(r=>r.id===ready.rows[1]).editable,false);
  assert.equal((await staff.request.get(base+mode)).status(),403);
  // Đối chiếu quyền POST bằng session/CSRF thật của nhân viên.
  const csrf=(await staff.cookies()).find(c=>c.name==='csrftoken').value;
  const blocked=await staff.request.post(base+grid+'luu-json/',{headers:{'X-CSRFToken':csrf},data:{operation:crypto.randomUUID(),cells:[{id:ready.rows[1],column:'ghi_chu',old:null,value:'Không được ghi'}]}});assert.equal(blocked.status(),403);
  await s.screenshot({path:path.join(root,`staff-all-${width}.png`),fullPage:true});
  await m.screenshot({path:path.join(root,`mode-${width}.png`),fullPage:true});
  const overflow=await m.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2);assert(!overflow,'Trang cấu hình không tràn ngang');
  for(let i=0;i<15;i++){const start=performance.now();const response=await staff.request.get(base+grid+'du-lieu/');assert.equal(response.status(),200);out.timings.push({width,mode:'all',ms:performance.now()-start});}
  navigations=0;await m.locator('[name=mode][value=assigned]').check();await m.getByRole('button',{name:'Lưu thay đổi'}).click();
  await s.waitForFunction(()=>window.KNJSC_MASTER?.diagnostics().total===1);assert(navigations>0);
  for(let i=0;i<15;i++){const start=performance.now();const response=await staff.request.get(base+grid+'du-lieu/');assert.equal(response.status(),200);out.timings.push({width,mode:'assigned',ms:performance.now()-start});}
  await m.getByRole('link',{name:'Cột & cấp quyền',exact:true}).click();await m.getByRole('link',{name:'Chế độ xem bảng',exact:true}).waitFor();
  out.cases.push({width,twoWayReload:true,readonlyOthers:true,permissionLink:true,noHorizontalOverflow:true});
  await manager.close();await staff.close();
 }
 assert.equal(out.errors.length,0);out.ok=true;
}catch(e){out.errors.push(e.stack);process.exitCode=1;}finally{fs.writeFileSync(path.join(root,'browser-result.json'),JSON.stringify(out,null,2));await browser.close();console.log(JSON.stringify({ok:out.ok,cases:out.cases,errors:out.errors}));}})();
