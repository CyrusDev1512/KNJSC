"""CPU/RAM lấy mẫu trong đúng cửa sổ Locust; 100% CPU bằng một logical core."""
import json
import re
from datetime import datetime,timezone,timedelta
from pathlib import Path
root=Path(__file__).resolve().parents[2]/'storage/crm-update'
samples=[]
for file in root.glob('resources*.jsonl'):
    for line in file.read_text(encoding='utf-8-sig').splitlines():
        try:
            item=json.loads(line);stamp=datetime.fromisoformat(item['time'].replace('Z','+00:00'))
            for stat in item.get('stats') or []:
                memory=re.match(r'([\d.]+)(GiB|MiB|KiB|B)',stat['MemUsage'])
                if memory:samples.append((stamp,stat['Name'],float(stat['CPUPerc'].rstrip('%')),float(memory[1])*{'GiB':1024,'MiB':1,'KiB':1/1024,'B':1/1048576}[memory[2]]))
        except (ValueError,KeyError,TypeError):continue
results=[]
for file in sorted(root.glob('load*/final-*.json')):
    if '.oracle.' in file.name:continue
    result=json.loads(file.read_text())
    log=file.with_suffix('.log').read_text(encoding='utf-8-sig')
    match=re.search(r'\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),',log)
    if not match:continue
    start=datetime.strptime(match[1],'%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)+timedelta(seconds=result['warmup'])
    end=start+timedelta(seconds=result['measured'])
    for name in sorted({s[1] for s in samples}):
        selected=[s for s in samples if s[1]==name and start<=s[0]<=end]
        if selected:results.append({'phase':file.stem,'container':name,'n':len(selected),
            'cpu_mean':round(sum(s[2] for s in selected)/len(selected),2),'cpu_sample_max':max(s[2] for s in selected),
            'memory_mib_sample_max':round(max(s[3] for s in selected),2)})
(root/'resource-summary.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results[-4:],indent=2))
