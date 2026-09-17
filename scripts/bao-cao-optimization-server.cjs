/* Ghép request ID để phân biệt thời gian server với HTTP wall time. */
const fs=require('fs'),path=require('path');
const dir=path.resolve(__dirname,'../.agents/design-state/review/optimization');
const label=process.argv[2]||'endurance-final';
if(!['endurance-final','bulk-disjoint-final'].includes(label))throw Error('Chỉ tổng hợp lượt kiểm đã khai báo');
const read=name=>JSON.parse(fs.readFileSync(path.join(dir,name),'utf8').replace(/^\uFEFF/,''));
const summary=items=>{const s=items.slice().sort((a,b)=>a-b);return {n:s.length,...Object.fromEntries([['p50',.5],['p95',.95],['p99',.99]].map(([k,q])=>[k,s.length?s[Math.min(s.length-1,Math.ceil(s.length*q)-1)]:null]))};};
const logs=new Map();
for(const line of fs.readFileSync(path.join(dir,label+'-server.log'),'utf8').split(/\r?\n/)){
 const start=line.indexOf('{"request_id":');if(start<0)continue;
 let row;try{row=JSON.parse(line.slice(start));}catch{continue;}
 if(row.request_id&&typeof row.ms==='number')logs.set(row.request_id,row);
}
const groups={};
for(const sample of read(label+'.json').samples){
 const server=logs.get(sample.request_id);if(!server)continue;
 (groups[sample.name]||=[]).push({sample,server});
}
const report=Object.fromEntries(Object.entries(groups).map(([name,rows])=>[name,{
 matched:rows.length,statuses:Object.fromEntries([...new Set(rows.map(x=>x.server.status))].map(s=>[s,rows.filter(x=>x.server.status===s).length])),
 serverMs:summary(rows.filter(x=>x.sample.category==='ok').map(x=>x.server.ms)),
 dbMs:summary(rows.filter(x=>x.sample.category==='ok').map(x=>x.server.db_ms)),
 connectMs:summary(rows.filter(x=>x.sample.category==='ok').map(x=>x.server.connect_ms)),
 queries:summary(rows.filter(x=>x.sample.category==='ok').map(x=>x.server.queries))
}]));
fs.writeFileSync(path.join(dir,label==='endurance-final'?'endurance-server-summary.json':'bulk-server-summary.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));
