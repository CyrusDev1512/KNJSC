/* Mô phỏng het-phien.js (ADR-053): mã người mở trang, CSRF mới lúc gửi, cookie trùng tên lấy cái sau cùng, phân loại lỗi phiên. Chạy tay: node scripts/kiem-thu-het-phien-unit.cjs */
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const src=fs.readFileSync(process.argv[2]||require.resolve('../app/static/js/het-phien.js'),'utf8');
const calls=[];const listeners={};
const ctx={URL,Headers,FormData,URLSearchParams,Request,Object,String,Error,JSON,encodeURIComponent,decodeURIComponent,
  location:{href:'http://crm.test/bang-tinh/van_don/?trang=2',origin:'http://crm.test',pathname:'/bang-tinh/van_don/',search:'?trang=2'},
  document:{currentScript:{dataset:{nguoi:'7',ma:'THUANLT',dangNhap:'/dang-nhap/',doiMatKhau:'/doi-mat-khau/',csrfCookie:'knjsc_csrf_v2'}},
    cookie:'knjsc_csrf_v2=cu111; other=1; knjsc_csrf_v2=moi222',addEventListener:(n,f)=>{listeners[n]=f;},
    createElement:t=>{const e={tagName:t,dataset:{},style:{},setAttribute(){},appendChild(c){if(!e.firstChild)e.firstChild=c;}};return e;},
    querySelector:()=>null,body:{appendChild(){}},documentElement:{}}};
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
  assert.equal(S.sessionError({redirected:false,ok:false,status:409},{code:'nguoi_dung_doi',error:'Tài khoản vừa đăng nhập khác người mở trang — nháp không được lưu'}).code,'nguoi_dung_doi');
  assert.equal(S.sessionError({redirected:false,ok:false,status:403},{code:'csrf',error:'Mã bảo mật của trang không còn khớp'}).code,'csrf');
  assert.equal(S.sessionError({redirected:false,ok:false,status:403},{error:'Bạn không còn quyền'}),null,'403 mất quyền không phải lỗi phiên');
  assert.equal(S.sessionError({redirected:false,ok:true,status:200},{code:'csrf',name:'CSRF'}),null,'Phản hồi 200 có khoá code (mã sản phẩm "csrf") không phải lỗi phiên');
  assert.equal(S.sessionError({redirected:false,ok:true,status:200},{code:'nguoi_dung_doi',name:'Người dùng đổi'}),null,'Phản hồi 200 có code "nguoi_dung_doi" cũng không phải lỗi phiên');
  // htmx: phần tử gửi bị tách khỏi trang thì sự kiện không nổi lên document — nghe ngay trên phần tử; nổi lên rồi thì không xử lý lần hai
  const eltNghe={},elt={addEventListener:(n,f)=>{eltNghe[n]=f;}};
  listeners['htmx:configRequest']({detail:{elt,headers:{},verb:'get',parameters:{}}});
  assert.equal(typeof eltNghe['htmx:beforeOnLoad'],'function','Nghe htmx:beforeOnLoad ngay trên phần tử gửi');
  let ghi=0,chan=0;
  const dich={isConnected:true,querySelector:()=>null,replaceChildren(){ghi++;},closest:()=>null};
  const xhr={status:200,responseURL:'',getResponseHeader:h=>h==='HX-Redirect'?'/dang-nhap/?next=/bang-tinh/van_don/':''};
  const ev={detail:{xhr,target:dich,elt},preventDefault(){chan++;}};
  eltNghe['htmx:beforeOnLoad'](ev);listeners['htmx:beforeOnLoad'](ev);
  assert.equal(chan,1,'Chặn HX-Redirect về đăng nhập đúng một lần');assert.equal(ghi,1,'Lời báo ghi vào đích đúng một lần');
  // htmx 403 không mã (từ chối thật, không phải phiên): báo "không có quyền", không kèm liên kết đăng nhập lại
  let noiDung=null,chan2=0;const dich2={isConnected:true,querySelector:()=>null,replaceChildren(p){noiDung=p;},closest:()=>null};
  const xhr403={status:403,responseURL:'http://crm.test/van-don/chi-tiet/5/',getResponseHeader:h=>h==='Content-Type'?'text/html; charset=utf-8':''};
  listeners['htmx:beforeOnLoad']({detail:{xhr:xhr403,target:dich2,elt:{}},preventDefault(){chan2++;}});
  assert.equal(chan2,1,'Không dán trang 403 vào chỗ đích');assert.ok(noiDung.textContent.includes('không có quyền'),'403 thường: báo không có quyền');
  assert.equal(noiDung.firstChild,undefined,'403 thường: không kèm liên kết đăng nhập lại');
  console.log('PASS het-phien: mã người, CSRF mới lúc gửi, cookie sau cùng, khác nguồn không gắn, phân loại lỗi phiên theo mã trạng thái, phần tử bị tách vẫn chặn được');
})().catch(e=>{console.error(e);process.exitCode=1;});
