import time,json,os,re,threading
from django.db import connection
class Metrics:
 def __init__(self,get_response): self.get_response=get_response
 def __call__(self,request):
  start=time.perf_counter();queries=[];sql_errors=[]
  def execute(fn,sql,params,many,context):
   t=time.perf_counter()
   try:return fn(sql,params,many,context)
   except Exception as exc:
    cause=getattr(exc,'__cause__',None);diag=getattr(cause,'diag',None)
    sql_errors.append({'type':type(exc).__name__,'state':getattr(cause,'sqlstate',None),'constraint':getattr(diag,'constraint_name',None)})
    raise
   finally:
    text=sql.upper();tables=re.findall(r'(?:FROM|JOIN|INTO|UPDATE)\s+"([a-z_]+)"',sql,re.I)
    label=text.split()[0]+' '+','.join(dict.fromkeys(tables))
    if 'COUNT(' in text:label+=' COUNT'
    if 'MAX(' in text:label+=' MAX'
    if 'FOR UPDATE' in text:label+=' LOCK'
    if 'PG_ADVISORY_XACT_LOCK' in text:label+=' CODE_LOCK'
    if 'OFFSET' in text:label+=' OFFSET'
    queries.append((label,round((time.perf_counter()-t)*1000,3)))
  with connection.execute_wrapper(execute):response=self.get_response(request)
  elapsed=(time.perf_counter()-start)*1000;db=sum(v for k,v in queries)
  lock=sum(v for k,v in queries if 'CODE_LOCK' in k)
  response['Server-Timing']=f'app;dur={elapsed:.3f}, db;dur={db:.3f}, lock;dur={lock:.3f}'
  response['X-Test-Query-Count']=str(len(queries))
  row={'time':time.time(),'route':getattr(request.resolver_match,'route',None),'method':request.method,'status':response.status_code,'app_ms':round(elapsed,3),'lock_ms':round(lock,3),'db_ms':round(db,3),'queries':queries,'sql_errors':sql_errors}
  fd=os.open(f'/runtime/results/server-{os.getpid()}-{threading.get_ident()}.jsonl',os.O_CREAT|os.O_WRONLY|os.O_APPEND,0o600)
  try:os.write(fd,(json.dumps(row)+'\n').encode())
  finally:os.close(fd)
  return response
