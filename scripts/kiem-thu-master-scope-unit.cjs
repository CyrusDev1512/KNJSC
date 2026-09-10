/* Chạy hàm polling thật: thu quyền không tự gửi một phần lượt đang chờ. */
const assert=require('node:assert/strict'),fs=require('fs'),vm=require('vm');
const Working=require('../app/static/js/master-working-copy.js');
const source=fs.readFileSync(require.resolve('../app/static/js/master-grid.js'),'utf8');
const code=source.slice(source.indexOf('  async function poll()'),source.indexOf('  setInterval(poll,8000)'));
const working=new Working();working.stage([{id:1,column:'note',old:null,value:'A'},{id:2,column:'note',old:null,value:'B'}]);working.hold(working.pending());
let cleared=false;const buttons=[];
const ctx={working,Set,Map,JSON,document:{hidden:false},config:{filterUrl:'filter/',scopeUrl:'scope'},csrf:'test',json:async r=>r,
  fetch:async url=>url==='scope'?{visible:[2]}:{stamp:1},
  clearTimeout(){cleared=true;},refreshStatus(){},saveAll(){},invalidate(){},cancelEdit(){},message(){},
  element:()=>({}),$:()=>({close(){},replaceChildren(){},append:e=>buttons.push(e)}),reader:{hidden:true,querySelector:()=>({textContent:''})},
  state:{cache:new Map(),retry:{payload:{cells:working.pending()}},conflicts:[],busy:false},clearAccess(){throw Error('Không được bỏ mọi nháp');}};
vm.createContext(ctx);vm.runInContext(`let saveTimer=123,firstQueued=99;${code};globalThis.run=poll`,ctx);
(async()=>{await ctx.run();assert.equal(working.pending().length,1);assert.equal(working.pending()[0].id,2);
  assert.equal(ctx.state.saveError,true,'Polling phải dừng lượt đã mất một phần quyền');assert(cleared);assert.equal(working.held.size,0);assert.equal(ctx.state.retry,null);assert.equal(buttons.length,1);
  console.log('PASS: polling thu quyền giữ nháp hợp lệ, nhả biên nhận cũ và chờ Thử lại');
})().catch(e=>{console.error(e);process.exitCode=1;});
