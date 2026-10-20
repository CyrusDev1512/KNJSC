"""Gunicorn kiểm tải local: phục vụ static từ cùng snapshot, chặn DB ngoài môi trường riêng."""
import os
if os.environ.get('POSTGRES_DB') != 'knjsc_loadtest' or os.environ.get('KNJSC_PERF_ISOLATED') != '1':
    raise RuntimeError('WSGI kiểm tải chỉ dùng với compose.loadtest.yml.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE','knjsc.settings.dev')
from django.conf import settings
settings.ROOT_URLCONF='knjsc.urls_bangtinh'
settings.GRID_ONLY_TABLES=set()
settings.DEBUG=False
from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler
application=StaticFilesHandler(get_wsgi_application())
