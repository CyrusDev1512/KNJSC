import os,json,itertools,time,random,uuid
from pathlib import Path
from decimal import Decimal
from locust import HttpUser,task,between,events
manifest=json.loads(Path('/runtime/ready.json').read_text());assert manifest['database'].startswith('test_crm_update_load_')
stage=os.environ.get('LOAD_STAGE','before');warmup=int(os.environ.get('LOAD_WARMUP','60'));started=time.monotonic();samples=[];errors=[];slots=itertools.count();duration=int(os.environ.get('LOAD_SECONDS','300'))
expected={};extended=os.environ.get('LOAD_EXTENDED')=='1'
@events.request.add_listener
def collect(name,response_time,response_length,exception,response=None,**kw):
 if warmup<=time.monotonic()-started<=warmup+duration:samples.append({'t':time.monotonic()-started,'name':name,'sql':response.headers.get('Server-Timing') if response is not None else None,'request_id':response.headers.get('X-Request-ID') if response is not None else None,'ms':response_time,'bytes':response_length,'status':getattr(response,'status_code',0),'error':str(exception) if exception else None})
@events.quitting.add_listener
def finish(environment,**kw):
 elapsed=time.monotonic()-started
 Path(os.environ['LOAD_RESULT']).write_text(json.dumps({'stage':stage,'rows':manifest['rows'],'warmup':warmup,'elapsed':elapsed,'measured':min(duration,max(0,elapsed-warmup)),'samples':samples,'integrity_errors':errors,'expected':expected}))
 if errors or any(s['error'] for s in samples):environment.process_exit_code=1
class Editor(HttpUser):
 wait_time=between(.7,1.3)
 def on_start(self):
  index=next(slots);self.actor=manifest['actors'][(index%3)*20+index//3];self.base='/bang-tinh/'+self.actor['table']+'/'
  self.client.cookies.set('sessionid',self.actor['session']);self.client.cookies.set('csrftoken',manifest['csrf']);self.client.headers['X-CSRFToken']=manifest['csrf'];self.note=self.actor['note']
  if stage=='after':
   data=self.client.get(self.base+'du-lieu/',params={'f_ma_don__bang':self.actor['code']},name=self.label('setup')).json()
   row=next(r for r in data['rows'] if r['id']==self.actor['row'])
   self.note=row['cells']['ghi_chu']['value'];self.cost=row['cells']['cpqc']['value']
   expected[str(self.actor['row'])]={'table':self.actor['table'],'user':self.actor['user'],'data':{}}
 def label(self,action):return self.actor['group']+':'+action
 @task(5)
 def read(self):
  endpoint=self.base+('du-lieu/' if stage=='after' else '')
  with self.client.get(endpoint,name=self.label('read'),catch_response=True) as response:
   if response.status_code==200 and stage=='after':
    body=response.json();rows=body['rows']
    def wrong_owner(row):
     code=row['cells']['ma_don']['value']
     if code.startswith('NEW-'):return int(code.split('-')[1])!=self.actor['user']
     return int(code.split('-')[-1])%20!=int(self.actor['code'].split('-')[-1])%20
    if self.actor['group']!='van-don' and any(wrong_owner(r) for r in rows):
     response.failure('Scope mismatch');errors.append('scope');self.environment.runner.quit()
   if response.status_code!=200:response.failure('Unexpected read status');errors.append(self.label('read'));self.environment.runner.quit()
 @task(2)
 def filter(self):
  endpoint=self.base+('du-lieu/' if stage=='after' else '')
  self.client.get(endpoint,params={'f_ma_don__bang':self.actor['code']},name=self.label('filter'))
 @task(2)
 def write(self):
  value='TEST-'+uuid.uuid4().hex
  if stage=='before':response=self.client.post(self.base+'o/'+str(self.actor['row'])+'/ghi_chu/',data={'gia_tri':value},name=self.label('save'))
  else:response=self.client.post(self.base+'luu-json/',json={'operation':str(uuid.uuid4()),'cells':[{'id':self.actor['row'],'column':'ghi_chu','old':self.note,'value':value}]},name=self.label('save'))
  if response.status_code!=200:errors.append(self.label('write'));self.environment.runner.quit()
  else:
   self.note=value
   if stage=='after':expected[str(self.actor['row'])]['data']['ghi_chu']=value
 @task(1)
 def history(self):
  if stage=='after':self.client.get(self.base+'lich-su/',params={'record':self.actor['row']},name=self.label('history-new'))
 if extended and stage=='after':
  @task(1)
  def create_and_formula(self):
   operation=str(uuid.uuid4());code=f"NEW-{self.actor['user']}-{operation}"
   values={'ma_don':code,'ten_khach':'Khach synthetic','so_don':5,'cpqc':'100.00'}
   response=self.client.post(self.base+'luu-json/',json={'operation':operation,'kind':'paste','cells':[
    {'id':-1,'column':column,'old':None,'value':value} for column,value in values.items()]},name=self.label('create-new'))
   if response.status_code!=200:errors.append(self.label('create'));self.environment.runner.quit();return
   result=response.json();pk=result.get('id_map',{}).get('-1')
   if not pk or str(pk) in expected:errors.append('duplicate/new ID');self.environment.runner.quit();return
   values['so_don']=5
   if self.actor['group']!='van-don':values['cpo']='20.00'
   expected[str(pk)]={'table':self.actor['table'],'user':self.actor['user'],'created':True,'data':values}
   if self.actor['group']=='van-don':return
   cost=str(random.randrange(1,10000))+'.00'
   response=self.client.post(self.base+'luu-json/',json={'operation':str(uuid.uuid4()),'cells':[
    {'id':self.actor['row'],'column':'cpqc','old':self.cost,'value':cost}]},name=self.label('formula-save-new'))
   if response.status_code!=200:errors.append('formula save');self.environment.runner.quit();return
   row=next(r for r in response.json()['rows'] if r['id']==self.actor['row'])
   answer=str(Decimal(cost)/5)
   if Decimal(row['cells']['cpo']['value'])!=Decimal(answer):errors.append('formula result');self.environment.runner.quit();return
   self.cost=row['cells']['cpqc']['value'];expected[str(self.actor['row'])]['data'].update(cpqc=self.cost,cpo=answer)
