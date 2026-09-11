import os,json,time,re,random,uuid,math
from pathlib import Path
from urllib.parse import urlencode
from collections import defaultdict,deque
import gevent
from locust import HttpUser,task,between,events
from locust.exception import StopUser
M=json.loads(Path('/runtime/ready.json').read_text());assert M['database']=='test_knjsc_code_load'
PHASE=os.environ.get('PHASE','smoke');MIXED=os.environ.get('MIXED','0')=='1'
WARM=float(os.environ.get('WARMUP','15'));T0=0;ABORT='';BAD=0
PROTOCOL=int(os.environ.get('PROTOCOL','1'))
samples=defaultdict(list);timings=defaultdict(list);error_counts=defaultdict(int);statuses=defaultdict(lambda:defaultdict(int));expected409=0
orders=[];attempts=[];writes={};all_requests=[];users=defaultdict(deque)
for u in M['users']:users[u['role']].append(u)
def abort(reason,environment):
 global ABORT
 if not ABORT:
  ABORT=reason;Path('/runtime/results/'+PHASE+'-abort.txt').write_text(reason);gevent.spawn_later(.2,environment.runner.quit)
@events.test_start.add_listener
def start(environment,**kw):
 global T0
 T0=time.time()
@events.request.add_listener
def record(name,response_time,response=None,exception=None,**kw):
 global BAD
 all_requests.append({'time':time.time(),'name':name,'ms':response_time,'status':response.status_code if response is not None else 0,'failed':exception is not None})
 if response is not None and response.status_code>=500:BAD+=1
 if T0 and time.time()-T0>=WARM:
  samples[name].append(response_time);error_counts[name]+=int(exception is not None)
  if response is not None:
   statuses[name][str(response.status_code)]+=1
   d=dict((k,float(v)) for k,v in re.findall(r'(app|db|lock);dur=([0-9.]+)',response.headers.get('Server-Timing','')))
   if d:timings[name].append({**d,'queries':int(response.headers.get('X-Test-Query-Count',0))})
class Base(HttpUser):
 abstract=True
 def on_start(self):
  assert self.host=='http://knjsc-code-app:8000'
  self.actor=users[self.role].popleft();self.client.cookies.set('sessionid',self.actor['session']);self.client.cookies.set('csrftoken','a'*32)
  self.client.headers.update({'X-CSRFToken':'a'*32,'Referer':self.host+'/','Connection':'keep-alive'})
  self.client.get('/van-don/len-don/' if self.role=='sale' else '/bang-tinh/van_don_moi/',name=self.role+'/open')
  gevent.sleep(random.uniform(0,8))
 def fail(self,response,message):
  response.failure(message)
  if BAD>=3:abort('Three unexpected server errors',self.environment)
 def block(self,params,name):
  global expected409
  params={**params,'protocol':PROTOCOL}
  with self.client.get('/bang-tinh/van_don_moi/du-lieu/',params=params,name=name,catch_response=True,timeout=30) as r:
   if r.status_code==409:
    expected409+=1;r.success();return None
   if r.status_code!=200:self.fail(r,'Block HTTP '+str(r.status_code));return None
   try:d=r.json()
   except Exception:self.fail(r,'Block invalid JSON');return None
   if 'rows' not in d:self.fail(r,'Missing rows');return None
   if any(row['cells']['phu_trach_vd']['value']!=self.actor['username'] for row in d['rows']):
    self.fail(r,'Scope mismatch');abort('Scope mismatch',self.environment);return None
   d['_test_query']=urlencode({k:v for k,v in params.items() if k not in ['protocol','offset','version']})
   return d
class Delivery(Base):
 fixed_count=int(os.environ.get('DELIVERY_USERS','9'));role='delivery';wait_time=between(1,3)
 def on_start(self):
  super().on_start();self.version='';self.last_poll=0;self.last_stamp=None;self.ids=[];self.seq=0
 @task
 def work(self):
  self.seq+=1
  if time.monotonic()-self.last_poll>=8:
   self.last_poll=time.monotonic()
   with self.client.get('/bang-tinh/van_don_moi/moi-nhat/',name='grid/poll',catch_response=True,timeout=30) as r:
    if r.status_code==200:
     stamp=r.text
     if self.last_stamp and self.last_stamp!=stamp:self.version=''
     self.last_stamp=stamp
    else:self.fail(r,'Poll failed')
   if self.ids:self.client.post('/bang-tinh/van_don_moi/quyen-dong/',json={'ids':self.ids},name='grid/scope',timeout=30)
  choice=random.random();params={}
  if choice<.2:
   params={'f_trang_thai_vc__trong':M['status']};self.version='';name='grid/filter'
  elif choice<.3:
   params={'tim':'Khach TEST'};self.version='';name='grid/search'
  else:
   params={'offset':random.choice([0,100,500,2000,8000,9900])};name='grid/scroll'
   if self.version:params['version']=self.version
  d=self.block(params,name)
  if d is None:
   self.version='';params.pop('version',None);d=self.block(params,'grid/reload')
  if not d:return
  self.version=d.get('version','') if name=='grid/scroll' else '';self.ids=[r['id'] for r in d['rows']]
  if PROTOCOL==2 and d.get('query_token') and self.seq%3==0:
   self.client.post('/bang-tinh/van_don_moi/dong-bo/',json={'query_token':d['query_token'],'revision':d['revision'],'ids':self.ids,'visible':self.ids,'query':d['_test_query']},name='grid/sync-v2',timeout=30)
  if self.seq%3==0 and d['rows']:
   row=d['rows'][0];val=f'MIXED-TEST-{self.actor["index"]}-{uuid.uuid4().hex[:12]}'
   payload={'protocol':PROTOCOL,'operation':str(uuid.uuid4()),'cells':[{'id':row['id'],'column':'ghi_chu','old':row['cells']['ghi_chu']['value'],'value':val}]}
   with self.client.post('/bang-tinh/van_don_moi/luu-json/',json=payload,name='grid/save',catch_response=True,timeout=30) as r:
    if r.status_code!=200:self.fail(r,'Save HTTP '+str(r.status_code))
    else:
     saved=r.json();actual=saved['cells'][0]['value'] if saved.get('protocol')==2 else saved['rows'][0]['cells']['ghi_chu']['value']
     if actual!=val:self.fail(r,'Wrong acknowledgment');abort('Wrong acknowledgment',self.environment)
     else:writes[str(row['id'])]=val;self.version=''
class Sale(Base):
 abstract=not MIXED
 fixed_count=int(os.environ.get('SALE_USERS','30'));role='sale';wait_time=between(20,40)
 @task
 def order(self):
  phone='08'+uuid.uuid4().hex[:14];token=uuid.uuid4().hex
  self.client.get('/van-don/len-don/kiem-khach/',params={'phone':phone},name='sale/customer-check',timeout=30)
  data={'customer_name':'Khach KIEM TAI','phone':phone,'market':M['market'],'currency':'USD','payment_method':M['payment'],'product':M['products'][:2],'quantity':['2','1'],'unit_price':['10.10','20.20'],'unit':['h\u1ed9p','h\u1ed9p'],'note':'LOADTEST-'+token}
  self.client.post('/van-don/len-don/tom-tat/',data=data,name='sale/preview',timeout=30)
  attempts.append({'token':token,'actor':self.actor['id']})
  with self.client.post('/van-don/len-don/',data=data,name='sale/create',catch_response=True,timeout=30) as r:
   codes=re.findall(r'/van-don/don-goc/([^/]+)/',r.text)
   if r.status_code!=200 or not codes:
    self.fail(r,'Order rejected HTTP '+str(r.status_code));abort('Order rejected before acknowledgement',self.environment)
   else:orders.append({'code':codes[0],'actor':self.actor['id'],'token':token})
  if BAD>=3:abort('Three unexpected server errors',self.environment)
def pct(v,p):
 v=sorted(v);return round(v[max(0,min(len(v)-1,math.ceil(len(v)*p)-1))],2) if v else None
@events.quitting.add_listener
def finish(environment,**kw):
 duration=max(0,time.time()-T0-WARM);ops={}
 for n,v in samples.items():
  t=timings[n];ops[n]={'n':len(v),'p50_ms':pct(v,.5),'p95_ms':pct(v,.95),'p99_ms':pct(v,.99),'errors':error_counts[n],'statuses':dict(statuses[n]),'rps':round(len(v)/max(.001,duration),2),'app_p95_ms':pct([x['app'] for x in t],.95),'db_p95_ms':pct([x['db'] for x in t],.95),'queries_p50':pct([x['queries'] for x in t],.5)}
 Path('/runtime/results/'+PHASE+'.json').write_text(json.dumps({'phase':PHASE,'started':T0,'finished':time.time(),'warmup':WARM,'measured_seconds':duration,'abort':ABORT,'unexpected_server_errors':BAD,'expected_version_conflicts_total':expected409,'operations':ops,'orders':orders,'attempts':attempts,'writes':writes,'all_requests':all_requests},indent=2))
