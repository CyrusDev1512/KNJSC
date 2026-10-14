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
  console.log('PASS: không tự gửi lại lượt dòng, không đệ quy, lượt hỏi dừng khi mất phiên và không gỡ nháp');
})().catch(e=>{console.error(e);process.exitCode=1;});
