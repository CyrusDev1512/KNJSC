"""ERP isolated verification. Refuse active application ports."""
import os,re,itertools,time,json
from datetime import date,timedelta
from locust import HttpUser,task,between,events

counter=itertools.count()
submitted=0
mode=os.environ.get("ERP_MODE","baseline")
@events.test_start.add_listener
def guard(environment,**kw):
    import gevent
    gevent.spawn_later(60, environment.stats.reset_all)
    assert environment.host in ("http://127.0.0.1:8134","http://127.0.0.1:8135","http://knjsc-erp-baseline-v1:8000","http://knjsc-erp-final:8000"), "ERP test hosts only"

class ERPUser(HttpUser):
    wait_time=between(1,3)
    def on_start(self):
        self.client.headers.update({"Host":"localhost", "Connection":"close"})
        self.number=next(counter)%20
        kind=("mkt", "sale", "vd")[self.number % 3]
        self.kind=kind
        self.source="van_don" if kind == "vd" else "bao_cao_"+kind
        self.day=0
        role=self.number%5
        self.username = "erp_admin" if role==4 else f"erp_{kind}_manager" if role==3 else f"erp_{kind}_19" if role==2 else f"erp_{kind}_{self.number}"
        self.can_submit=role in (0,1) and kind != "vd"
        page=self.client.get("/dang-nhap/",name="login_form")
        token=re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"',page.text).group(1)
        self.client.post("/dang-nhap/",data={"username":self.username,"password":"erp-test-only-2026","csrfmiddlewaretoken":token},headers={"Referer":"http://localhost/dang-nhap/"},name="login")
        self.params={"nguon":self.source,"tu":"2020-01-01","den":"2025-12-31"}
    @task(3)
    def history(self):
        self.client.get("/bao-cao/lich-su/",params={"tu":"2020-01-01","den":"2025-12-31"},name="read_history")
    @task(3)
    def summary(self):
        path="/bao-cao/tong-hop/" if mode=="baseline" else "/bao-cao/hoat-dong/"
        self.client.get(path,params=self.params,name="read_summary_" + self.kind)
    @task(2)
    def dashboard(self):
        self.client.get("/",params={"mkt_tu":"2020-01-01","mkt_den":"2025-12-31","tu":"2020-01-01","den":"2025-12-31"},name="read_dashboard")
    @task(1)
    def export(self):
        path="/bao-cao/tong-hop/xuat/" if mode=="baseline" else "/bao-cao/hoat-dong/xuat/"
        self.client.get(path,params={**self.params,"tu":"2020-01-01","den":"2020-01-31"},name="export_" + self.kind)
    @task(1)
    def submit(self):
        if not self.can_submit:
            self.history()
            return
        self.day+=1
        page=self.client.get("/bao-cao/",params={"bieu_mau":f"bc_{self.kind}_ngay"},name="submission_form")
        token=re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"',page.text).group(1)
        day=(date(2040,1,1)+timedelta(days=self.day+int(os.environ.get("ERP_DAY_OFFSET","0")))).isoformat()
        data={"csrfmiddlewaretoken":token,"bieu_mau":f"bc_{self.kind}_ngay","ngay_bao_cao":day,
            f"{self.kind}_ngay":day,f"{self.kind}_san_pham":"ERP product 0",f"{self.kind}_thi_truong":"Canada",f"{self.kind}_so_mess":"100",f"{self.kind}_so_don":"5",f"{self.kind}_doanh_so":"1000",f"{self.kind}_cpqc":"200"}
        with self.client.post("/bao-cao/",data=data,headers={"Referer":"http://localhost/bao-cao/"},name="submit",catch_response=True) as r:
            if "/lich-su/" not in r.url:
                r.failure("Submission not persisted/redirected")
                self.environment.runner.quit()


@events.request.add_listener
def verify_write(request_type, name, exception, **kwargs):
    global submitted
    if request_type == "POST" and name == "submit" and exception is None:
        submitted += 1


@events.quitting.add_listener
def acceptance(environment, **kwargs):
    reads = [entry for entry in environment.stats.entries.values()
             if entry.name.startswith("read_") and entry.num_requests]
    failures = environment.stats.total.num_failures
    passed = failures == 0 and all(entry.get_response_time_percentile(.95) <= 1000 for entry in reads)
    proof = {"mode": mode, "offset": os.environ.get("ERP_DAY_OFFSET", "0"),
             "writes_including_warmup": submitted, "passed": passed,
             "failures": failures, "read_p95": {entry.name: entry.get_response_time_percentile(.95) for entry in reads}}
    filename = f"/storage/erp-verification/proof-{mode}-{proof['offset']}.json"
    with open(filename, "w") as output:
        json.dump(proof, output, indent=2)
    if not passed:
        environment.process_exit_code = 1
