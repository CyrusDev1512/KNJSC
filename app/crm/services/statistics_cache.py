"""Số liệu sống tối đa 15 giây; quyền luôn lấy từ PostgreSQL hiện hành."""
import copy
import math
import time
from functools import wraps
from django.core.cache import caches
from django.db import connection, transaction
from django.utils import timezone
from crm.models import GridRevision
from .optimization import digest, enabled, scope_key


def snapshot(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not enabled('STATS') or connection.in_atomic_block:
            return view(*args, **kwargs)
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
            from django.contrib.auth import get_user_model
            from django.core.exceptions import PermissionDenied
            request=args[0]
            current=get_user_model().objects.select_related('profile').filter(pk=request.user.pk,is_active=True).first()
            if current is None:raise PermissionDenied
            request.user=current
            return view(*args, **kwargs)
    return wrapped


def result(user, tables, params, date_from, date_to, build):
    def calculate():
        # Tính tuổi từ đầu snapshot, không kéo dài khi GET lại.
        now=timezone.now()
        return {'calculated':now,'value':build()}
    if not enabled('STATS'):
        return calculate()
    epochs={row.table_id:[row.fields.get('__access',0),row.fields.get('__schema',0)]
            for row in GridRevision.objects.filter(table_id__in=[t.pk for t in tables])}
    query=sorted((k,params.getlist(k)) for k in params if k!='lam_moi' and k!='trang' and not k.startswith('chart_'))
    key='statistics:'+digest([connection.settings_dict['NAME'],scope_key(user),sorted(t.pk for t in tables),epochs,query,date_from,date_to])
    def valid(value):
        return value is not None and (timezone.now()-value['calculated']).total_seconds()<15
    try:
        cache=caches['crm']
        value=None if params.get('lam_moi')=='1' else cache.get(key)
        if valid(value):return copy.deepcopy(value)
        # Lease không xóa thủ công: tránh xóa khóa mới của request khác khi lease hết.
        owner=cache.add(key+':computing',True,15)
        if not owner and params.get('lam_moi')!='1':
            deadline=time.monotonic()+2
            while time.monotonic()<deadline:
                time.sleep(.05);value=cache.get(key)
                if valid(value):return copy.deepcopy(value)
    except Exception:
        return calculate()
    value=calculate()
    ttl=15-(timezone.now()-value['calculated']).total_seconds()
    if ttl>0:
        try:cache.set(key,value,max(1,math.ceil(ttl)))
        except Exception:pass
    return copy.deepcopy(value)
