import subprocess,sys,json
from pathlib import Path
root=Path(__file__).resolve().parent.parent
variant=sys.argv[1];assert variant in ['before','after','compat']
def run(*args):subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
# Chỉ DB do harness này tạo trên container/network riêng; không dùng Compose dev.
for name in ['knjsc-code-db','knjsc-code-app']:
 info=json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0]
 assert list(info['NetworkSettings']['Networks'])==['knjsc-code-test'], 'Sai network test'
run('docker','rm','-f','knjsc-code-app')
if variant!='compat':
 run('docker','exec','knjsc-code-db','dropdb','-U','code_test','test_knjsc_code_load')
 run('docker','exec','knjsc-code-db','createdb','-U','code_test','-T','test_knjsc_code_pristine','test_knjsc_code_load')
source=root/'before-app' if variant=='before' else root.parent.parent/'app'
args=['docker','run','-d','--name','knjsc-code-app','--network','knjsc-code-test','--env-file',str(root/'runtime.env'),'-e','POSTGRES_DB=test_knjsc_code_load','-e','DJANGO_SETTINGS_MODULE=mixed_settings','-p','127.0.0.1:8851:8000','-v',str(source)+':/app:ro','-v',str(root)+':/runtime','-v',str(root/'harness')+':/harness:ro']
for flag in ['READ','SYNC','RECEIPTS','RENDER','STATS','EXPORT','QUEUES']:
 args+=['-e','CRM_OPT_'+flag+'='+str(int(variant=='compat' and flag in ['READ','SYNC','RECEIPTS','RENDER']))]
args+=['knjsc-web','gunicorn','mixed_wsgi:application','--bind','0.0.0.0:8000','--workers','3','--threads','4','--timeout','60','--keep-alive','5']
subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
print('Started isolated app',variant,flush=True)
