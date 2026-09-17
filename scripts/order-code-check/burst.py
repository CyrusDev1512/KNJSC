import os,time,json,uuid,re,math
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import requests
root=Path('/runtime');m=json.loads((root/'ready.json').read_text());assert m['database']=='test_knjsc_code_load'
base='http://knjsc-code-app:8000';actors=[u for u in m['users'] if u['role']=='sale'];assert len(actors)==30
barrier=Barrier(30)
def work(actor):
 token=uuid.uuid4().hex;s=requests.Session();s.cookies.set('sessionid',actor['session']);s.cookies.set('csrftoken','a'*32);s.headers.update({'X-CSRFToken':'a'*32,'Referer':base+'/'})
 data={'customer_name':'Khach TEST BURST','phone':'BURST-'+token,'market':m['market'],'currency':'USD','payment_method':m['payment'],'product':m['products'][:2],'quantity':['2','1'],'unit_price':['10.10','20.20'],'unit':['hộp','túi'],'note':'LOADTEST-'+token}
 barrier.wait(timeout=10);start=time.perf_counter();r=s.post(base+'/van-don/len-don/',data=data,timeout=30)
 codes=re.findall(r'/van-don/don-goc/([^/]+)/',r.text)
 return {'actor':actor['id'],'token':token,'status':r.status_code,'code':codes[0] if codes else None,'ms':(time.perf_counter()-start)*1000,'timing':dict((k,float(v)) for k,v in re.findall(r'(app|db|lock);dur=([0-9.]+)',r.headers.get('Server-Timing','')))}
started=time.time()
with ThreadPoolExecutor(max_workers=30) as pool:rows=list(pool.map(work,actors))
orders=[{k:r[k] for k in ['code','actor','token']} for r in rows if r['status']==200 and r['code']]
def p(v,q):return sorted(v)[math.ceil(len(v)*q)-1]
out={'started':started,'finished':time.time(),'results':rows,'orders':orders,'attempts':[{'actor':r['actor'],'token':r['token']} for r in rows],'writes':{},'unique_codes':len({o['code'] for o in orders}),'p50_ms':p([r['ms'] for r in rows],.5),'p95_ms':p([r['ms'] for r in rows],.95),'p99_ms':p([r['ms'] for r in rows],.99),'lock_p95_ms':p([r['timing'].get('lock',0) for r in rows],.95)}
(root/'results/burst.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['results','orders','attempts','writes']},indent=2))
assert len(orders)==out['unique_codes']==30, 'Burst incomplete'
