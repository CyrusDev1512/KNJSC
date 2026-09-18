// HTTPS hai hostname test; không dùng tài khoản hoặc database vận hành.
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),https=require('https'),http=require('http'),assert=require('assert/strict');
const folder=path.resolve(__dirname,'../storage/shared-login');
const origins={erp:'https://erp.shared.test:8445',crm:'https://crm.shared.test:8445'};
const result={ok:false,cases:[],errors:[]};
(async()=>{
 const ready=JSON.parse(fs.readFileSync(path.join(folder,'browser-ready.json')));
 const proxy=https.createServer({key:fs.readFileSync(path.join(folder,'tls-key.pem')),cert:fs.readFileSync(path.join(folder,'tls-cert.pem'))},(req,res)=>{
  const upstream=http.request({hostname:'127.0.0.1',port:8863,path:req.url,method:req.method,headers:{...req.headers,'x-forwarded-proto':'https'}},response=>{res.writeHead(response.statusCode,response.headers);response.pipe(res);});
  upstream.on('error',()=>{res.writeHead(502);res.end();});req.pipe(upstream);
 });
 await new Promise(resolve=>proxy.listen(8445,'127.0.0.1',resolve));
 const browser=await chromium.launch({channel:'chrome',headless:true,args:['--no-proxy-server','--host-resolver-rules=MAP erp.shared.test 127.0.0.1, MAP crm.shared.test 127.0.0.1','--ignore-certificate-errors-spki-list='+fs.readFileSync(path.join(folder,'tls-spki.txt'),'utf8').trim(),'--disable-features=HttpsUpgrades']});
 async function login(page,origin,user){
  await page.goto(origin+'/dang-nhap/');assert(new URL(page.url()).pathname.includes('dang-nhap'));
  await page.locator('[name=username]').fill(user);await page.locator('[name=password]').fill('matkhau-kiem-thu-1');
  await Promise.all([page.waitForURL(u=>!u.pathname.includes('dang-nhap')),page.locator('button[type=submit]').click()]);
 }
 async function logout(page){
  let button=page.locator('form[action$="/dang-xuat/"] button:visible').first();
  if(!await button.count()) {const menu=page.getByRole('button',{name:'Menu',exact:true});if(await menu.count())await menu.click();}
  button=page.locator('form[action$="/dang-xuat/"] button:visible').first();
  await Promise.all([page.waitForURL(u=>u.pathname.includes('dang-nhap')),button.click()]);
 }
 try{
  for(const width of [1440,390])for(const start of ['erp','crm'])for(const user of ['staff_sale_1','leader_sale_1','manager_sale','quan_tri']){
   const context=await browser.newContext({viewport:{width,height:900}});
   context.setDefaultTimeout(15000);context.setDefaultNavigationTimeout(20000);
   console.log(JSON.stringify({begin:{width,start,user}}));
   context.on('page',p=>p.on('pageerror',e=>result.errors.push(e.message)));
   const first=await context.newPage(),other=start==='erp'?'crm':'erp';
   if(width===390){
    await login(first,origins.erp,'staff_sale_2');
    const old=(await context.cookies()).find(c=>c.name==='knjsc_session_v2');
    await context.clearCookies();
    await context.addCookies(['erp.shared.test','crm.shared.test'].map(domain=>({name:'sessionid',value:old.value,domain,path:'/',secure:true,httpOnly:true,sameSite:'Lax'})));
   }
   await login(first,origins[start],user);
   let link=first.locator(`a[href="${origins[other]}/"]:visible`).first();
   if(!await link.count()){const menu=first.getByRole('button',{name:'Menu',exact:true});if(await menu.count())await menu.click();}
   link=first.locator(`a[href="${origins[other]}/"]:visible`).first();
   let second;
   if(await link.getAttribute('target')==='_blank'){[second]=await Promise.all([first.waitForEvent('popup'),link.click()]);await second.waitForLoadState();}
   else{await link.click();await first.waitForURL(origins[other]+'/**');second=first;}
   assert(!second.url().includes('dang-nhap'));
   const crm=await context.newPage();await crm.goto(origins.crm+'/van-don/len-don/');
   assert((await crm.locator('.vd-note').innerText()).includes(user));
   const name=`Shared Login QA ${width} ${start} ${user}`;
   await crm.locator('[name=customer_name]').fill(name);await crm.locator('[name=phone]').fill('098'+String(result.cases.length).padStart(7,'0'));
   await crm.locator('[name=market]').selectOption({label:'Hoa Kỳ'});await crm.locator('[name=currency]').selectOption('USD');await crm.locator('[name=payment_method]').selectOption({label:'Thẻ'});
   await crm.locator('[name=product]').selectOption(ready.product);await crm.locator('[name=quantity]').fill('2');await crm.locator('[name=unit_price]').fill('12.50');
   await crm.getByRole('button',{name:'Lưu đơn',exact:true}).click();await crm.locator('.vd-success').waitFor();
   await crm.goto(origins.crm+'/');
   await logout(crm);
   await second.goto(origins[other]+'/');assert(second.url().includes('dang-nhap'));
   await login(crm,origins.crm,'staff_sale_2');
   await second.goto(origins.erp+'/');assert(!second.url().includes('dang-nhap'));
   await crm.goto(origins.crm+'/van-don/len-don/');assert((await crm.locator('.vd-note').innerText()).includes('staff_sale_2'));
   const cookies=await context.cookies();const session=cookies.find(c=>c.name==='knjsc_session_v2');
   assert.equal(session.domain,'.shared.test');assert(session.secure&&session.httpOnly&&session.sameSite==='Lax');
   result.cases.push({width,start,user,shared:true,write:true,permissions:true,logout:true,switchAccount:true,legacyCookies:width===390});
   console.log(JSON.stringify(result.cases.at(-1)));await context.close();
  }
  assert.equal(result.errors.length,0);result.ok=true;
 }catch(error){result.errors.push(error.message);process.exitCode=1;}
 finally{fs.writeFileSync(path.join(folder,'browser-result.json'),JSON.stringify(result,null,2));await browser.close();await new Promise(resolve=>proxy.close(resolve));console.log(JSON.stringify({ok:result.ok,cases:result.cases.length,errors:result.errors}));}
})();
