/* Đọc artifact kiểm thử; không kết nối hoặc ghi database. */
const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'../.agents/design-state/review/master-nine-capacity');
const percentile=(a,p)=>{const v=[...a].sort((x,y)=>x-y);return v[Math.max(0,Math.ceil(v.length*p)-1)];};
const stats=a=>({n:a.length,p50:percentile(a,.5),p95:percentile(a,.95),p99:percentile(a,.99)});
const resources=['resources.jsonl','resources-final.jsonl'].flatMap(file=>fs.existsSync(path.join(root,file))?fs.readFileSync(path.join(root,file),'utf8').split(/\r?\n/).filter(s=>s.trim()).flatMap(s=>{try{return [JSON.parse(s.trim())];}catch{return [];}}):[]);
function resourceWindow(directory,name,data){
  const file=path.join(directory,name.replace('.json','.log'));if(!fs.existsSync(file))return {};
  const start=fs.readFileSync(file,'utf8').match(/\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d+)\].*Starting Locust/);if(!start)return {};
  const at=Date.parse(start[1].replace(' ','T').replace(',','.')+'+07:00');
  const found=resources.filter(r=>Date.parse(r.at)>=at+data.warmup*1000&&Date.parse(r.at)<=at+data.elapsed*1000),groups={};
  for(const r of found)for(const c of r.containers){
    const mem=c.MemUsage.split('/')[0].trim().match(/([\d.]+)\s*(\w+)/),bytes=mem?Number(mem[1])*({B:1,KiB:1024,MiB:1024**2,GiB:1024**3}[mem[2]]||1):0;
    (groups[c.Name]??=[]).push({cpu:parseFloat(c.CPUPerc),bytes});
  }
  return Object.fromEntries(Object.entries(groups).map(([k,v])=>[k,{samples:v.length,cpuPercent:stats(v.map(x=>x.cpu)),maxMemoryBytes:Math.max(...v.map(x=>x.bytes))}]));
}
const result={method:'Nearest rank; milliseconds; HTTP excludes 60s warmup. Expected CAS conflicts are counted separately, not duplicated as requests.',http:[],browser:[],storage:null};
const finalDir=path.join(root,'final');
const runState=path.join(finalDir,'run-state.json');if(fs.existsSync(runState))result.runState=JSON.parse(fs.readFileSync(runState));
const files=fs.readdirSync(root).filter(name=>!fs.existsSync(finalDir)||(!name.startsWith('after-')&&!name.startsWith('endurance'))).map(name=>({name,directory:root}));
if(fs.existsSync(finalDir))files.push(...fs.readdirSync(finalDir).map(name=>({name,directory:finalDir})));
for(const {name,directory} of files){
  if(/^(before|after)-\d+-\d+\.json$/.test(name)||name==='endurance.json'){
    const data=JSON.parse(fs.readFileSync(path.join(directory,name))),samples=data.samples.filter(s=>s.name!=='expected:conflict'),groups={};
    for(const s of samples)(groups[s.name]??=[]).push(s);
    result.http.push({name:name.replace('.json',''),seconds:data.elapsed-data.warmup,requests:samples.length,
      rps:samples.length/(data.elapsed-data.warmup),errors:samples.filter(s=>s.error).length,
      conflicts:data.samples.filter(s=>s.name==='expected:conflict').length,integrityErrors:data.integrity_errors||[],
      resources:resourceWindow(directory,name,data),
      endpoints:Object.fromEntries(Object.entries(groups).map(([key,v])=>[key,{...stats(v.map(s=>s.ms)),errors:v.filter(s=>s.error).length}]))});
  }
  if(/^(before|after)-\d+-browser\.json$/.test(name)||name==='endurance-browser.json')result.browser.push({name,...JSON.parse(fs.readFileSync(path.join(directory,name)))});
}
if(fs.existsSync(path.join(root,'storage.json'))){const d=JSON.parse(fs.readFileSync(path.join(root,'storage.json')));result.storage={...d,samples:Object.fromEntries(Object.entries(d.samples).map(([k,v])=>[k,stats(v)]))};}
fs.writeFileSync(path.join(root,'summary.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify({http:result.http,storage:result.storage},null,2));
