"""Số đo kỹ thuật; không ghi URL query, SQL, cookie hoặc nội dung request."""
import json
import logging
import os
import re
import time
import uuid
from django.conf import settings
from django.db import connection

logger=logging.getLogger('knjsc.request')


class RequestMetricsMiddleware:
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):
        if not getattr(settings,'CRM_REQUEST_METRICS',False):return self.get_response(request)
        raw=request.headers.get('X-Request-ID','')
        request_id=raw if re.fullmatch(r'[A-Za-z0-9_-]{1,64}',raw) else uuid.uuid4().hex
        request.request_id=request_id
        start=time.perf_counter();db_ms=0;queries=0;connect_ms=0;sqlstate=None;status=500
        original=connection.ensure_connection
        def ensure():
            nonlocal connect_ms
            missing=connection.connection is None;t=time.perf_counter()
            try:return original()
            finally:
                if missing:connect_ms+=(time.perf_counter()-t)*1000
        def execute(executor,sql,params,many,context):
            nonlocal db_ms,queries,sqlstate
            t=time.perf_counter();queries+=1
            try:return executor(sql,params,many,context)
            except Exception as exc:
                sqlstate=getattr(getattr(exc,'__cause__',None),'sqlstate',None)
                raise
            finally:db_ms+=(time.perf_counter()-t)*1000
        connection.ensure_connection=ensure
        try:
            with connection.execute_wrapper(execute):response=self.get_response(request)
            status=response.status_code
            response['X-Request-ID']=request_id
            response['Server-Timing']=f'db;dur={db_ms:.2f}, connect;dur={connect_ms:.2f}'
            return response
        finally:
            connection.ensure_connection=original
            logger.info(json.dumps({'request_id':request_id,'route':getattr(request.resolver_match,'route',None),
                'method':request.method,'status':status,'ms':round((time.perf_counter()-start)*1000,2),
                'pid':os.getpid(),'db_ms':round(db_ms,2),'connect_ms':round(connect_ms,2),'queries':queries,
                'db_pid':getattr(getattr(connection.connection,'info',None),'backend_pid',None),
                'sqlstate':sqlstate,'connection':request.headers.get('Connection','').lower() if request.headers.get('Connection','').lower() in ('close','keep-alive') else None}))
