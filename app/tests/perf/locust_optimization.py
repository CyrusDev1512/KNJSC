"""Locust tách container. ID/thứ tự/tổng phải khớp oracle; lỗi đúng không đếm hai lần."""
import itertools
import json
import os
import random
import time
import uuid
from pathlib import Path
from locust import HttpUser, task, between, events

manifest=json.loads(Path(os.environ['OPT_MANIFEST']).read_text())
assert manifest['database'].startswith('test_knjsc_opt_')
slots=itertools.count();samples=[];integrity_errors=[]
started=time.monotonic();warmup=int(os.environ.get('OPT_WARMUP','60'))
protocol=int(os.environ.get('OPT_PROTOCOL','1'))
base='/bang-tinh/van_don_moi/'

@events.request.add_listener
def collect(name,response_time,response_length,exception,response=None,context=None,**kwargs):
    if time.monotonic()-started>=warmup:
        samples.append({'name':name,'ms':response_time,'bytes':response_length,
                        'status':getattr(response,'status_code',0),'request_id':getattr(response,'headers',{}).get('X-Request-ID') or (context or {}).get('request_id'),
                        'category':'expected:cas' if getattr(response,'status_code',0)==409 and name=='write:cell' else 'unexpected' if exception else 'ok',
                        'error':type(exception).__name__ if exception else None})

@events.quitting.add_listener
def finish(environment,**kwargs):
    Path(os.environ['OPT_RESULT']).write_text(json.dumps({'warmup':warmup,'elapsed':time.monotonic()-started,'samples':samples,'integrity_errors':integrity_errors}))
    if integrity_errors or any(s['category']=='unexpected' for s in samples):environment.process_exit_code=1

class Editor(HttpUser):
    wait_time=between(float(os.environ.get('OPT_WAIT_MIN','1')),float(os.environ.get('OPT_WAIT_MAX','3')))
    def invalid(self,response,reason):
        response.failure(reason);integrity_errors.append(reason);self.environment.runner.quit()
    def on_start(self):
        self.actor=manifest['actors'][next(slots)];self.poll_at=0;self.query_token=None;self.export_at=0
        self.client.cookies.set('sessionid',self.actor['session']);self.client.cookies.set('csrftoken',manifest['csrf'])
        self.client.headers.update({'X-CSRFToken':manifest['csrf']})
        original=self.client.request
        def correlated(method,url,*args,**kwargs):
            request_id=uuid.uuid4().hex
            kwargs['headers']={**kwargs.get('headers',{}),'X-Request-ID':request_id}
            kwargs['context']={**kwargs.get('context',{}),'request_id':request_id}
            return original(method,url,*args,**kwargs)
        self.client.request=correlated
    @task(5)
    def read(self):
        offset=random.choice(list(self.actor['pages']))
        params={'offset':offset,'protocol':protocol}
        if self.query_token:params['query_token']=self.query_token
        with self.client.get(base+'du-lieu/',params=params,name='read:block',catch_response=True) as r:
            if r.status_code==200:
                data=r.json();ids=[row['id'] for row in data['rows']]
                if ids!=self.actor['pages'][offset] or data['total']!=self.actor['total']:self.invalid(r,'ID/order/total mismatch');return
                self.query_token=data.get('query_token')
                self.revision=data.get('revision');self.ids=ids
        if time.monotonic()-self.poll_at>=8:
            if protocol==2 and self.query_token:
                self.client.post(base+'dong-bo/',json={'query_token':self.query_token,'revision':self.revision,'ids':self.ids,'visible':self.ids,'query':''},name='poll')
            else:self.client.get(base+'moi-nhat/',name='poll')
            self.poll_at=time.monotonic()
    @task(1)
    def filtered(self):
        with self.client.get(base+'du-lieu/',params={'protocol':protocol,'f_quoc_gia':'USA'},name='read:filter',catch_response=True) as r:
            if r.status_code==200:
                data=r.json()
                if data['total']!=self.actor['filtered']['total'] or [row['id'] for row in data['rows']]!=self.actor['filtered']['ids']:self.invalid(r,'Filtered ID/order/total mismatch')
    @task(2)
    def write(self):
        with self.client.get(base+'du-lieu/',params={'f_ma_don':self.actor['code'],'protocol':protocol},name='read:write-target',catch_response=True) as r:
            if r.status_code!=200:return
            rows=r.json()['rows']
            if len(rows)!=1 or rows[0]['id']!=self.actor['row']:self.invalid(r,'Wrong write target');return
            row=rows[0]
        value=uuid.uuid4().hex
        payload={'protocol':protocol,'operation':str(uuid.uuid4()),'cells':[{'id':row['id'],'column':'ghi_chu','old':row['cells']['ghi_chu']['value'],'value':value}]}
        with self.client.post(base+'luu-json/',json=payload,name='write:cell',catch_response=True) as r:
            if r.status_code==409:r.success()
            elif r.status_code==200:
                data=r.json();saved=data['cells'][0]['value'] if data.get('protocol')==2 else data['rows'][0]['cells']['ghi_chu']['value']
                if saved!=value:self.invalid(r,'Wrong acknowledged value')

    @task(1)
    def history(self):
        with self.client.get(base+'lich-su/',params={'record':self.actor['row']},name='read:history',catch_response=True) as r:
            if r.status_code==200 and len(r.json()['items'])>50:self.invalid(r,'Unbounded history')

    @task(1)
    def statistics(self):
        # Không tăng tải cho lượt chẩn đoán kết nối đã chạy với workload cũ.
        if os.environ.get('OPT_MIXED')=='1':
            self.client.get('/thong-ke/',params={'nguon':'van_don_moi'},name='read:statistics')

    @task(1)
    def export(self):
        if os.environ.get('OPT_MIXED')!='1' or self.actor['total']>50000 or time.monotonic()-self.export_at<60:return
        self.export_at=time.monotonic()
        self.client.get(base+'xuat/',name='export:queue')
