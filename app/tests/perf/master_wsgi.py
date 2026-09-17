"""WSGI chỉ cho phép DB test; dùng chung runtime trước/sau trong phép đo AC-21."""
import os
assert os.environ.get('POSTGRES_DB', '').startswith('test_knjsc_master_capacity')
os.environ['DJANGO_SETTINGS_MODULE'] = 'knjsc.settings.test'
from django.conf import settings
settings.ROOT_URLCONF = 'knjsc.urls_bangtinh'
settings.GRID_ONLY_TABLES = set()
settings.DEBUG = False
settings.ALLOWED_HOSTS = ['*']
# Docker db hiện có /dev/shm 64MB. Giới hạn trong kết nối DB test của cả hai
# snapshot; không ALTER SYSTEM hoặc khởi động lại PostgreSQL đang dùng.
settings.DATABASES['default'].setdefault('OPTIONS', {})['options'] = '-c max_parallel_workers_per_gather=0'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
# Tệp tĩnh dùng mã của từng snapshot; HTTP API vẫn đi đúng gunicorn gthread.
from django.contrib.staticfiles.handlers import StaticFilesHandler
application = StaticFilesHandler(application)
