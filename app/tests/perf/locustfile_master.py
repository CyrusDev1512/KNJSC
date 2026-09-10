"""AC-21: tải có giới hạn, chỉ nhận manifest do pytest DB test tạo."""
import itertools
import json
import os
import random
import time
import uuid
from pathlib import Path
from locust import HttpUser, task, between, events

manifest = json.loads(Path(os.environ['MASTER_MANIFEST']).read_text())
assert manifest['database'].startswith('test_knjsc_master_capacity')
assert os.environ['MASTER_STAGE'] in ('before', 'after')
assert int(os.environ['MASTER_USERS']) in (10, 20)
slots = itertools.count()
samples = []
started = time.monotonic()
base = '/bang-tinh/van_don_moi/'

@events.request.add_listener
def record(request_type, name, response_time, response_length, exception, **kwargs):
    if time.monotonic() - started >= 10:
        samples.append({'name': name, 'ms': response_time, 'bytes': response_length, 'error': str(exception) if exception else None})

@events.quitting.add_listener
def finish(environment, **kwargs):
    Path(os.environ['MASTER_RESULT']).write_text(json.dumps({'warmup_seconds': 10, 'samples': samples}))

class MasterUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.slot = next(slots)
        assert self.slot < 20
        self.actor = manifest['actors'][self.slot]
        self.client.cookies.set('sessionid', self.actor['session'])
        self.client.cookies.set('csrftoken', manifest['csrf'])
        self.client.headers.update({'X-CSRFToken': manifest['csrf']})
        self.value = self.actor['old']
        self.poll_at = 0

    @task(5)
    def read(self):
        offset = random.choice([0, 100, 1000, manifest['rows'] // 2, manifest['rows'] - 100])
        suffix = f'du-lieu/?offset={offset}' if os.environ['MASTER_STAGE'] == 'after' else f'?trang={offset//100+1}&moi_trang=100'
        self.client.get(base + suffix, name='read:block')
        if time.monotonic() - self.poll_at >= 8:
            self.client.get(base+'moi-nhat/', name='poll')
            self.poll_at = time.monotonic()

    @task(1)
    def filter(self):
        suffix = 'du-lieu/?' if os.environ['MASTER_STAGE'] == 'after' else '?'
        self.client.get(base+suffix+'f_quoc_gia=USA', name='read:filter')

    @task(2)
    def write(self):
        value = uuid.uuid4().hex
        if os.environ['MASTER_STAGE'] == 'after':
            with self.client.post(base+'luu-json/', json={'operation': str(uuid.uuid4()), 'cells': [
                    {'id': self.actor['row'], 'column': 'ghi_chu', 'old': self.value, 'value': value}]}, name='write:cell', catch_response=True) as response:
                if response.status_code == 200:
                    actual=response.json()['rows'][0]['cells']['ghi_chu']['value']
                    if actual != value: response.failure('Sai giá trị chuẩn hóa')
                    self.value = actual
        else:
            response=self.client.post(base+f"o/{self.actor['row']}/ghi_chu/", data={'gia_tri': value}, name='write:cell')
            if response.status_code == 200: self.value = value
