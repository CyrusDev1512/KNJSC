"""Tổng hợp cửa sổ đo thực tế; không tính warmup vào percentile."""
import json
import math
import re
from collections import defaultdict
from pathlib import Path

root = Path(__file__).resolve().parents[2] / 'storage/crm-update'


def percentile(values, p):
    values = sorted(values)
    return round(values[max(0, math.ceil(len(values) * p) - 1)], 2) if values else None


results = []
for file in sorted(root.glob('load*/final-*.json')):
    if '.oracle.' in file.name:
        continue
    result = json.loads(file.read_text(encoding='utf-8'))
    groups = defaultdict(list)
    for sample in result['samples']:
        groups[sample['name']].append(sample)
    times = sorted(s['t'] for s in result['samples'])
    phase = {key: result[key] for key in ('stage', 'rows', 'measured', 'elapsed')}
    phase.update(file=str(file.relative_to(root)), errors=result['integrity_errors'],
                 samples=len(times), first=times[0] if times else None,
                 last=times[-1] if times else None,
                 max_gap=round(max((b-a for a,b in zip(times,times[1:])),default=0),3), actions=[])
    for name, samples in sorted(groups.items()):
        values = [s['ms'] for s in samples]
        sql = [float(m.group(1)) for s in samples if (m:=re.search(r'db;dur=([\d.]+)',s.get('sql') or ''))]
        phase['actions'].append({'name':name,'n':len(values), 'p50':percentile(values,.5),
            'p95':percentile(values,.95),'p99':percentile(values,.99),
            'sql_p95':percentile(sql,.95), 'bytes_p50':percentile([s['bytes'] for s in samples],.5),
            'rps':round(len(values)/result['measured'],3) if result['measured'] else 0,
            'errors':sum(bool(s['error']) or s['status']>=400 for s in samples)})
    results.append(phase)
(root/'load-summary.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['| Lượt | Nhóm | Mẫu | p50 ms | p95 ms | p99 ms | SQL p95 ms | req/s | Lỗi |',
       '|---|---|---:|---:|---:|---:|---:|---:|---:|']
for phase in results:
    for action in phase['actions']:
        lines.append('| '+ ' | '.join(str(v) for v in [Path(phase['file']).stem,action['name'],action['n'],
            action['p50'],action['p95'],action['p99'],action['sql_p95'],action['rps'],action['errors']])+' |')
(root/'load-summary.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps([{'file':r['file'],'measured':r['measured'],'samples':r['samples'],'max_gap':r['max_gap'],
                  'errors':r['errors']} for r in results],indent=2))
