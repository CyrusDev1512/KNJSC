import json
from pathlib import Path
import django
django.setup()
from django.conf import settings
from django.core.checks import run_checks
from django.urls import clear_url_caches
from django.db import connection
assert connection.settings_dict['NAME']=='test_knjsc_code_load' and connection.settings_dict['HOST']=='knjsc-code-db'
results={}
for conf in ['knjsc.urls','knjsc.urls_bangtinh']:
 settings.ROOT_URLCONF=conf;clear_url_caches();results[conf]=[str(e) for e in run_checks()]
Path('/runtime/results/startup.json').write_text(json.dumps(results));print(json.dumps(results));assert not any(results.values())
