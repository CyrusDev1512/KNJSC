import os
from pathlib import Path
assert os.environ['POSTGRES_DB']=='test_knjsc_code_load'
assert os.environ['POSTGRES_HOST']=='knjsc-code-db'
from knjsc.settings.base import *
DEBUG=False
ROOT_URLCONF='knjsc.urls_bangtinh'
ALLOWED_HOSTS=['*']
GRID_ONLY_TABLES=set()
STORAGE_DIR=Path('/runtime/files')
MEDIA_ROOT=STORAGE_DIR/'uploads'
EXPORT_DIR=STORAGE_DIR/'exports'
BACKUP_DIR=STORAGE_DIR/'backups'
EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
CELERY_TASK_ALWAYS_EAGER=False
CELERY_BROKER_URL='redis://knjsc-code-redis:6379/1'
CELERY_RESULT_BACKEND=CELERY_BROKER_URL
MIDDLEWARE=['mixed_metrics.Metrics']+MIDDLEWARE
LOGGING={'version':1,'disable_existing_loggers':False,'handlers':{'null':{'class':'logging.NullHandler'}},'root':{'handlers':['null'],'level':'INFO'}}
