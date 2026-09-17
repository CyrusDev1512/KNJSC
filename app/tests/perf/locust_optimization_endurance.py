"""Bài bền: cùng tải ngắn, thêm lượt 2.000 ô khi các vai trò vẫn làm việc."""
import time
import uuid
import json
import os
from pathlib import Path
import gevent
import psycopg
from locust import events
import locust_optimization as base

monitor=None


@events.test_start.add_listener
def start_monitor(**kwargs):
    global monitor
    def sample():
        output=Path(os.environ['OPT_RESULT']).with_suffix('.telemetry.jsonl')
        while True:
            data={'time':time.time()}
            try:
                with psycopg.connect(host=os.environ.get('POSTGRES_HOST','db'),dbname=base.manifest['database'],
                    user=os.environ['POSTGRES_USER'],password=os.environ['POSTGRES_PASSWORD'],autocommit=True,
                    application_name='crm-opt-monitor',options='-c statement_timeout=1000') as conn,conn.cursor() as c:
                    c.execute("SELECT state,wait_event_type,wait_event,count(*) FROM pg_stat_activity WHERE datname=current_database() AND application_name<>'crm-opt-monitor' GROUP BY 1,2,3")
                    data['connections']=c.fetchall()
                    c.execute("SELECT status,count(*),max(extract(epoch FROM clock_timestamp()-created_at)) FILTER(WHERE status='pending') FROM core_backgroundjob GROUP BY status")
                    data['jobs']=c.fetchall()
            except Exception as error:data['error']=type(error).__name__
            with output.open('a') as file:file.write(json.dumps(data,default=str)+'\n')
            gevent.sleep(10)
    monitor=gevent.spawn(sample)


@events.test_stop.add_listener
def stop_monitor(**kwargs):
    if monitor is not None:monitor.kill()

events.request.remove_listener(base.collect)


@events.request.add_listener
def collect(**kwargs):
    before=len(base.samples)
    base.collect(**kwargs)
    if (len(base.samples)>before and kwargs.get('name') in ('write:bulk2000','write:style2000')
        and getattr(kwargs.get('response'),'status_code',None)==409):
        base.samples[-1]['category']='expected:cas'


class EnduranceEditor(base.Editor):
    def on_start(self):
        super().on_start();self.bulk_at=time.monotonic();self.bulk_count=0

    def bulk_or_write(self):
        if self.actor['user']!=base.manifest['actors'][0]['user'] or time.monotonic()-self.bulk_at<float(os.environ.get('OPT_BULK_INTERVAL','120')):
            return super().write()
        self.bulk_at=time.monotonic();self.bulk_count+=1
        rows=[]
        start=int(base.manifest.get('bulk_offset',0))
        for offset in range(0,2000,100):
            with self.client.get(base.base+'du-lieu/',params={'protocol':2,'offset':start+offset},name='read:bulk-target',catch_response=True) as response:
                if response.status_code!=200:return
                part=response.json()['rows']
                expected=self.actor['bulk_ids'][offset:offset+100]
                if [r['id'] for r in part]!=expected:self.invalid(response,'Bulk target ID/order mismatch');return
                rows.extend(part)
        style=self.bulk_count%2==0 and not base.manifest.get('bulk_values_only');value=uuid.uuid4().hex
        cells=[{'id':r['id'],'column':'ghi_chu','old':r['cells']['ghi_chu']['value'],'value':value} for r in rows]
        if style:
            cells=[{'id':r['id'],'column':'ghi_chu','property':'fs','old':r['cells']['ghi_chu']['style'].get('fs'),
                    'value':16 if r['cells']['ghi_chu']['style'].get('fs')!=16 else 20} for r in rows]
        payload={'protocol':2,'operation':str(uuid.uuid4()),'kind':'format' if style else 'paste','cells':cells}
        with self.client.post(base.base+'luu-json/',json=payload,name='write:style2000' if style else 'write:bulk2000',catch_response=True) as response:
            if response.status_code==409:response.success()
            elif response.status_code==200:
                actual={(c['id'],c['column'],c['property']):c['value'] for c in response.json()['cells']}
                expected={(c['id'],c['column'],c.get('property','value')):c['value'] for c in cells}
                if actual!=expected:self.invalid(response,'Bulk acknowledgement mismatch')


# Giữ trọng số và khoảng nghỉ của tải ngắn; chỉ thay nhánh ghi của một Admin.
EnduranceEditor.tasks=[EnduranceEditor.bulk_or_write if task is base.Editor.write else task for task in base.Editor.tasks]
