/* Evidence tổng hợp có thể theo Git: không sao chép session, body hoặc log dữ liệu. */
const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..'),raw=path.join(root,'.agents/design-state/review/optimization');
const read=f=>JSON.parse(fs.readFileSync(path.join(raw,f),'utf8').replace(/^\uFEFF/,''));
const summary=v=>{const s=v.slice().sort((a,b)=>a-b);return {n:s.length,...Object.fromEntries([['p50',.5],['p95',.95],['p99',.99]].map(([k,q])=>[k,s.length?s[Math.min(s.length-1,Math.ceil(s.length*q)-1)]:null]))};};
const official=/^(before|after)-(100000|300000)-(10|20)-p[12]\.json$|^(endurance-final|bulk-disjoint-final)\.json$/;
const http=read('http-summary.json').filter(x=>official.test(x.file));
if(http.length<8)throw Error('Thiếu ma trận trước/sau: cần đủ tám lượt, không sinh báo cáo rỗng.');
const resources=read('resources-summary.json').filter(x=>official.test(x.file.replace('-resources.jsonl','.json')));
const browser=[];
for(const stage of ['before','after'])for(const count of [100000,300000]){
 const file=(stage==='before'?'browser/':'browser-final/')+`${stage}-${count}.json`,d=read(file);
 browser.push({file,stage,count,sourceSHA256:d.sourceSHA256,ok:d.ok,errors:d.errors,
   samples:Object.fromEntries(Object.entries(d.samples).map(([k,v])=>[k,summary(v)])),
   responsive:d.responsive,scroll:d.scroll,memory:d.memory,requests:d.requests});
}
const measurements=['before300','after300'].map(stage=>{
 const d=read(`measure-${stage}.json`);
 return {stage,mode:d.mode,plans:Object.fromEntries(Object.entries(d.plans).map(([k,v])=>[k,v.map(plan=>({executionMs:plan[0]['Execution Time'],planningMs:plan[0]['Planning Time'],sharedHitBlocks:plan[0].Plan['Shared Hit Blocks'],sharedReadBlocks:plan[0].Plan['Shared Read Blocks']}))])),
 storage:d.storage.map(({request_ids,server_ms,response_bytes,...rest})=>({...rest,httpWallMs:summary(server_ms),responseBytes:summary(response_bytes)}))};
});
const telemetryFile=path.join(raw,'endurance-final.telemetry.jsonl');let telemetry;
if(fs.existsSync(telemetryFile)){
 const entries=fs.readFileSync(telemetryFile,'utf8').trim().split(/\r?\n/).map(x=>JSON.parse(x));
 telemetry={samples:entries.length,errors:entries.filter(x=>x.error).map(x=>({time:x.time,error:x.error})),
  maxPending:Math.max(...entries.map(x=>(x.jobs||[]).find(j=>j[0]==='pending')?.[1]||0)),
  maxPendingAgeSeconds:Math.max(...entries.map(x=>Number((x.jobs||[]).find(j=>j[0]==='pending')?.[2]||0))),
  lockWaitSamples:entries.filter(x=>(x.connections||[]).some(c=>c[1]==='Lock')).length,
  waits:Object.fromEntries([...new Set(entries.flatMap(x=>(x.connections||[]).filter(c=>c[0]==='active'&&c[1]).map(c=>c[1]+':'+c[2])))].map(wait=>[wait,entries.filter(x=>(x.connections||[]).some(c=>c[0]==='active'&&c[1]+':'+c[2]===wait)).length])),
  maxConnections:Math.max(...entries.map(x=>(x.connections||[]).reduce((sum,c)=>sum+c[3],0))),
  first:entries[0],last:entries.at(-1)};
}
const output={generated:new Date().toISOString(),scope:'Local; không chứng minh VPS. Payload HTTP là body giải nén. Tài nguyên PostgreSQL dùng chung. WAL toàn cluster.',
 http,resources,browser,measurements,telemetry,
 jobs:fs.existsSync(path.join(raw,'endurance-jobs.json'))?read('endurance-jobs.json'):null,
 server:fs.existsSync(path.join(raw,'endurance-server-summary.json'))?read('endurance-server-summary.json'):null,
 bulkServer:fs.existsSync(path.join(raw,'bulk-server-summary.json'))?read('bulk-server-summary.json'):null};
const dir=path.join(root,'docs/verification');fs.mkdirSync(dir,{recursive:true});
fs.writeFileSync(path.join(dir,'crm-optimization-20260911.json'),JSON.stringify(output,null,2));
const manifest=read('baseline-manifest.json');
fs.writeFileSync(path.join(dir,'crm-optimization-baseline.json'),JSON.stringify(manifest,null,2));
console.log(`Đã tổng hợp ${http.length} lượt HTTP và ${browser.length} lượt Chrome; không lấy dữ liệu phiên/ô.`);
