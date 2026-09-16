/* Hồi quy hủy request viewport cũ nhưng giữ request đã được editor/copy dùng. */
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(require.resolve('../app/static/js/master-grid.js'),'utf8');
const state={ready:true,persistedTotal:100000,total:100000,generation:1,pending:new Map(),cache:new Map(),cursors:new Map()};
const calls=[],ctx={state,config:{dataUrl:'/rows'},BLOCK:100,CACHE:10,HEADER:54,AbortController,URLSearchParams,
 query:new URLSearchParams(),scrollDirection:1,prefetchPaused:true,jumpPending:true,prefetchFailed:new Set(),
 viewport:{scrollTop:1000*28,clientHeight:800},geometry:{at:pixel=>Math.floor(pixel/28)},
 fetch:(url,{signal})=>new Promise((resolve,reject)=>{calls.push({url,signal});signal.addEventListener('abort',()=>reject(Object.assign(new Error('abort'),{name:'AbortError'})));}),json:x=>x};
vm.createContext(ctx);vm.runInContext(source.slice(source.indexOf('  async function loadBlock('),source.indexOf('  function element('))+';this.load=loadBlock;this.view=loadViewport;',ctx);
(async()=>{
 const old=ctx.load(0,false,true);ctx.view(990,1040);
 assert(calls[0].signal.aborted,'Viewport cũ phải nhường vùng đích');assert.equal(calls.length,1,'Timer nhảy đang chờ không phát request');await old;
 const owned=ctx.load(10,false,true),direct=ctx.load(10);
 ctx.viewport.scrollTop=2000*28;ctx.view(1990,2040);
 assert(!calls[1].signal.aborted,'Request được editor/copy dùng chung phải giữ');
 ctx.jumpPending=false;ctx.view(1990,2040);
 assert.deepEqual(calls.slice(2).map(c=>new URL(c.url,'http://test').searchParams.get('offset')),['2000']);
 // Callback finally của request bị hủy không xóa request mới cùng khối.
 const previous=state.pending.get(20);previous.controller.abort();state.pending.delete(20);
 const replacement=ctx.load(20,false,true),replacementController=state.pending.get(20).controller;
 await Promise.resolve();await Promise.resolve();
 assert.equal(state.pending.get(20)?.controller,replacementController);
 for(const p of state.pending.values())p.controller.abort();await Promise.all([owned,direct,replacement]);
 console.log('PASS jump timer, viewport cancellation, direct consumer ownership, replacement request');
})().catch(error=>{console.error(error);process.exitCode=1;});
