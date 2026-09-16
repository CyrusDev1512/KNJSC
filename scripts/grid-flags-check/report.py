"""Xuất số đo gọn; không đưa session test, giá trị ô hoặc tài khoản vào Git."""
import json
import sys
from pathlib import Path
from run import ROOT

result = {"source": json.loads((ROOT / "manifest.json").read_text()), "runs": {}, "browser": {}}
analysis_path = ROOT / "results/analysis.json"
analysis = json.loads(analysis_path.read_text()) if analysis_path.exists() else {}
for name in sys.argv[1:]:
    data = json.loads((ROOT / "results" / (name + ".json")).read_text())
    integrity = json.loads((ROOT / "results" / (name + "-integrity.json")).read_text())
    browser = json.loads((ROOT / "results" / (name + "-browser.json")).read_text())
    record = {key: data[key] for key in ["warmup", "measured_seconds", "abort", "unexpected_server_errors", "operations"]}
    record["integrity"] = integrity
    record["browser_errors"] = browser["errors"]
    record["browser_memory"] = browser.get("memorySamples", [])
    stop = ROOT / "results" / (name + "-stop.json")
    if stop.exists():
        record["early_stop"] = json.loads(stop.read_text())
    runtime = ROOT / "results" / (name + "-runtime.json")
    if runtime.exists():
        record["runtime"] = json.loads(runtime.read_text())
    if name in analysis:
        measured = analysis[name]
        record["analysis"] = {key: measured[key] for key in
                              ["window_seconds", "browser", "routes", "top_sql_categories", "resources"]}
        record["analysis"]["sql_error_count"] = len(measured["sql_errors"])
    result["runs"][name] = record
for file in (ROOT / "results").glob("*-real-browser.json"):
    result["browser"][file.stem] = json.loads(file.read_text())
for name in ["flag-contract", "invalidation-audit"]:
    file = ROOT / "results" / (name + ".json")
    if file.exists():
        result[name] = json.loads(file.read_text())
destination = ROOT.parents[1] / "docs/verification/grid-flags-20260916.json"
destination.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(destination)
