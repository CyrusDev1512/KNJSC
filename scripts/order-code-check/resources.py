import subprocess,json,time,sys
from pathlib import Path
p=Path(__file__).resolve().parent.parent/'results';phase=sys.argv[1]
names=['knjsc-code-app','knjsc-code-db','knjsc-code-redis','knjsc-code-load']
end=time.monotonic()+450
with (p/(phase+'-resources.jsonl')).open('w') as f:
 while time.monotonic()<end and not (p/(phase+'.json')).exists():
  r=subprocess.run(['docker','stats','--no-stream','--format','{{json .}}',*names],capture_output=True,text=True)
  rows=[]
  for line in r.stdout.splitlines():
   try:rows.append(json.loads(line))
   except ValueError:pass
  f.write(json.dumps({'time':time.time(),'containers':rows})+'\n');f.flush();time.sleep(5)
print('resources finished',phase)
