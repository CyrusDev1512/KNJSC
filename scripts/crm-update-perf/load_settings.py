from knjsc.settings.bangtinh import *
ALLOWED_HOSTS=['*']
PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher']
STORAGE_DIR=Path('/runtime/storage')
MEDIA_ROOT=STORAGE_DIR/'uploads'
EXPORT_DIR=STORAGE_DIR/'exports'
BACKUP_DIR=STORAGE_DIR/'backups'
CELERY_TASK_ALWAYS_EAGER=False
CRM_OPT_READ=CRM_OPT_SYNC=CRM_OPT_RECEIPTS=CRM_OPT_RENDER=CRM_OPT_STATS=False
