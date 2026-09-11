const assert=require('node:assert/strict'),fs=require('fs'),vm=require('vm');
const source=fs.readFileSync(require.resolve('../app/static/js/master-grid.js'),'utf8');
const ctx={Error,URL};vm.createContext(ctx);
vm.runInContext(source.slice(source.indexOf('  async function json('),source.indexOf('  function layout('))+';this.parse=json;',ctx);
(async()=>{
  await assert.rejects(ctx.parse({ok:true,redirected:true,url:'http://localhost/dang-nhap/?next=grid',headers:{get:()=> 'text/html'},json:async()=>({})}),e=>e.status===403,'Hết phiên/khóa tài khoản phải đi đường gỡ dữ liệu đã mất quyền');
  await assert.rejects(ctx.parse({ok:false,status:503,headers:{get:()=> 'text/html'},json:async()=>({})}),e=>e.status===503,'Lỗi mạng/server giữ nguyên nháp');
  assert.deepEqual(await ctx.parse({ok:true,redirected:false,headers:{get:()=> 'application/json'},json:async()=>({protocol:2})}),{protocol:2});
  console.log('PASS quyền mất phiên, phân biệt lỗi server và JSON hợp lệ');
  const state={generation:0,pending:new Map(),cache:new Map(),cursors:new Map(),version:'',queryToken:'q',revision:9};
  let observed=0;
  const grid={state,config:{protocol:2,dataUrl:'/data'},BLOCK:100,CACHE:10,AbortController,URLSearchParams,query:new URLSearchParams(),
    fetch:async()=>({protocol:2,revision:8,query_token:'q',version:'v',metadata_version:'m',total:0,columns:[],rows:[]}),json:async x=>x,
    updateGeometry:fn=>fn(),geometry:{total:0},working:{observe:()=>observed++},layout:()=>{},repaint:()=>{}};
  vm.createContext(grid);
  vm.runInContext(source.slice(source.indexOf('  async function loadBlock('),source.indexOf('  function element('))+';this.load=loadBlock;',grid);
  await grid.load(0);
  assert.equal(observed,0,'Phản hồi khối trước mốc polling không được ghi đè cache mới');
  assert.equal(state.cache.size,0);
  grid.fetch=async()=>({protocol:2,revision:9,query_token:'q',version:'v',metadata_version:'m',total:0,columns:[],rows:[]});
  await grid.load(0);assert.equal(state.cache.size,1);
  console.log('PASS phản hồi khối đến muộn sau polling');
  const polling={state:{busy:false,generation:0,queryToken:'q',revision:1,cache:new Map()},config:{syncUrl:'/sync'},document:{hidden:false},
    working:{pending:()=>[],observe:()=>{}},canvas:{querySelectorAll:()=>[]},query:new URLSearchParams(),csrf:'test',json:async x=>x,updateRows:()=>{}};
  polling.fetch=async()=>{polling.state.busy=true;return {revision:2,removed:[],reset:false,invalidate:[],rows:[]};};
  vm.createContext(polling);
  vm.runInContext(source.slice(source.indexOf('  async function poll('),source.indexOf('  setInterval(poll,'))+';this.run=poll;',polling);
  await polling.run();assert.equal(polling.state.revision,1,'Không vượt mốc sync khi lượt lưu mới đã bắt đầu');
  console.log('PASS polling đến muộn trong lúc lưu');
  assert(source.includes('  function fetch('),'Cần mã request từ phía client, không chỉ từ server');
  const calls=[],trace={Headers,crypto:require('crypto').webcrypto,performance,config:{requestMetrics:true},requestLog:[],window:{fetch:async(url,options)=>{calls.push(options);return {status:200,headers:{get:()=>null}};}}};
  vm.createContext(trace);vm.runInContext(source.slice(source.indexOf('  function fetch('),source.indexOf('  function layout('))+';this.run=fetch;',trace);
  for(let i=0;i<105;i++)await trace.run('/test',{headers:{'X-CSRFToken':'fixture'}});
  assert.equal(trace.requestLog.length,100);assert.equal(calls[0].headers.get('X-CSRFToken'),'fixture');
  assert.match(calls[0].headers.get('X-Request-ID'),/^[0-9a-f]{32}$/);
  assert.equal(new Set(calls.map(c=>c.headers.get('X-Request-ID'))).size,105);
  assert(trace.requestLog.every(e=>!('url' in e)&&!('body' in e)));
  console.log('PASS mã request client, bảo toàn CSRF và giới hạn metadata trong RAM');
})().catch(e=>{console.error(e);process.exitCode=1;});
