import subprocess,os,sys,json,time
from pathlib import Path
root=Path(__file__).resolve().parent.parent
phase=sys.argv[1]; mixed=len(sys.argv)>2 and sys.argv[2]=='mixed'
assert phase in ['before-delivery','after-delivery','after-mixed','compat-smoke']
seconds=362 if phase!='compat-smoke' else 45
warm=60 if seconds>60 else 0
node=Path('C:/Users/PC/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
env={**os.environ,'NODE_PATH':str(node.parent.parent/'node_modules'),'PHASE':phase,'DURATION':str(seconds+10),'WARMUP':str(warm)}
logs=[]
def launch(name,args,env=None):
 f=(root/'results'/f'{phase}-{name}.log').open('w',encoding='utf-8');logs.append(f)
 return subprocess.Popen(args,stdout=f,stderr=subprocess.STDOUT,env=env)
browser=launch('chrome',[str(node),str(root/'harness/browser.cjs')],env)
resources=launch('resources',[sys.executable,str(root/'harness/resources.py'),phase])
args=['docker','run','--rm','--name','knjsc-code-load','--network','knjsc-code-test','--env-file',str(root/'runtime.env'),'-e','PHASE='+phase,'-e','WARMUP='+str(warm),'-e','DELIVERY_USERS=9','-e','MIXED='+str(int(mixed)),'-e','PROTOCOL='+('2' if phase=='compat-smoke' else '1'),'-v',str(root)+':/runtime','-v',str(root/'harness')+':/harness:ro','knjsc-web','locust','-f','/harness/locust_mixed.py','--headless','--host','http://knjsc-code-app:8000','-u',str(39 if mixed else 9),'-r','2','-t',str(seconds)+'s','--only-summary']
load=launch('locust',args)
rc=load.wait();browser_rc=browser.wait(timeout=65);resources.wait(timeout=20)
for f in logs:f.close()
report=json.loads((root/'results'/f'{phase}.json').read_text())
print(json.dumps({'phase':phase,'exit':rc,'browser_exit':browser_rc,'measured_seconds':report['measured_seconds'],'abort':report['abort'],'server_errors':report['unexpected_server_errors'],'orders':len(report['orders']),'operations':report['operations']},indent=2),flush=True)
