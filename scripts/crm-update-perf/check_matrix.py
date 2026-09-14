"""Cổng bài bền: bốn lượt bản sau đủ thời gian, đúng dữ liệu và đạt p95."""
import json
import math
from collections import defaultdict
from pathlib import Path

root=Path(__file__).resolve().parents[2]/'storage/crm-update'
(root/'matrix-gate.json').write_text(json.dumps({'passed':False, 'reason':'Đang kiểm lại toàn bộ kết quả; không dùng cổng đạt của lượt trước.'}))
evidence=[]
for count in (100000,300000):
    for users in (10,20):
        file=root/('load100' if count==100000 else 'load300')/f'final-after-{count}-{users}.json'
        result=json.loads(file.read_text())
        oracle=json.loads(file.with_suffix('.oracle.json').read_text())
        assert result['measured']==300 and result['warmup']==60
        assert not result['integrity_errors'] and not oracle['errors'] and oracle['checked']==users
        groups=defaultdict(list)
        for sample in result['samples']:
            assert not sample['error'] and sample['status']==200
            groups[sample['name']].append(sample['ms'])
        rows=[]
        for group in ('marketing','sale','van-don'):
            for action in ('read','filter','save','history-new'):
                values=sorted(groups[group+':'+action])
                assert len(values)>=10
                p95=values[math.ceil(.95*len(values))-1]
                limit=500 if action=='save' else 1000
                rows.append({'action':group+':'+action,'n':len(values),'p95':p95,'limit':limit})
                assert p95<=limit,(file.name,group,action,p95,limit)
        times=sorted(s['t'] for s in result['samples'])
        assert times[0]<65 and times[-1]>355 and max(b-a for a,b in zip(times,times[1:]))<5
        evidence.append({'file':file.name,'samples':len(times),'oracle':oracle,'actions':rows})
(root/'matrix-gate.json').write_text(json.dumps({'passed':True,'phases':evidence},indent=2))
print(json.dumps({'passed':True,'phases':len(evidence)}))
