/* Mô phỏng het-phien.js (ADR-053): mã người mở trang, CSRF mới lúc gửi, cookie trùng tên lấy cái sau cùng, phân loại lỗi phiên. Chạy tay: node scripts/kiem-thu-het-phien-unit.cjs */
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const src=fs.readFileSync(process.argv[2]||require.resolve('../app/static/js/het-phien.js'),'utf8');
const calls=[];const listeners={};
const ctx={URL,Headers,FormData,URLSearchParams,Request,Object,String,Error,JSON,encodeURIComponent,decodeURIComponent,
  location:{href:'http://crm.test/bang-tinh/van_don/?trang=2',origin:'http://crm.test',pathname:'/bang-tinh/van_don/',search:'?trang=2'},
  document:{currentScript:{dataset:{nguoi:'7',ma:'THUANLT',dangNhap:'/dang-nhap/',doiMatKhau:'/doi-mat-khau/',csrfCookie:'knjsc_csrf_v2'}},
    cookie:'knjsc_csrf_v2=cu111; other=1; knjsc_csrf_v2=moi222',addEventListener:(n,f)=>{listeners[n]=f;},
    createElement:t=>({tagName:t,dataset:{},appendChild(){},setAttribute(){},style:{}})}};
ctx.window=ctx;ctx.fetch=async(input,init)=>{calls.push({input,init});return {ok:true};};
vm.createContext(ctx);vm.runInContext(src,ctx);
(async()=>{
  const S=ctx.KNJSC_SESSION;
  assert.equal(S.csrfToken(),'moi222','Cookie trùng tên: lấy cái sau cùng như Django');
  await ctx.fetch('/bang-tinh/van_don/du-lieu/?offset=0');
  assert.equal(calls[0].init.headers.get('X-KNJSC-User'),'7');assert.equal(calls[0].init.headers.get('X-CSRFToken'),null,'GET không mang CSRF');
  const fd=new FormData();fd.set('csrfmiddlewaretoken','cu111');fd.set('note','x');
  await ctx.fetch('/chung-tu-thanh-toan/tao/',{method:'post',body:fd,headers:{'X-CSRFToken':'cu111'}});
  assert.equal(calls[1].init.headers.get('X-CSRFToken'),'moi222');assert.equal(fd.get('csrfmiddlewaretoken'),'moi222','Tham số CSRF trong FormData lấy mã mới');
  await ctx.fetch('https://erp.test/x',{method:'POST'});
  assert.equal(calls[2].init.headers,undefined,'Khác nguồn: không gắn gì');
  // htmx configRequest
  const det={headers:{'X-CSRFToken':'cu111'},verb:'post',parameters:{csrfmiddlewaretoken:'cu111'}};listeners['htmx:configRequest']({detail:det});
  assert.equal(det.headers['X-KNJSC-User'],'7');assert.equal(det.headers['X-CSRFToken'],'moi222');assert.equal(det.parameters.csrfmiddlewaretoken,'moi222');
  const g={headers:{},verb:'get',parameters:{q:'a'}};listeners['htmx:configRequest']({detail:g});
  assert.equal(g.headers['X-KNJSC-User'],'7');assert.equal(g.headers['X-CSRFToken'],undefined);
  // sessionError
  assert.equal(S.sessionError({redirected:true,url:'http://crm.test/dang-nhap/?next=/x'},null).code,'het_phien');
  assert.equal(S.sessionError({redirected:true,url:'http://crm.test/doi-mat-khau/'},null).code,'doi_mat_khau');
  assert.equal(S.sessionError({redirected:false},{code:'nguoi_dung_doi',error:'Tài khoản vừa đăng nhập khác người mở trang — nháp không được lưu'}).code,'nguoi_dung_doi');
  assert.equal(S.sessionError({redirected:false,status:403},{error:'Bạn không còn quyền'}),null,'403 mất quyền không phải lỗi phiên');
  console.log('PASS het-phien: mã người, CSRF mới lúc gửi, cookie sau cùng, khác nguồn không gắn, phân loại lỗi phiên');
})().catch(e=>{console.error(e);process.exitCode=1;});
