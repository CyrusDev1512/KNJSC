"""Chuẩn bị bản đối chứng bất biến và harness kiểm tải trên DB riêng.

Không chạy migration/seed ở đây. Runtime chứa session test, không được commit.
"""
import hashlib
import io
import json
import secrets
import shutil
import subprocess
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "storage/grid-flags-20260916"
assert not (ROOT / "manifest.json").exists(), "Đã cố định nguồn; không ghi đè một lượt đo"
ROOT.mkdir(parents=True, exist_ok=True)
(ROOT / "results").mkdir(exist_ok=True)
commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
archive = subprocess.check_output(["git", "archive", "--format=zip", commit, "app"], cwd=REPO)
with zipfile.ZipFile(io.BytesIO(archive)) as z:
    z.extractall(ROOT / "before")
shutil.copytree(ROOT / "before", ROOT / "after")
source = (REPO / "app/static/js/master-grid.js").read_text(encoding="utf-8")
baseline = (ROOT / "before/app/static/js/master-grid.js").read_text(encoding="utf-8")
# Chỉ đưa tối ưu cuộn/chọn ô vào bản đo; không lấy tính năng ngày của task ERP.
start = source.index("    // Bộ nhập dùng D/M/Y;")
end = source.index("    if(options.length", start)
old_start = baseline.index("    // Ngày giờ giữ ô chữ ISO")
old_end = baseline.index("    if(options.length", old_start)
source = source[:start] + baseline[old_start:old_end] + source[end:]
start = source.index("    let display=original.display;")
end = source.index("\n  function refreshStatus", start)
old_start = baseline.index("    return {...original,value,style,class:classes,display:")
old_end = baseline.index("\n  function refreshStatus", old_start)
source = source[:start] + baseline[old_start:old_end] + source[end:]
source = source.replace("    if(!discard&&editor.elements.value&&!editor.elements.value.reportValidity())return false;\n", "")
(ROOT / "after/app/static/js/master-grid.js").write_text(source, encoding="utf-8", newline="\n")
for relative in ["crm/services/optimization.py", "crm/tests/test_optimization_contract.py"]:
    shutil.copyfile(REPO / "app" / relative, ROOT / "after/app" / relative)
harness = ROOT / "harness"
harness.mkdir(exist_ok=True)
for filename in ["mixed_settings.py", "mixed_wsgi.py", "mixed_metrics.py", "setup.py", "seed.py", "locust_mixed.py", "browser.cjs", "verify.py", "resources.py", "analyze.py"]:
    text = (REPO / "scripts/order-code-check" / filename).read_text(encoding="utf-8")
    text = text.replace("knjsc-code-", "knjsc-gridflags-").replace("test_knjsc_code_load", "test_knjsc_gridflags_load").replace("8851", "18641")
    if filename == "seed.py":
        text = text.replace("PaymentMethod.CARD", "PaymentMethod.ZELLE")
        # Ba thị trường có tiền tệ khác nhau; không seed nhãn tiền sai quốc gia.
        text = text.replace("'loai_tien':'USD'", "'loai_tien':['USD','CAD','PHP'][i%3]")
        text = text.replace("total=Decimal('40.40'),currency='USD'", "total=Decimal('40.40'),currency=['USD','CAD','PHP'][i%3]")
    if filename == "locust_mixed.py":
        text = text.replace("if PROTOCOL==2 and d.get('query_token')", "if os.environ.get('SYNC')=='1' and PROTOCOL==2 and d.get('query_token')")
        text = text.replace("if time.monotonic()-self.last_poll>=8:", "if time.monotonic()-self.last_poll>=8 and os.environ.get('SYNC')!='1':")
        text = text.replace("if T0 and time.time()-T0>=WARM:", "if T0 and WARM<=time.time()-T0<=WARM+float(os.environ.get('MEASURE_SECONDS','3600')):")
        text = text.replace("duration=max(0,time.time()-T0-WARM)", "duration=max(0,min(time.time()-T0-WARM,float(os.environ.get('MEASURE_SECONDS','3600'))))")
        text = text.replace("orders=[];attempts=[];writes={};", "orders=[];attempts=[];writes={};cell_attempts=[];cell_acks=[];")
        text = text.replace("   with self.client.post('/bang-tinh/van_don/luu-json/'", "   cell_attempts.append({'id':row['id'],'value':val,'actor':self.actor['username']})\n   with self.client.post('/bang-tinh/van_don/luu-json/'")
        text = text.replace("else:writes[str(row['id'])]=val;self.version=''", "else:writes[str(row['id'])]=val;cell_acks.append({'id':row['id'],'value':val,'actor':self.actor['username']});self.version=''")
        text = text.replace("'writes':writes,'all_requests'", "'writes':writes,'cell_attempts':cell_attempts,'cell_acks':cell_acks,'all_requests'")
    if filename == "verify.py":
        text = text.replace("actual={str(i):", "ack_values={x['value'] for x in m.get('cell_acks',[])}\nfor item in m.get('cell_attempts',[]):\n if item['value'] not in ack_values:errors.append({'kind':'cell_attempt_without_ack','id':item['id']})\nhistory=set(GridCellHistory.objects.filter(after__in=list(ack_values),column='ghi_chu').values_list('record_id','after','receipt__actor__username'))\nfor item in m.get('cell_acks',[]):\n if (item['id'],item['value'],item['actor']) not in history:errors.append({'kind':'cell_ack_without_history','id':item['id']})\nactual={str(i):")
    if filename == "analyze.py":
        text = text.replace("browser=json.loads", "hi=min(hi,lo+m['measured_seconds']) if not diagnostic else hi\n browser=json.loads")
    if filename == "resources.py":
        text = text.replace("+450", "+float(__import__('os').environ.get('DURATION','450'))+30")
    if filename == "browser.cjs":
        # Lỗi Chrome phải làm cả lượt đo không đạt, không âm thầm thoát 0.
        text = text.replace("result.finished=Date.now();", "if(result.errors.length)process.exitCode=1;result.finished=Date.now();")
        # Không để chính probe tăng RAM suốt lượt chạy bền.
        text = text.replace("window.probeFrames.push({start:t,duration:t-prev});", "if(window.probeFrames.length<3600)window.probeFrames.push({start:t,duration:t-prev});")
        text = text.replace("i++;await sleep(3000);", "if(i%20===0)(result.memorySamples||=[]).push({time:Date.now(),...(await page.evaluate(()=>({heap:performance.memory?.usedJSHeapSize,grid:KNJSC_MASTER.diagnostics()})))});i++;await sleep(3000);")
    (harness / filename).write_text(text, encoding="utf-8", newline="\n")
(ROOT / "shared").mkdir(exist_ok=True)
shared = (REPO / "scripts/kiem-thu-shared-grid.cjs").read_text(encoding="utf-8")
shared = shared.replace("../storage/crm-update", "../shared").replace("127.0.0.1:8854", "127.0.0.1:18642")
(harness / "shared.cjs").write_text(shared, encoding="utf-8", newline="\n")
env = {
    "POSTGRES_HOST": "knjsc-gridflags-db", "POSTGRES_PORT": "5432",
    "POSTGRES_USER": "gridflags_test", "POSTGRES_DB": "test_knjsc_gridflags_load",
    "POSTGRES_PASSWORD": secrets.token_urlsafe(32), "DJANGO_SECRET_KEY": secrets.token_urlsafe(48),
    "RUN_MIGRATIONS": "0", "PYTHONPATH": "/harness:/app",
    "REDIS_URL": "redis://knjsc-gridflags-redis:6379/0", "DJANGO_SETTINGS_MODULE": "mixed_settings",
}
(ROOT / "runtime.env").write_text("\n".join(f"{k}={v}" for k, v in env.items()) + "\n", encoding="utf-8")
manifest = {"baseline_commit": commit, "candidate_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "baseline_sha256": hashlib.sha256(baseline.encode()).hexdigest(),
            "read_contract_sha256": hashlib.sha256((ROOT / "after/app/crm/services/optimization.py").read_bytes()).hexdigest(),
            "excluded": "Uncommitted ERP/date changes", "rows": 100000,
            "runtime": "PostgreSQL16 1280MiB/Redis7; app 1 worker x 4 threads 640MiB; no CPU quota; separate network/DB; shared Docker host"}
(ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps(manifest))
