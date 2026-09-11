/* Diff riêng so với snapshot có thay đổi nền, không so với HEAD đơn thuần. */
const fs=require('fs'),path=require('path'),crypto=require('crypto'),cp=require('child_process');
const root=path.resolve(__dirname,'..'),base='C:/KNJSC/CRM-Optimization-baseline',out=path.join(root,'.agents/design-state/review/optimization');
const manifest=JSON.parse(fs.readFileSync(path.join(base,'snapshot-manifest.json'))),hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
for(const entry of manifest.files.filter(f=>!f.excludedFromBaseline)){
 if(hash(path.join(base,entry.path))!==entry.sha256)throw Error('Snapshot bị đổi: '+entry.path);
}
const files=cp.execFileSync('git',['ls-files','--cached','--others','--exclude-standard','-z'],{cwd:root,encoding:'utf8'}).split('\0').filter(Boolean);
const entries=new Map(manifest.files.map(f=>[f.path,f])),changed=[];let diff='';
const empty=path.join(out,'empty-for-diff');fs.writeFileSync(empty,'');
for(const name of [...new Set([...files,...entries.keys()])].sort()){
 if(entries.get(name)?.excludedFromBaseline)continue;
 const before=path.join(base,name),after=path.join(root,name),a=fs.existsSync(before),b=fs.existsSync(after);
 if((!a&&!b)||(a&&b&&hash(before)===hash(after)))continue;
 changed.push({path:name,before:a?hash(before):null,after:b?hash(after):null});
 try{diff+=cp.execFileSync('git',['diff','--no-index','--no-ext-diff','--',a?before:empty,b?after:empty],{encoding:'utf8',maxBuffer:30e6});}
 catch(e){if(e.status!==1)throw e;diff+=e.stdout;}
}
fs.writeFileSync(path.join(out,'optimization-only.diff'),diff);
fs.writeFileSync(path.join(out,'optimization-files.json'),JSON.stringify({baseline:manifest.head,checked:manifest.files.length,changed},null,2));
console.log(`Baseline nguyên vẹn; ${changed.length} file riêng tác vụ. Diff chỉ tại thư mục evidence bị gitignore.`);
