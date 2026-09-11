/* Tổng hợp dữ liệu thô, không suy số đo từ mục tiêu. */
const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'../.agents/design-state/review/optimization');
const percentile=(values,q)=>{const sorted=values.slice().sort((a,b)=>a-b);return sorted.length?sorted[Math.min(sorted.length-1,Math.ceil(sorted.length*q)-1)]:null;};
const summary=values=>({n:values.length,p50:percentile(values,.5),p95:percentile(values,.95),p99:percentile(values,.99)});
const reports=[];
for(const file of fs.readdirSync(root).filter(f=>f.endsWith('.json'))){
 let data;try{data=JSON.parse(fs.readFileSync(path.join(root,file),'utf8').replace(/^\uFEFF/,''));}catch{continue;}
 if(!Array.isArray(data.samples))continue;
 const operations={};
 for(const name of [...new Set(data.samples.map(s=>s.name))]){
   const rows=data.samples.filter(s=>s.name===name),ok=rows.filter(s=>s.category==='ok');
   operations[name]={...summary(ok.map(s=>s.ms)),payloadBytes:summary(ok.map(s=>s.bytes)),unexpected:rows.filter(s=>s.category==='unexpected').length,expectedCAS:rows.filter(s=>s.category==='expected:cas').length};
 }
 const seconds=data.elapsed-data.warmup;
 reports.push({file,warmup:data.warmup,seconds,requests:data.samples.length,rps:data.samples.length/seconds,
   unexpected:data.samples.filter(s=>s.category==='unexpected').length,integrityErrors:data.integrity_errors,operations});
}
fs.writeFileSync(path.join(root,'http-summary.json'),JSON.stringify(reports,null,2));
const resources=[];
for(const file of fs.readdirSync(root).filter(f=>f.endsWith('-resources.jsonl'))){
 const groups={};
 for(const line of fs.readFileSync(path.join(root,file),'utf8').split(/\r?\n/).filter(Boolean)){
  let row;try{row=JSON.parse(line.replace(/^\uFEFF/,''));}catch{continue;}
  for(const c of row.containers||[]){
   const name=c.Name,match=(c.MemUsage||'').match(/^([\d.]+)([A-Za-z]+)/);
   const mib=match?Number(match[1])*({B:1/1048576,KiB:1/1024,MiB:1,GiB:1024}[match[2]]||0):0;
   (groups[name]||=[]).push({cpu:parseFloat(c.CPUPerc)||0,mib});
  }
 }
 resources.push({file,components:Object.fromEntries(Object.entries(groups).map(([k,v])=>[k,{samples:v.length,cpu:summary(v.map(x=>x.cpu)),maxCpu:Math.max(...v.map(x=>x.cpu)),memoryMiB:summary(v.map(x=>x.mib)),maxMemoryMiB:Math.max(...v.map(x=>x.mib))}]))});
}
fs.writeFileSync(path.join(root,'resources-summary.json'),JSON.stringify(resources,null,2));
for(const r of reports)console.log(r.file,`${r.requests} mẫu sau warmup`,`${r.unexpected} lỗi ngoài dự kiến`,Object.fromEntries(Object.entries(r.operations).map(([k,v])=>[k,Math.round(v.p95||0)])));
