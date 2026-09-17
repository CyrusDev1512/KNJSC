import json,math,sys
from pathlib import Path
from collections import defaultdict,Counter
root=Path(__file__).resolve().parent.parent/'results'
def pct(v,p):
 v=sorted(v);return round(v[max(0,min(len(v)-1,math.ceil(len(v)*p)-1))],2) if v else None
out={}
for phase in sys.argv[1:]:
 m=json.loads((root/(phase+'.json')).read_text());hi=m['finished'];diagnostic=bool(m['abort']) and hi<m['started']+m['warmup'];lo=m['started'] if diagnostic else m['started']+m['warmup']
 browser=json.loads((root/(phase+'-browser.json')).read_text());ops=defaultdict(list)
 for a in browser['actions']:
  if lo<=a['time']/1000<=hi:ops[a['kind']].append(a['ms'])
 diag=browser.get('diagnostics',{});origin=browser.get('documentStart',0)/1000
 long=[x['duration'] for x in diag.get('long',[]) if lo<=origin+x['start']/1000<=hi]
 renders=[x['duration'] for x in diag.get('render',[]) if lo<=origin+x['start']/1000<=hi]
 route=defaultdict(list);q=defaultdict(list);errors=[]
 for line in '\n'.join(f.read_text() for f in root.glob('server*.jsonl')).splitlines():
  try:r=json.loads(line)
  except ValueError:continue
  if not lo<=r['time']<=hi:continue
  key=r['method']+' '+str(r['route']);route[key].append(r)
  for name,t in r['queries']:q[(key,name)].append(t)
  if r.get('sql_errors'):errors.append(r)
 resources=defaultdict(list)
 for line in (root/(phase+'-resources.jsonl')).read_text().splitlines():
  r=json.loads(line)
  if lo<=r['time']<=hi:
   for c in r['containers']:resources[c['Name']].append(c)
 result={'diagnostic_only':diagnostic,'window_seconds':hi-lo,'http':m['operations'],'browser':{'actions':{n:{'n':len(v),'p50_ms':pct(v,.5),'p95_ms':pct(v,.95),'max_ms':max(v)} for n,v in ops.items()},'initial_ready_ms':browser.get('initialReadyMs'),'long_tasks':len(long),'long_task_max_ms':max(long,default=0),'render_p95_ms':pct(renders,.95),'render_max_ms':max(renders,default=0),'errors':browser['errors'],'heap_bytes':diag.get('heap'),'grid':diag.get('grid')},'routes':{n:{'n':len(v),'app_p95_ms':pct([r['app_ms'] for r in v],.95),'db_p95_ms':pct([r['db_ms'] for r in v],.95),'lock_p50_ms':pct([r.get('lock_ms',0) for r in v],.5),'lock_p95_ms':pct([r.get('lock_ms',0) for r in v],.95),'lock_p99_ms':pct([r.get('lock_ms',0) for r in v],.99),'db_share_total':round(sum(r['db_ms'] for r in v)/sum(r['app_ms'] for r in v),3),'query_p50':pct([len(r['queries']) for r in v],.5)} for n,v in route.items()},'top_sql_categories':[{'route':key[0],'category':key[1],'n':len(v),'total_ms':round(sum(v),2),'p95_ms':pct(v,.95)} for key,v in sorted(q.items(),key=lambda x:-sum(x[1]))[:12]],'resources':{n:{'samples':len(v),'cpu_p50':pct([float(c['CPUPerc'].strip('%')) for c in v],.5),'cpu_p95':pct([float(c['CPUPerc'].strip('%')) for c in v],.95),'cpu_max':max(float(c['CPUPerc'].strip('%')) for c in v),'memory_last':v[-1]['MemUsage'],'network_first':v[0]['NetIO'],'network_last':v[-1]['NetIO']} for n,v in resources.items()},'sql_errors':errors}
 out[phase]=result
(root/'analysis.json').write_text(json.dumps(out,indent=2))
for phase,r in out.items():
 print(phase,json.dumps({'browser':r['browser'],'resources':r['resources'],'top_sql':r['top_sql_categories'][:5]},ensure_ascii=True))
