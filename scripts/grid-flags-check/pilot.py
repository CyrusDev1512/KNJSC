"""Chuỗi kiểm ngắn sau lượt after-delivery; dừng khi có lỗi toàn vẹn/browser."""
import json
import os
import subprocess
import sys
import time
from run import ROOT, NODE, start, phase

deadline = time.monotonic() + 600
previous = sys.argv[1] if len(sys.argv) > 1 else "after-delivery"
marker = ROOT / "results" / (previous + "-integrity.json")
while not marker.exists():
    assert time.monotonic() < deadline, "Hết thời gian chờ lượt tải trước"
    time.sleep(2)
assert not json.loads(marker.read_text())["errors"]
assert not json.loads((ROOT / "results" / (previous + "-browser.json")).read_text())["errors"]
env = {**os.environ, "NODE_PATH": str(NODE.parent.parent / "node_modules")}
script = ROOT.parents[1] / "scripts/grid-flags-check/browser-real.cjs"
subprocess.run(["docker", "cp", str(script.parent / "contract.py"), "knjsc-gridflags-app:/tmp/grid_flag_contract.py"], check=True)
subprocess.run(["docker", "exec", "knjsc-gridflags-app", "python", "/tmp/grid_flag_contract.py"], check=True)
assert all(not item["errors"] for item in json.loads((ROOT / "results/flag-contract.json").read_text()))
if not (ROOT / "results/after-real-real-browser.json").exists():
    subprocess.run([str(NODE), str(script), "after-real"], check=True, env=env)
for variant in ["render", "read", "sync"]:
    start(variant)
    phase("pilot-" + variant, variant, True, 45)
    subprocess.run([str(NODE), str(script), variant + "-real"], check=True, env=env)
print("PILOT DONE", flush=True)
