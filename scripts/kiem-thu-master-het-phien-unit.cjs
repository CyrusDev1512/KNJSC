/* Mô phỏng: lượt hoàn tác/xoá dòng chưa xác nhận + lỗi phiên; lượt hỏi khi mất phiên (ADR-053). */
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const src=fs.readFileSync(process.argv[2]||require.resolve('../app/static/js/master-grid.js'),'utf8');
const cut=(a,b)=>src.slice(src.indexOf(a),src.indexOf(b));
(async()=>{
  // 1. rowRetry còn + ô chờ lưu: tự lưu không gửi gì, không đệ quy; bấm Lưu gửi đúng một lượt cũ; lỗi phiên giữ lượt
  const code=cut('  async function travelCreated(','  // Xoá dòng — chỉ Admin')+cut('  async function travelDeleted(','  function scheduleSave(')+cut('  async function saveAll(','  async function retainReadableDrafts(');
  const sent=[],notices=[];
  const ctx={state:{busy:false,rowRetry:null,retry:null,conflicts:[]},working:{count:1,pending:()=>[{id:1}],undo:[],redo:[]},
    fetch:async(url,o)=>{sent.push(JSON.parse(o.body));throw Object.assign(Error('Phiên đăng nhập đã hết'),{status:401,code:'het_phien',session:true});},
    json:x=>x,status(){},message(){},element:()=>({}),$:()=>({append(){}}),refreshStatus(){},finishEditor:()=>true,
    crypto:{randomUUID:()=>'moi'},config:{saveUrl:'/s'},csrf:'t',invalidate(){},sessionNotice:e=>notices.push(e.code)};
  vm.createContext(ctx);vm.runInContext(code+';globalThis.saveAll=saveAll;',ctx);
  const step=[];step.deletedRows=[{id:5,version:'v'}];
  ctx.state.rowRetry={payload:{operation:'cu',kind:'delete_rows',cells:[],row_changes:[]},step,redo:true,fresh:true};
  await ctx.saveAll(false);
  assert.equal(sent.length,0,'Tự lưu không được tự gửi lại lượt xoá/hoàn tác dòng');
  await ctx.saveAll(true);
  assert.equal(sent.length,1,'Bấm Lưu/Thử lại: đúng một lượt, không đệ quy saveAll ↔ travelDeleted');
  assert.equal(sent[0].operation,'cu','Gửi lại đúng mã lượt cũ (biên nhận chống lặp)');
  assert.ok(ctx.state.rowRetry,'Lỗi phiên giữ lượt để còn nút Thử lại');
  assert.deepEqual(notices,['het_phien']);
  // 1b. Cùng kịch bản với lượt hoàn tác có tạo dòng (travelCreated): không đệ quy, giữ lượt khi lỗi phiên
  sent.length=0;notices.length=0;
  const s2=[{id:7,column:'ghi_chu',old:'a',value:'b'}];s2.createdRows=[];
  ctx.state.rowRetry={payload:{operation:'cu2',kind:'undo',cells:[],row_changes:[]},step:s2,redo:false};
  await ctx.saveAll(false);assert.equal(sent.length,0,'Tự lưu không tự gửi lại lượt hoàn tác');
  await ctx.saveAll(true);
  assert.equal(sent.length,1,'Thử lại hoàn tác: đúng một lượt, không đệ quy saveAll ↔ travelCreated');
  assert.equal(sent[0].operation,'cu2');assert.ok(ctx.state.rowRetry,'Lỗi phiên giữ lượt hoàn tác để còn nút Thử lại');
  assert.deepEqual(notices,['het_phien']);
  // 2. Lượt hỏi: đang mất phiên thì không hỏi máy chủ; gặp lỗi phiên thì không gỡ nháp
  const pollCode=cut('  function reloadForViewMode(','  setInterval(poll,8000)');
  let fetched=0,cleared=0,shown=[];const seen=[];
  const p={working:{pending:()=>[],count:0},Set,Map,JSON,document:{hidden:false},config:{filterUrl:'f/',scopeUrl:'s'},csrf:'t',
    json:async r=>r,fetch:async()=>{fetched++;throw Object.assign(Error('Phiên đăng nhập đã hết'),{status:401,code:'het_phien',session:true});},
    clearTimeout(){},refreshStatus(){},saveAll(){},invalidate(){},cancelEdit(){},message:t=>shown.push(t),refresh(){},
    element:(t,c,x)=>({textContent:x}),$:()=>({append:e=>seen.push(e),close(){},replaceChildren(){}}),reader:{hidden:true,querySelector:()=>({textContent:''})},
    state:{cache:new Map(),retry:null,conflicts:[],busy:false,sessionLost:true},clearAccess(){cleared++;},sessionNotice:e=>{p.state.sessionLost=true;}};
  vm.createContext(p);vm.runInContext(`let saveTimer=0,firstQueued=0;${pollCode};globalThis.run=poll`,p);
  await p.run();assert.equal(fetched,0,'Mất phiên thì lượt hỏi dừng, không gửi gì');
  p.state.sessionLost=false;await p.run();
  assert.equal(fetched,1);assert.equal(cleared,0,'Lỗi phiên không đi clearAccess');
  assert.ok(shown.some(t=>String(t).includes('Phiên đăng nhập đã hết')));assert.equal(p.state.sessionLost,true);
  assert.equal(seen[0]?.textContent,'Tiếp tục','Không có nháp: nút Tiếp tục');
  // 3. Có lỗi lưu đang chờ: lượt hỏi không gọi message() (không xoá nút Thử lại xoá dòng/Đối chiếu xung đột)
  shown=[];p.state.sessionLost=false;p.state.saveError=true;await p.run();assert.equal(shown.length,0);
  // 4. Lưu gặp lỗi phiên: giữ đúng lượt và mã lượt (không nhả), không hẹn tự thử lại; 5xx lúc mất phiên cũng không
  const saveCode=cut('  async function saveAll(','  async function retainReadableDrafts(');
  const ops=[];let released=0,timers=0,uuid=0;
  const s={state:{busy:false,rowRetry:null,retry:null,conflicts:[],saveError:false,sessionLost:false,retryCount:0,columns:[]},
    working:{count:1,pending:()=>[{id:1,column:'ghi_chu',old:'a',value:'b'}],hold(){},release(){released++;}},
    fetch:async(u,o)=>{ops.push(JSON.parse(o.body).operation);throw Object.assign(Error('Phiên đăng nhập đã hết'),{status:401,code:'het_phien',session:true});},
    json:x=>x,status(){},message(){},closeMore(){},repaintSelection(){},refreshStatus(){},repaint(){},scheduleSave(){},finishEditor:()=>true,
    element:()=>({}),$:()=>({append(){}}),crypto:{randomUUID:()=>'op'+(++uuid)},config:{saveUrl:'/s'},csrf:'t',
    clearTimeout(){},setTimeout(){timers++;},sessionNotice(){s.state.sessionLost=true;},window:{confirm:()=>false}};
  vm.createContext(s);vm.runInContext(`let saveTimer=0,firstQueued=0;${saveCode};globalThis.saveAll=saveAll;`,s);
  await s.saveAll(true);await s.saveAll(true);
  assert.deepEqual(ops,['op1','op1'],'Thử lại sau lỗi phiên dùng lại đúng mã lượt cũ (biên nhận chống ghi đôi)');
  assert.equal(released,0,'Lỗi phiên không nhả lượt chưa rõ kết quả');
  assert.equal(timers,0,'Lỗi phiên không hẹn tự thử lại');
  s.fetch=async()=>{throw Object.assign(Error('Máy chủ lỗi'),{status:502});};
  await s.saveAll(true);assert.equal(timers,0,'Đang mất phiên: lỗi 5xx cũng không hẹn tự thử lại');
  s.state.sessionLost=false;await s.saveAll(true);assert.equal(timers,1,'Phiên còn: lỗi 5xx vẫn tự thử lại như cũ');
  // Đã biết mất phiên mà lượt cũ còn: lối tự động (saveAll(false)) không gửi; bấm Thử lại (explicit) gửi đúng lượt cũ
  s.fetch=async(u,o)=>{ops.push(JSON.parse(o.body).operation);throw Object.assign(Error('Máy chủ lỗi'),{status:502});};
  const truoc=ops.length;s.state.sessionLost=true;s.state.saveError=false;
  await s.saveAll(false);assert.equal(ops.length,truoc,'Mất phiên: lối tự động không gửi lại lượt cũ');
  // 4b. Lưu bị 403 rồi lượt kiểm quyền dòng gặp hết phiên: không clearAccess (không gỡ nháp), báo lỗi phiên
  const save2=cut('  async function saveAll(','  function soViet(');
  let xoa=0;const bao2=[];
  const t={state:{busy:false,rowRetry:null,retry:null,conflicts:[],saveError:false,sessionLost:false,retryCount:0,columns:[],cache:new Map()},
    working:{count:1,pending:()=>[{id:1,column:'ghi_chu',old:'a',value:'b'}],hold(){},release(){},forget(){}},
    fetch:async u=>{if(u==='/s')throw Object.assign(Error('Bạn không còn quyền sửa các dòng này.'),{status:403});
      throw Object.assign(Error('Phiên đăng nhập đã hết'),{status:401,code:'het_phien',session:true});},
    json:x=>x,status(){},message:x=>bao2.push(x),closeMore(){},repaintSelection(){},refreshStatus(){},repaint(){},scheduleSave(){},finishEditor:()=>true,
    element:()=>({}),$:()=>({append(){},close(){},replaceChildren(){}}),crypto:{randomUUID:()=>'op9'},config:{saveUrl:'/s',scopeUrl:'/q'},csrf:'t',
    clearTimeout(){},setTimeout(){},sessionNotice(){t.state.sessionLost=true;},clearAccess(){xoa++;},window:{confirm:()=>false}};
  vm.createContext(t);vm.runInContext(`let saveTimer=0,firstQueued=0;${save2};globalThis.saveAll=saveAll;`,t);
  await t.saveAll(true);
  assert.equal(xoa,0,'Kiểm quyền dòng gặp hết phiên: không gỡ nháp');assert.equal(t.state.sessionLost,true);
  assert.ok(bao2.some(x=>String(x).includes('Phiên đăng nhập đã hết')),'Báo hết phiên, không báo mất quyền');
  // 4c. Bỏ chi tiết gặp lỗi phiên: báo và gọi sessionNotice (có nút Tiếp tục), không đóng gì
  let bao3=0;const u={state:{},fetch:async()=>{throw Object.assign(Error('Phiên đăng nhập đã hết'),{status:401,code:'het_phien',session:true});},
    json:x=>x,config:{clearDetailsUrl:'/b'},csrf:'t',crypto:{randomUUID:()=>'x'},status(){},refreshStatus(){},invalidate(){},message(){},sessionNotice(){bao3++;}};
  vm.createContext(u);vm.runInContext(cut('  async function clearDetails(','  const safe=fn=>')+';globalThis.cd=clearDetails;',u);
  assert.equal(await u.cd([{id:1,column:'san_pham',old:'x'}]),false);assert.equal(bao3,1,'Bỏ chi tiết gặp hết phiên: gọi sessionNotice');
  // 5. Phản hồi JSON hợp lệ (đăng nhập lại đúng người) gỡ chặn tải khối của holdForSession
  const j={state:{sessionHold:'Phiên…',lastError:'Phiên…',sessionLost:true},URL};
  vm.createContext(j);vm.runInContext(cut('  async function json(response) {','  function fetch(url,options={}) {')+';globalThis.json=json;',j);
  await j.json({redirected:false,ok:true,headers:{get:()=>'application/json'},json:async()=>({ok:1})});
  assert.equal(j.state.lastError,'','Thử lại xoá dòng/bỏ chi tiết thành công: lưới tải lại, không trống mãi');
  assert.equal(j.state.sessionLost,false);assert.equal(j.state.sessionHold,'');
  // 6. Lượt dòng chưa xác nhận: thanh trạng thái không báo Đã lưu, nút Lưu thử lại được
  let st='';const nut={};
  const r={state:{draft:null,conflicts:[],busy:false,saveError:false,rowRetry:{step:[]},retry:null},working:{count:0},editor:{elements:{}},
    same:(a,b)=>a===b,status:t=>{st=t;},$:id=>id==='mg-save'?nut:{}};
  vm.createContext(r);vm.runInContext(cut('  function refreshStatus() {','  function finishEditor(')+';globalThis.rs=refreshStatus;',r);r.rs();
  assert.equal(st,'Lỗi lưu','Lượt xoá dòng còn treo không được báo Đã lưu');assert.equal(nut.disabled,false,'Nút Lưu thử lại được lượt dòng');
  // 7. Lỗi loadBlock đã báo (kèm nút, liên kết) thì safe() không đè
  const dong=src.indexOf('  const safe=fn=>');let msgs=0;const sf={message(){msgs++;}};
  vm.createContext(sf);vm.runInContext(src.slice(dong,src.indexOf('\n',dong))+';globalThis.safe=safe;',sf);
  await sf.safe(()=>{throw Object.assign(Error('đã báo'),{handled:true});})();await sf.safe(()=>{throw Error('chưa báo');})();
  assert.equal(msgs,1,'safe() chỉ báo lỗi chưa được báo');
  // 8. holdForSession giữ cả khối có nháp đang nằm trong stale (tải lại mềm)
  const h={working:{pending:()=>[{id:7}]},state:{retry:null,draft:null,pending:new Map(),cache:new Map(),
    stale:new Map([[0,{rows:[{id:7}]}],[1,{rows:[{id:200}]}]])},reader:{hidden:false,querySelector:()=>({textContent:''})},
    cellHistory:{hidden:false},$:()=>({close(){},replaceChildren(){}}),repaint(){}};
  vm.createContext(h);vm.runInContext(cut('  function holdForSession(text){','  function sessionNotice(error){')+';globalThis.hold=holdForSession;',h);
  h.hold('Phiên…');
  assert.deepEqual([...h.state.stale.keys()],[0],'Khối có nháp trong stale vẫn hiện, khối không nháp bỏ');
  assert.equal(h.state.cache.size,0,'Không đưa khối của thứ tự cũ sang bộ đệm (sau đăng nhập lại phải tải khối mới)');
  assert.equal(h.state.sessionHold,'Phiên…');
  h.state.stale=new Map([[1,{rows:[{id:200}]}]]);h.hold('Phiên…');assert.equal(h.state.stale,null,'Không còn khối có nháp thì bỏ stale');
  // 9. sessionNotice: huỷ hẹn tự thử lại; chưa có nút nào (ẩn cột, bỏ chi tiết) thì có Tiếp tục; lời cũ thiếu câu hết phiên thì thêm
  const them=[];let huy=0;const hop={hidden:true,textContent:'Không đổi được cột.',querySelector:()=>null,append:(...x)=>them.push(...x)};
  const sn={state:{saveError:false,rowRetry:null,conflicts:[]},holdForSession(){},clearTimeout(){huy++;},element:(t,c,x)=>({textContent:x}),$:()=>hop,refresh(){},message(){}};
  vm.createContext(sn);vm.runInContext(`let saveTimer=5,firstQueued=1;${cut('  function sessionNotice(error){','  function clearAccess(text){')};globalThis.sn=sessionNotice;`,sn);
  sn.sn(Object.assign(Error('Phiên đăng nhập đã hết — thay đổi chưa được lưu.'),{code:'het_phien',session:true}));
  assert.equal(sn.state.sessionLost,true);assert.equal(huy,1,'Huỷ hẹn tự thử lại đang chờ');
  assert.ok(them.some(x=>x&&x.textContent==='Tiếp tục'),'Có nút Tiếp tục');
  assert.ok(them.some(x=>String(x).includes('Phiên đăng nhập đã hết')),'Thêm câu hết phiên vào lời cũ');
  console.log('PASS: không tự gửi lại lượt dòng, không đệ quy, lượt hỏi dừng khi mất phiên và không gỡ nháp');
  console.log('PASS: lỗi phiên giữ mã lượt, không hẹn tự thử lại, phiên sống lại thì lưới tải tiếp, lượt dòng treo không báo Đã lưu, giữ khối nháp trong stale, có nút Tiếp tục');
})().catch(e=>{console.error(e);process.exitCode=1;});
