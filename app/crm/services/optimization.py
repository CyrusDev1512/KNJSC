"""Cache có phiên bản và token gắn quyền; Redis hỏng luôn đọc lại DB."""
import hashlib
import json
from django.conf import settings
from django.core import signing
from django.core.cache import caches
from django.db import connection
from django.db.models import Q
from core.exceptions import BusinessError, OutOfScopeError
from forms_builder.models import DataRecord
from crm.models import GridRevision, GridChange

TRANSPORT={'protocol','offset','version','query_token','cursor','metadata_version','trang','moi_trang'}


def enabled(name):
    return getattr(settings,'CRM_OPT_'+name,False)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,default=str,ensure_ascii=False).encode()).hexdigest()


def cached(key, build, seconds=300):
    try:
        cache=caches['crm'];value=cache.get(key)
        if value is not None:return value
    except Exception:
        return build()
    value=build()
    try:cache.set(key,value,seconds)
    except Exception:pass
    return value


def state(table):
    return GridRevision.objects.filter(table_id=table.pk).values('revision','fields').first() or {'revision':0,'fields':{}}


def params_only(params):
    return sorted((k,params.getlist(k)) for k in params if k not in TRANSPORT)


def dependencies(grid, params):
    keys={'__membership','__schema','__access'}
    for key in params:
        if key.startswith('f_'):keys.add(key[2:].split('__')[0])
    if params.get('sp') or any(k.startswith('f_san_pham') for k in params):keys.add('__items')
    if params.get('sap'):keys.add(params['sap'])
    if params.get('tim') or params.get('trung'):
        keys.update(c.code for c in grid.columns if c.meaning)
    return keys


def scope_key(user):
    p=getattr(user,'profile',None)
    return [user.pk,user.is_active,user.is_superuser,*(getattr(p,k,None) for k in ('rank','department_id','team_id','session_epoch'))]


def authority(user,table):
    from django.contrib.auth import get_user_model
    from forms_builder.models import TableDef
    user=get_user_model().objects.select_related('profile').filter(pk=user.pk,is_active=True).first()
    if user is None or not TableDef.objects.in_scope(user).filter(pk=table.pk).exists():raise OutOfScopeError()
    return user


def query_identity(user,table,grid,params,current):
    versions={k:current['fields'].get(k,0) for k in dependencies(grid,params)}
    return digest([connection.settings_dict['NAME'],scope_key(user),table.pk,params_only(params),versions])


def token(value):return signing.Signer(salt='crm-grid-v2').sign_object(value,compress=True)


def untoken(value):
    try:return signing.Signer(salt='crm-grid-v2').unsign_object(value)
    except (signing.BadSignature,ValueError,TypeError):raise BusinessError('Phiên truy vấn không hợp lệ.',code='conflict')


def block(user,table,params):
    from . import master_grid_service as master, grid_service
    user=authority(user,table)
    current=state(table);grid=grid_service.build_grid(user,params,table=table)
    for column in grid.columns:column.table=table
    identity=query_identity(user,table,grid,params,current);query_token=token({'q':identity})
    if params.get('query_token') and untoken(params['query_token'])!={'q':identity}:
        raise BusinessError('Kết quả lọc đã thay đổi; đang cập nhật vùng nhìn.',code='conflict')
    try:
        offset=int(params.get('offset',0))
        if not 0<=offset<=2**31-1:raise ValueError
    except (ValueError,TypeError):raise BusinessError('Vị trí dữ liệu không hợp lệ.')
    qs=grid.queryset;ordering=list(qs.query.order_by) or ['created_at','pk']
    if 'pk' not in ordering and 'id' not in ordering:ordering.append('pk')
    qs=qs.order_by(*ordering)
    total=cached('grid-total:'+identity,qs.count)
    simple=not params.get('sap') and ordering in (['created_at','pk'],['created_at','id'])
    candidate=qs.select_related(None)
    backwards=False
    if params.get('cursor'):
        c=untoken(params['cursor'])
        if not isinstance(c,dict) or not simple or c.get('q')!=identity or c.get('offset')!=offset:raise BusinessError('Con trỏ đã hết hiệu lực.',code='conflict')
        from django.utils.dateparse import parse_datetime
        dt=parse_datetime(c.get('time',''));pk=c.get('id');backwards=c.get('back',False)
        if not dt or type(pk) is not int:raise BusinessError('Con trỏ không hợp lệ.')
        candidate=candidate.filter(Q(created_at__lt=dt)|Q(created_at=dt,pk__lt=pk)) if backwards else candidate.filter(Q(created_at__gt=dt)|Q(created_at=dt,pk__gt=pk))
        if backwards:candidate=candidate.order_by('-created_at','-pk')
        selected=list(candidate.values_list('pk','created_at')[:master.BLOCK_SIZE])
        if backwards:selected.reverse()
    else:selected=list(candidate.values_list('pk','created_at')[offset:offset+master.BLOCK_SIZE])
    ids=[pk for pk,_ in selected];by_id={r.pk:r for r in qs.filter(pk__in=ids).order_by()}
    rows=[by_id[pk] for pk in ids if pk in by_id]
    mv=digest([table.pk,current['fields'].get('__schema',0)])
    result={'protocol':2,'rows':master.serialize(rows,grid.columns,user),'total':total,'version':identity,'query_token':query_token,'revision':current['revision'],'offset':offset,'block_size':master.BLOCK_SIZE,'metadata_version':mv}
    if params.get('metadata_version')!=mv:result['columns']=master.metadata(grid.columns)
    if selected and simple:
        def cursor(item,next_offset,back):return token({'q':identity,'id':item[0],'time':item[1].isoformat(),'offset':next_offset,'back':back})
        if offset+len(selected)<total:result['next_cursor']=cursor(selected[-1],offset+len(selected),False)
        if offset>=master.BLOCK_SIZE:result['previous_cursor']=cursor(selected[0],offset-master.BLOCK_SIZE,True)
    return result


def sync(user,table,payload):
    from django.http import QueryDict
    from . import grid_service,master_grid_service as master
    user=authority(user,table)
    ids=payload.get('ids');visible_ids=payload.get('visible',[])
    if not isinstance(ids,list) or len(ids)>4000 or any(type(i)is not int or i<1 for i in ids):raise BusinessError('Danh sách dòng không hợp lệ.')
    if not isinstance(visible_ids,list) or len(visible_ids)>100 or any(i not in ids for i in visible_ids):raise BusinessError('Vùng nhìn không hợp lệ.')
    current=state(table);params=QueryDict(payload.get('query',''))
    grid=grid_service.build_grid(user,params,table=table)
    for c in grid.columns:c.table=table
    identity=query_identity(user,table,grid,params,current)
    allowed=set(DataRecord.objects.in_scope(user,table=table).filter(pk__in=ids).values_list('pk',flat=True))
    result={'revision':current['revision'],'removed':sorted(set(ids)-allowed),'rows':[],'invalidate':[],'reset':False}
    try:since=int(payload.get('revision',-1))
    except (TypeError,ValueError):raise BusinessError('Phiên bản không hợp lệ.')
    if since<max(0,current['revision']-10000) or since>current['revision'] or untoken(payload.get('query_token'))!={'q':identity}:
        result['reset']=True;return result
    changed=set()
    for event in GridChange.objects.filter(table=table,revision__gt=since).order_by('revision').iterator(chunk_size=100):
        if event.reset:result['reset']=True;return result
        changed.update(allowed.intersection(event.record_ids))
    refresh=changed & allowed & set(visible_ids)
    result['rows']=master.serialize(grid.queryset.filter(pk__in=refresh),grid.columns,user)
    result['invalidate']=sorted((changed & allowed)-set(visible_ids))
    return result
