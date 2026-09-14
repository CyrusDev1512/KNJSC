"""Nghiệm thu bài bền từ bằng chứng HTTP, PostgreSQL, Chrome và Celery."""
import json
import math
from collections import defaultdict
from pathlib import Path

root = Path(__file__).resolve().parents[2] / 'storage/crm-update'
directory = root / 'load300'
gate = root / 'endurance-gate.json'
gate.write_text(json.dumps({'passed': False, 'reason': 'Đang kiểm lại bằng chứng.'}))


def read(name):
    return json.loads((directory / name).read_text(encoding='utf-8'))


def p95(values):
    return sorted(values)[math.ceil(len(values) * .95) - 1]


result = read('final-endurance-after-300000-20.json')
oracle = read('final-endurance-after-300000-20.oracle.json')
browser = read('endurance-browser.json')
jobs = read('background.json')
assert result['warmup'] == 60 and result['measured'] == 1800
assert not result['integrity_errors'] and not oracle['errors']
assert oracle['created'] > 0 and oracle['checked'] > 19
groups = defaultdict(list)
for sample in result['samples']:
    assert sample['status'] == 200 and not sample['error']
    groups[sample['name']].append(sample['ms'])
actions = []
for group in ('marketing', 'sale', 'van-don'):
    names = ['read', 'filter', 'save', 'history-new', 'create-new']
    if group != 'van-don':
        names.append('formula-save-new')
    for name in names:
        values = groups[f'{group}:{name}']
        assert len(values) >= 30
        limit = 500 if name in ('save', 'formula-save-new') else 1000
        latency = p95(values)
        assert latency <= limit, (group, name, latency, limit)
        actions.append({'action': f'{group}:{name}', 'n': len(values), 'p95': latency})
times = sorted(sample['t'] for sample in result['samples'])
assert times[0] < 65 and times[-1] > 1855
assert max(b - a for a, b in zip(times, times[1:])) < 5

assert browser['elapsed'] >= 1860 and not browser['errors']
samples = browser['samples']
assert len(samples) >= 500 and samples[-1]['t'] > 1855
assert all(s['cache'] <= 10 and s['cells'] <= 1500 for s in samples)
assert p95([s['ms'] for s in samples]) <= 100
conflicts = browser.get('versionConflicts', [])
recoveries = browser.get('recoveries', [])
if conflicts:
    assert recoveries and recoveries[-1]['t'] >= conflicts[-1]['t']
assert len(jobs) == 62 and all(job['status'] == 'done' for job in jobs)
exports = [job for job in jobs if job['kind'] == 'export']
assert len(exports) == 31 and all(job['verified_excel_rows'] == job['total'] for job in exports)

# Heap được ghi theo thời gian để xem dấu hiệu tăng; không tự đặt một ngưỡng
# RAM nghiệm thu mới hoặc dùng heap cuối thấp làm bằng chứng không rò nhớ.
evidence = {'passed': True, 'measured': result['measured'],
    'samples': len(result['samples']), 'oracle': oracle, 'actions': actions,
    'browser': {'samples': len(samples), 'p95': p95([s['ms'] for s in samples]),
        'cache_max': max(s['cache'] for s in samples),
        'cells_max': max(s['cells'] for s in samples),
        'dom_max': max(s['dom'] for s in samples),
        'heap_first': samples[0].get('heap'), 'heap_last': samples[-1].get('heap'),
        'heap_max': max(s.get('heap', 0) for s in samples),
        'version_conflicts': len(conflicts), 'recoveries': len(recoveries)},
    'background_jobs': len(jobs)}
gate.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(evidence, ensure_ascii=False))
