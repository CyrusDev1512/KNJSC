"""Hồi quy browser lưới chung trên database test khác, chỉ chạy khi dừng đo tải."""
import json
import os
import subprocess
import time
from run import ROOT, NODE, common

assert subprocess.run(["docker", "inspect", "knjsc-gridflags-load"], capture_output=True).returncode != 0, "Không chồng browser lên lượt kiểm tải"
folder = ROOT / "shared"
folder.mkdir(exist_ok=True)
source = ROOT.parents[1] / "scripts/kiem-thu-shared-grid.cjs"
script = ROOT / "harness/shared.cjs"
script.write_text(source.read_text(encoding="utf-8").replace("../storage/crm-update", "../shared").replace("127.0.0.1:8854", "127.0.0.1:18642"), encoding="utf-8")
ready = folder / "shared-browser-ready.json"
assert not ready.exists(), "Fixture trước còn chạy"
with (folder / "server.log").open("w", encoding="utf-8") as log:
    server = subprocess.Popen(["docker", "run", "--rm", "--name", "knjsc-gridflags-shared", *common(),
        "-e", "POSTGRES_DB=gridflags_shared_browser", "-e", "DJANGO_SETTINGS_MODULE=knjsc.settings.test",
        "-e", "CRM_UPDATE_BROWSER=1", "-p", "127.0.0.1:18642:18642", "-v", str(folder) + ":/evidence",
        "-v", str(ROOT / "after/app") + ":/app:ro", "knjsc-web", "pytest", "crm/tests/test_shared_browser_server.py",
        "--liveserver=0.0.0.0:18642", "-o", "addopts=--ds=knjsc.settings.test", "-q", "-p", "no:cacheprovider"], stdout=log, stderr=subprocess.STDOUT)
    deadline = time.monotonic() + 90
    while not ready.exists():
        assert server.poll() is None, "Fixture không khởi động; xem server.log"
        assert time.monotonic() < deadline, "Fixture chưa sẵn sàng"
        time.sleep(.5)
    result = subprocess.run([str(NODE), str(script)], env={**os.environ, "NODE_PATH": str(NODE.parent.parent / "node_modules")})
    rc = server.wait(timeout=40)
    assert result.returncode == rc == 0, "Browser hoặc kiểm chứng server thất bại"
print(json.dumps({"shared_browser": "passed"}))
