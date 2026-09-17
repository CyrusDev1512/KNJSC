import time
from pathlib import Path
import django
django.setup()
from django.db import connection,transaction
from django.utils import timezone
from orders.services.order_service import ORDER_CODE_LOCK_NAMESPACE
assert connection.settings_dict['NAME']=='test_knjsc_code_load' and connection.settings_dict['HOST']=='knjsc-code-db'
r=Path('/runtime'); release=r/'release-lock'; ready=r/'lock-ready'
release.unlink(missing_ok=True);ready.unlink(missing_ok=True)
try:
 with transaction.atomic(),connection.cursor() as c:
  c.execute('SELECT pg_advisory_xact_lock(%s,%s)',[ORDER_CODE_LOCK_NAMESPACE,int(timezone.localdate().strftime('%d%m'))])
  ready.write_text('locked')
  end=time.monotonic()+20
  while not release.exists() and time.monotonic()<end:time.sleep(.05)
finally:ready.unlink(missing_ok=True)
