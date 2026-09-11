"""Runtime chung, chỉ DB test; mã ứng dụng lấy từ từng snapshot."""
import os
assert os.environ.get('POSTGRES_DB', '').startswith('test_knjsc_opt_')
os.environ['DJANGO_SETTINGS_MODULE'] = 'optimization_settings'
from django.conf import settings
settings.ROOT_URLCONF = 'knjsc.urls_bangtinh'
settings.GRID_ONLY_TABLES = set()
settings.DEBUG = False
settings.ALLOWED_HOSTS = ['*']
settings.DATABASES['default'].setdefault('OPTIONS', {})['options'] = '-c max_parallel_workers_per_gather=0'
from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler
application = StaticFilesHandler(get_wsgi_application())
if os.environ.get('OPT_INSTRUMENT')=='1':
    import importlib.util
    import sys
    settings.CRM_REQUEST_METRICS=False
    spec=importlib.util.spec_from_file_location('optimization_metrics','/instrument/request_metrics.py')
    module=importlib.util.module_from_spec(spec);sys.modules['optimization_metrics']=module;spec.loader.exec_module(module)
    # Même wrapper sur les deux snapshots, sans changer les sources baseline.
    settings.MIDDLEWARE=[m for m in settings.MIDDLEWARE if m!='core.request_metrics.RequestMetricsMiddleware']
    settings.MIDDLEWARE.insert(0,'optimization_metrics.RequestMetricsMiddleware')
    settings.CRM_REQUEST_METRICS=True
    application=StaticFilesHandler(get_wsgi_application())
