/* Local-only fixture server: no Django/database/customer writes. */
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const root=path.resolve(__dirname,'..'),folder=path.join(root,'storage/grid-interaction');
const fixture=JSON.parse(fs.readFileSync(path.join(root,'storage/grid-scroll/fixture.json')));
const original=fs.readFileSync(path.join(root,'storage/grid-scroll/fixture.html'),'utf8');
const rows=new Map();let held=[],fail=false;
function row(id){if(!rows.has(id)){const r=structuredClone(fixture.rows[0]);r.id=id;r.cells.ten_khach={...r.cells.ten_khach,value:`Test ${id}`,display:`Test ${id}`};rows.set(id,r);}return rows.get(id);}
function json(res,data,status=200){res.writeHead(status,{'Content-Type':'application/json'});res.end(JSON.stringify(data));}
const server=http.createServer(async(req,res)=>{
 const u=new URL(req.url,'http://127.0.0.1');
 if(u.pathname==='/release'){const pending=held.splice(0);for(const [r,p] of pending){if(fail){json(r,{error:'Lỗi lưu mô phỏng'},503);continue;}const out=new Map();for(const c of p.cells){const obj=row(c.id);obj.cells[c.column]={...obj.cells[c.column],value:c.value,display:String(c.value??'')};out.set(obj.id,structuredClone(obj));}json(r,{rows:[...out.values()]});}return json(res,{released:pending.length});}
 if(u.pathname==='/fail'){fail=true;return json(res,{ok:true});}
 if(u.pathname==='/reset'){rows.clear();fail=false;return json(res,{ok:true});}
 if(u.pathname==='/result'&&req.method==='POST'){let body='';for await(const c of req)body+=c;const data=JSON.parse(body);fs.writeFileSync(path.join(folder,data.stage+'.json'),JSON.stringify(data,null,2));return json(res,{ok:true});}
 if(u.pathname.endsWith('/du-lieu/')){const offset=Number(u.searchParams.get('offset')||0);return json(res,{...fixture,total:10000,rows:Array.from({length:100},(_,i)=>row(offset+i+1))});}
 if(u.pathname.endsWith('/moi-nhat/'))return json(res,{});
 if(u.pathname.endsWith('/luu-json/')&&req.method==='POST'){let s='';for await(const c of req)s+=c;held.push([res,JSON.parse(s)]);return;}
 if(u.pathname.endsWith('/quyen-dong/')&&req.method==='POST'){let s='';for await(const c of req)s+=c;return json(res,{visible:JSON.parse(s).ids});}
 if(u.pathname==='/probe.js'){res.setHeader('Content-Type','text/javascript');return res.end(fs.readFileSync(path.join(root,'scripts/grid-interaction-probe.js')));}
 if(u.pathname.startsWith('/static/')){const p=path.resolve(root,'app',u.pathname.slice(1));if(!p.startsWith(path.join(root,'app/static')+path.sep)||!fs.existsSync(p)){res.writeHead(404);return res.end();}res.setHeader('Content-Type',p.endsWith('.js')?'text/javascript':p.endsWith('.css')?'text/css':'image/svg+xml');let body=fs.readFileSync(p);if(p.endsWith('master-grid.js')&&u.searchParams.get('stage')==='before')body=fs.readFileSync(path.join(folder,'baseline.js'));return res.end(body);}
 const stage=u.searchParams.get('stage')==='before'?'before':'after';
 const html=original.replace(/(src="[^"]*master-grid.js)[^"]*"/,`$1?stage=${stage}"`).replace('</body>',`<aside style="position:fixed;right:8px;bottom:40px;z-index:99999;background:white;border:1px solid #333;padding:6px;max-width:550px"><b>TEST ONLY · ${stage} · 10k rows</b><button id="probe-run">Đo chọn và nhập khi đang lưu</button><button id="probe-release">Trả kết quả lưu</button><button id="probe-fail">Mô phỏng lỗi lưu</button><textarea id="probe-output" rows="3" style="width:100%" aria-label="Kết quả đo"></textarea></aside><script src="/probe.js"></script></body>`);
 res.setHeader('Content-Type','text/html');res.end(html);
});
server.listen(18621,'127.0.0.1',()=>console.log('Fixture only http://127.0.0.1:18621/?stage=before'));
