import django,runpy
django.setup()
from django.core.management import call_command
from django.db import connection
assert connection.settings_dict['NAME']=='test_knjsc_code_load' and connection.settings_dict['HOST']=='knjsc-code-db'
call_command('migrate',interactive=False,verbosity=0)

runpy.run_path('/harness/seed.py',run_name='__main__')
