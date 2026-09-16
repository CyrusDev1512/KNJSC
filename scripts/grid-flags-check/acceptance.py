"""Lượt đo chính sau khi đã chuẩn hóa tài nguyên và cách dừng Locust."""
import json
import time
from run import ROOT, start, phase

deadline = time.monotonic() + 600
marker = ROOT / "results/final-before-delivery-integrity.json"
while not marker.exists():
    assert time.monotonic() < deadline
    time.sleep(2)
report = json.loads((ROOT / "results/final-before-delivery.json").read_text())
assert report["measured_seconds"] >= 300 and not report["abort"]
assert not json.loads(marker.read_text())["errors"]
assert not json.loads((ROOT / "results/final-before-delivery-browser.json").read_text())["errors"]
for name, variant, mixed in [
    ("final-after-delivery", "after", False),
    ("final-after-mixed", "after", True),
    ("final-sync-mixed", "sync", True),
]:
    start(variant)
    phase(name, variant, mixed, 362)
print("ACCEPTANCE PHASES DONE", flush=True)
