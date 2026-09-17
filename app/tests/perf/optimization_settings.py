"""Các worker kiểm tải dùng DB/broker/file riêng; không nhận việc của máy đang dùng."""
import os
from pathlib import Path
assert os.environ.get('POSTGRES_DB','').startswith('test_knjsc_opt_')
from knjsc.settings.test import *
ROOT_URLCONF='knjsc.urls_bangtinh'
GRID_ONLY_TABLES=set()
DEBUG=False
ALLOWED_HOSTS=['*']
CELERY_TASK_ALWAYS_EAGER=False
CELERY_BROKER_URL='redis://crm-opt-broker:6379/'+str({'test_knjsc_opt_before100':0,'test_knjsc_opt_before300':1,'test_knjsc_opt_after100':2,'test_knjsc_opt_after300':3}[os.environ['POSTGRES_DB']])
CELERY_RESULT_BACKEND=CELERY_BROKER_URL
STORAGE_DIR=Path('/runtime/storage')
MEDIA_ROOT=STORAGE_DIR/'uploads'
EXPORT_DIR=STORAGE_DIR/'exports'
BACKUP_DIR=STORAGE_DIR/'backups'
DATABASES['default'].setdefault('OPTIONS',{})['options']='-c max_parallel_workers_per_gather=0'
