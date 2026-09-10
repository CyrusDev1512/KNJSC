"""Tải JSON trước/sau, chỉ nhận manifest DB test do pytest tạo."""
import itertools
import json
import os
import random
import time
import uuid
from pathlib import Path
from locust import HttpUser, task, between, events

manifest = json.loads(Path(os.environ['MASTER_MANIFEST']).read_text())
assert manifest['database'].startswith('test_knjsc_master_capacity_nine')
slots = itertools.count()
samples = []
integrity_errors = []
started = time.monotonic()
warmup = int(os.environ.get('MASTER_WARMUP', '60'))
base = '/bang-tinh/van_don_moi/'


@events.request.add_listener
def collect(name, response_time, response_length, exception, **kwargs):
    if time.monotonic()-started >= warmup:
        samples.append({'name': name, 'ms': response_time, 'bytes': response_length,
                        'error': type(exception).__name__ if exception else None})


@events.quitting.add_listener
def finish(environment, **kwargs):
    Path(os.environ['MASTER_RESULT']).write_text(json.dumps({'warmup': warmup, 'elapsed': time.monotonic()-started, 'samples': samples, 'integrity_errors': integrity_errors}))


class Editor(HttpUser):
    wait_time = between(1, 3)

    def invalid(self, response, reason):
        response.failure(reason)
        integrity_errors.append(reason)
        self.environment.runner.quit()

    def on_start(self):
        self.actor = manifest['actors'][next(slots)]
        self.client.cookies.set('sessionid', self.actor['session'])
        self.client.cookies.set('csrftoken', manifest['csrf'])
        self.client.headers.update({'X-CSRFToken': manifest['csrf']})
        self.poll_at = 0

    @task(5)
    def read(self):
        total = self.actor['total']
        offset = random.choice([0, 100, 1000, total//2, max(0, total-100)])
        with self.client.get(base+f'du-lieu/?offset={offset}', name='read:block', catch_response=True) as r:
            if r.status_code == 200:
                ids = [row['id'] for row in r.json()['rows']]
                if len(ids) > 100 or len(ids) != len(set(ids)):
                    self.invalid(r, 'Unbounded or duplicate rows')
        if time.monotonic()-self.poll_at >= 8:
            self.client.get(base+'moi-nhat/', name='poll')
            self.poll_at = time.monotonic()

    @task(1)
    def filter(self):
        self.client.get(base+'du-lieu/?f_quoc_gia=USA', name='read:filter')

    @task(2)
    def write(self):
        with self.client.get(base+'du-lieu/?f_ma_don='+self.actor['code'], name='read:write-target', catch_response=True) as response:
            if response.status_code != 200:
                return
            rows = response.json()['rows']
            if len(rows) != 1:
                self.invalid(response, 'Missing target');return
            row = rows[0]
        value = uuid.uuid4().hex
        with self.client.post(base+'luu-json/', json={'operation': str(uuid.uuid4()), 'cells': [
                {'id': row['id'], 'column': 'ghi_chu', 'old': row['cells']['ghi_chu']['value'], 'value': value}]}, name='write:cell', catch_response=True) as r:
            if r.status_code == 409:
                r.success()  # CAS từ chối đúng; thống kê riêng, không coi là mất ghi.
                samples.append({'name': 'expected:conflict', 'ms': r.elapsed.total_seconds()*1000, 'bytes': 0, 'error': None})
            elif r.status_code == 200 and r.json()['rows'][0]['cells']['ghi_chu']['value'] != value:
                self.invalid(r, 'Wrong persisted value')
