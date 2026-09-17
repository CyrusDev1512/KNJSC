"""Lên đơn: đọc form, xem trước Decimal và đọc đơn gốc trên fixture test_order_hub_browser_server; 10s làm nóng + 60s đo."""
import json
import os
import re
import time
from collections import defaultdict
from pathlib import Path
from locust import HttpUser, between, events, task

manifest = json.loads(Path('/app/.order-hub-ready.json').read_text())
assert manifest['database'].startswith('test_')
users = int(os.environ['HUB_USERS'])
assert users in (10, 20)
actor = os.environ.get('HUB_ACTOR', 'staff_sale_1')
check = os.environ.get('HUB_CHECK', 'entry')
assert actor in ('staff_sale_1', 'quan_tri') and check in ('entry', 'clock')
started = time.monotonic()
samples = defaultdict(list)
errors = defaultdict(int)


@events.request.add_listener
def measured(name, response_time, exception, **kwargs):
    if time.monotonic() - started >= 10 and name in ('entry', 'preview', 'original_order'):
        samples[name].append(response_time)
        errors[name] += int(exception is not None)


class Reader(HttpUser):
    wait_time = between(.2, .5)

    def on_start(self):
        assert self.host == 'http://127.0.0.1:8812'
        page = self.client.get('/dang-nhap/', name='login')
        token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page.text).group(1)
        response = self.client.post('/dang-nhap/', {'username':actor,
            'password':'matkhau-kiem-thu-1', 'csrfmiddlewaretoken':token}, name='login',
            headers={'Referer': self.host + '/dang-nhap/'})
        assert response.status_code == 200 and '/dang-nhap/' not in response.url

    def read(self, url, name, marker):
        with self.client.get(url, name=name, catch_response=True) as response:
            if response.status_code != 200 or marker not in response.text or '/dang-nhap/' in response.url:
                response.failure('Trang sai trạng thái, mất phiên hoặc thiếu nội dung')

    @task
    def entry(self):
        self.read('/van-don/len-don/', 'entry', 'order-date')

    @task
    def preview(self):
        with self.client.post('/van-don/len-don/tom-tat/', {'product': manifest['products'][0],
                'quantity': '2', 'unit_price': '10.10', 'unit': 'hộp', 'currency': 'USD'},
                headers={'X-CSRFToken': self.client.cookies.get('csrftoken'), 'Referer': self.host + '/van-don/len-don/'},
                name='preview', catch_response=True) as response:
            if response.status_code != 200 or response.json().get('total') != '20.20':
                response.failure('Xem trước không khớp Decimal hoặc không thành công')

    @task
    def original_order(self):
        self.read('http://127.0.0.1:8812/van-don/don-goc/' + manifest['order'] + '/',
                  'original_order', manifest['order'])


@events.quitting.add_listener
def report(environment, **kwargs):
    duration = time.monotonic() - started - 10
    result = {'users': users, 'actor': actor, 'warmup_seconds': 10, 'measured_seconds': round(duration,2), 'operations': {}}
    for name, values in samples.items():
        values.sort()
        def percentile(p):
            return round(values[min(len(values)-1, int(len(values)*p))],2)
        result['operations'][name] = {'requests':len(values), 'p50_ms':percentile(.5),
            'p95_ms':percentile(.95), 'p99_ms':percentile(.99), 'errors':errors[name],
            'requests_per_second':round(len(values)/duration,2)}
    ok = len(samples) == 3 and all(v['p95_ms'] <= 1000 and not v['errors'] for v in result['operations'].values())
    result['ok'] = ok
    Path(f'/storage/order-{check}-load-{users}.json').write_text(json.dumps(result, indent=2))
    if not ok: environment.process_exit_code = 1
