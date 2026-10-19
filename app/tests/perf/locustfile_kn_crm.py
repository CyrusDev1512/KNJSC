"""TL-112/124 — kiểm tải JSON/cuộn ảo, chỉ môi trường riêng và dòng PERF-*.

Đo đọc khối, poll, sửa/dán và định dạng. Không gọi đường HTML đã bỏ; không
tự tạo đơn, đổi cột hay xoá dòng bằng quyền Leader. Các luồng đó được kiểm
riêng bằng regression/diễn tập có dữ liệu và quyền phù hợp.
Chạy scripts/kiem-tai-kn-crm.py; không chạy lên domain thật.
"""
import os
import random
import re
import time
import uuid
from urllib.parse import parse_qsl, urlencode, urlparse
from locust import HttpUser, between, events, task
from core.constants import PERF_READ_P95_MS, PERF_WRITE_P95_MS, PERF_POLL_P95_MS

PERF_PREFIX = 'PERF-'
BASE = '/bang-tinh/van_don/'
LIMITS = {'read':PERF_READ_P95_MS, 'write':PERF_WRITE_P95_MS, 'poll':PERF_POLL_P95_MS}


def require_local_target(host):
    if urlparse(host or '').hostname not in {'localhost','127.0.0.1','bangtinh','crm'}:
        raise ValueError('Chỉ nhận localhost hoặc dịch vụ CRM trong mạng Docker riêng.')
    if os.environ.get('KNJSC_PERF_ISOLATED') != '1':
        raise ValueError('Chạy bằng scripts/kiem-tai-kn-crm.py trên database riêng.')


def fake_row(row):
    return str(row.get('cells',{}).get('ma_don',{}).get('value') or '').startswith(PERF_PREFIX)


class TabLuoi(HttpUser):
    wait_time = between(2,5)

    def on_start(self):
        require_local_target(self.host or self.client.base_url)
        self.rows=[];self.goc=BASE;self.poll_at=0
        response=self.client.get('/dang-nhap/',name='login:form')
        token=re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"',response.text)
        response=self.client.post('/dang-nhap/',data={
            'username':os.environ.get('KNJSC_PERF_USER','vd.staff'),
            'password':os.environ.get('KNJSC_MAT_KHAU','matkhaucuatoi'),
            'csrfmiddlewaretoken':token.group(1) if token else self.client.cookies.get('csrftoken','')},
            headers={'Referer':self.client.base_url+'/dang-nhap/'},name='login:submit')
        if '/dang-nhap/' in response.url:
            raise RuntimeError('Đăng nhập thất bại; không đo với trang đăng nhập.')
        self.client.headers.update({'X-CSRFToken':self.client.cookies.get('csrftoken',''),
            'Referer':self.client.base_url+BASE})
        self.client.get(BASE,name='read:shell')

    def _luoi(self, qs='', ten='read:block'):
        params=dict(parse_qsl(qs))
        params['f_ma_don__bat_dau']=PERF_PREFIX
        response=self.client.get(self.goc+'du-lieu/?'+urlencode(params),name=ten)
        self.rows=[r for r in response.json().get('rows',[]) if fake_row(r)] if response.status_code==200 else []
        return response

    def _payload(self, n, *, formatting=False):
        candidates=[r for r in self.rows if fake_row(r) and r['cells'].get('ghi_chu',{}).get('editable')]
        chosen=random.sample(candidates,min(n,len(candidates)))
        if not chosen:
            return None
        return {'operation':str(uuid.uuid4()),'kind':'format' if formatting else 'paste', 'cells':[
            {'id':r['id'],'column':'ghi_chu',
             'property':'fs' if formatting else 'value',
             'old':r['cells']['ghi_chu'].get('style',{}).get('fs') if formatting else r['cells']['ghi_chu'].get('value'),
             'value':random.choice([12,13,14]) if formatting else 'PERF '+uuid.uuid4().hex}
            for r in chosen]}

    @task(6)
    def read(self):
        self._luoi('offset='+str(random.choice([0,100,500,1000])))
        if time.monotonic()-self.poll_at>=8:
            self.client.get(BASE+'moi-nhat/',name='poll:latest')
            self.poll_at=time.monotonic()

    @task(2)
    def filtered(self):
        self._luoi('sap=ngay&chieu=giam',ten='read:sort')

    @task(2)
    def write(self):
        payload=self._payload(random.choice([1,5,100]),formatting=random.random()<0.2)
        if not payload:
            self._luoi()
            return
        # Không đổi 4xx/5xx thành thành công; 409 cũng được ghi rõ trong kết quả.
        response=self.client.post(BASE+'luu-json/',json=payload,name='write:cells')
        if response.status_code==200:
            changed={r['id']:r for r in response.json().get('rows',[]) if fake_row(r)}
            self.rows=[changed.get(r['id'],r) for r in self.rows]
        else:
            self.rows=[]


@events.quitting.add_listener
def finish(environment, **kwargs):
    ok=True
    smoke=os.environ.get('KNJSC_PERF_SMOKE')=='1'
    for group,limit in LIMITS.items():
        entries=[e for e in environment.stats.entries.values() if e.name.startswith(group+':')]
        count=sum(e.num_requests for e in entries)
        failed=sum(e.num_failures for e in entries)
        p95=max((e.get_response_time_percentile(.95) or 0 for e in entries),default=0)
        passed=count>0 and failed==0 and (smoke or (count>=20 and p95<=limit))
        ok &= passed
        print(f'{group}: {count} yêu cầu, {failed} lỗi, p95 quan sát {p95} ms; '+
              ('SMOKE — không nghiệm thu hiệu năng' if smoke else 'ĐẠT' if passed else 'CHƯA ĐẠT/THIẾU MẪU'))
    print('Không đo ở đây: lên đơn, đổi cấu trúc/tính lại, xoá/khôi phục. Không coi là đã đạt.')
    environment.process_exit_code=0 if ok and not environment.stats.total.num_failures else 1
