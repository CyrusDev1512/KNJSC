"""Read-only search/detail workload. Only the isolated ERP test container."""
import re, itertools, os
from locust import HttpUser, task, between, events
counter=itertools.count()
@events.test_start.add_listener
def guard(environment, **kw):
    import gevent
    assert environment.host=='http://knjsc-erp-final:8000'
    gevent.spawn_later(60,environment.stats.reset_all)
class Reader(HttpUser):
    wait_time=between(1,2)
    def on_start(self):
        self.client.headers.update({'Host':'localhost','Connection':'close'})
        self.username=['erp_mkt_0','erp_mkt_19','erp_mkt_manager','erp_admin'][next(counter)%4]
        r=self.client.get('/dang-nhap/',name='login_form')
        csrf=re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"',r.text).group(1)
        self.client.post('/dang-nhap/',data={'username':self.username,'password':'erp-test-only-2026','csrfmiddlewaretoken':csrf},headers={'Referer':'http://localhost/dang-nhap/'},name='login')
        r=self.client.get('/bao-cao/lich-su/',name='setup_history')
        self.detail=re.search(r'href="(/bao-cao/\d+/)"',r.text).group(1)
    @task(2)
    def code(self):
        with self.client.get('/bao-cao/lich-su/',params={'tim':'erp_mkt_0','tu':'2000-01-01','den':'2025-12-31'},name='history_code',catch_response=True) as response:
            if os.environ.get('IDENTITY_EXPECT_CODE') == '1' and 'data-employee-code="erp_mkt_0"' not in response.text:
                response.failure('Employee code result missing')
    @task(2)
    def name(self):
        self.client.get('/bao-cao/lich-su/',params={'tim':'ERP','tu':'2000-01-01','den':'2025-12-31'},name='history_name')
    @task
    def detail_page(self):
        self.client.get(self.detail,name='detail')
@events.quitting.add_listener
def result(environment, **kw):
    if environment.stats.total.num_failures or any(s.get_response_time_percentile(.95)>1000 for s in environment.stats.entries.values() if s.name in ['history_code','history_name','detail']):
        environment.process_exit_code=1
