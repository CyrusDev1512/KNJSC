/* Chạy chính các hàm controller với đồng hồ/network giả; không sao chép thuật toán. */
const assert=require('node:assert/strict'),fs=require('fs'),vm=require('vm'),crypto=require('crypto');
const Working=require('../app/static/js/master-working-copy.js');
const source=fs.readFileSync(require.resolve('../app/static/js/master-grid.js'),'utf8');
const code=source.slice(source.indexOf('  function scheduleSave()'),source.indexOf('  async function copy()'));
function fixture(){
  let now=10000,sequence=0;const timers=new Map(),requests=[];
  const ctx={Working,crypto,Map,Set,Date:{now:()=>now},
    setTimeout:(fn,delay)=>{const id=++sequence;timers.set(id,{fn,at:now+delay});return id;},clearTimeout:id=>timers.delete(id),
    fetch:(url,options)=>new Promise((resolve,reject)=>requests.push({url,payload:JSON.parse(options.body),resolve,reject})),
    json:async r=>r,$:()=>({append(){},close(){},replaceChildren(){}}),element:()=>({}),
    editor:{hidden:true},reader:{hidden:true,querySelector:()=>({textContent:''})},cancelEdit(){},
    status(){},message(){},closeMore(){},repaint(){},refreshStatus(){},finishEditor:()=>true,
    clearAccess(){},invalidate(){},showConflicts(){},config:{saveUrl:'test',scopeUrl:'scope'},csrf:'test',window:{KNJSCWorkingCopy:Working}};
  vm.createContext(ctx);vm.runInContext(`let working=new Working(),saveTimer=0,firstQueued=0;const state={busy:false,saveError:false,conflicts:[],cache:new Map(),pending:new Map(),generation:0,accessEpoch:0,retryCount:0};${code};globalThis.api={working,state,scheduleSave,saveAll};`,ctx);
  const settle=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
  const advance=async delta=>{const end=now+delta;while(true){const next=[...timers].filter(([,v])=>v.at<=end).sort((a,b)=>a[1].at-b[1].at)[0];if(!next)break;now=next[1].at;timers.delete(next[0]);next[1].fn();await settle();}now=end;await settle();};
  const stage=value=>{const old=ctx.api.working.value(1,'note',null);ctx.api.working.stage([{id:1,column:'note',old,value}]);ctx.api.scheduleSave();};
  const success=async index=>{const q=requests[index];q.resolve({rows:[{id:1,cells:{note:{value:q.payload.cells[0].value,style:{}}}}]});await settle();};
  return {...ctx.api,requests,advance,stage,success,settle,timers};
}
(async()=>{
  const a=fixture();a.stage('A');await a.advance(499);assert.equal(a.requests.length,0);await a.advance(1);assert.equal(a.requests.length,1);
  a.stage('B');await a.advance(2000);assert.equal(a.requests.length,1,'Chỉ một request đang chạy');await a.success(0);assert.equal(a.working.pending()[0].value,'B');await a.advance(500);assert.equal(a.requests.length,2);await a.success(1);assert.equal(a.working.count,0);
  const b=fixture();for(let i=0;i<5;i++){b.stage(String(i));await b.advance(400);}assert.equal(b.requests.length,1,'Nhập liên tục vẫn gửi chậm nhất 2 giây');await b.success(0);
  const c=fixture();c.stage('A');await c.advance(500);const payload=JSON.stringify(c.requests[0].payload);
  for(let i=0;i<4;i++){c.requests[i].reject(Error('Mất phản hồi'));await c.settle();await c.advance(1000*2**i-1);assert.equal(c.requests.length,i+1);await c.advance(1);assert.equal(c.requests.length,i+2);assert.equal(JSON.stringify(c.requests[i+1].payload),payload);}
  c.requests[4].reject(Error('Vẫn mất mạng'));await c.settle();await c.advance(20000);assert.equal(c.requests.length,5);assert.equal(c.state.saveError,true);assert.equal(c.working.count,1);
  for(const status of [400,409]){const d=fixture();d.stage('A');await d.advance(500);d.requests[0].reject(Object.assign(Error('Từ chối'),{status}));await d.settle();await d.advance(20000);assert.equal(d.requests.length,1);assert.equal(d.state.saveError,true);}
  const denied=fixture();denied.working.stage([{id:1,column:'note',old:null,value:'Mất quyền'},{id:2,column:'note',old:null,value:'Còn quyền'}]);denied.scheduleSave();await denied.advance(500);
  denied.working.stage([{id:2,column:'note',old:'Còn quyền',value:'Nháp mới còn quyền'}]);denied.scheduleSave();
  denied.requests[0].reject(Object.assign(Error('Quyền thay đổi'),{status:403}));await denied.settle();
  assert.equal(denied.requests[1]?.url,'scope','403 phải kiểm lại dòng còn quyền trước khi bỏ bản nháp');
  denied.requests[1].resolve({visible:[2]});await denied.settle();
  assert.equal(denied.working.pending().length,1);assert.equal(denied.working.pending()[0].id,2);assert.equal(denied.working.pending()[0].value,'Nháp mới còn quyền');
  await denied.advance(20000);assert.equal(denied.requests.length,2,'Không tự gửi lại một phần sau mất quyền');
  console.log('PASS: debounce 500ms/max 2s, một request, nháp mới, retry 1–2–4–8s cùng payload; 403 giữ nháp còn quyền và không tự gửi một phần; không tự retry 400/409');
})().catch(error=>{console.error(error);process.exitCode=1;});
