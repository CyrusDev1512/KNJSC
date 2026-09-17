# Chỉ tạo lại container riêng của bài đo; không restart dịch vụ của người dùng.
$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $taskRoot
$baseline='C:/KNJSC/CRM-Optimization-baseline/app'
foreach($case in @(@('before100',8038,0),@('before300',8040,0),@('after100',8042,1),@('after300',8043,1))){
  $name=$case[0];$port=$case[1];$enabled=$case[2]
  $app=if($enabled){Join-Path $taskRoot 'app'}else{$baseline}
  $runtime=Join-Path $taskRoot ".test-runtime/$name"
  $exists=docker ps -aq --filter "name=^crm-opt-$name$"
  if($exists){docker stop "crm-opt-$name" | Out-Null}
  & docker compose -p knjsc -f deploy/docker-compose.yml run -d --rm --no-deps --name "crm-opt-$name" -p "${port}:8000" -v "${app}:/app:ro" -v "${taskRoot}/app/tests/perf:/harness:ro" -v "${taskRoot}/app/core/request_metrics.py:/instrument/request_metrics.py:ro" -v "${runtime}:/runtime" -e OPT_INSTRUMENT=1 -e RUN_MIGRATIONS=0 -e "POSTGRES_DB=test_knjsc_opt_$name" -e CRM_CACHE_URL=redis://crm-opt-cache:6379/0 -e "CRM_OPT_READ=$enabled" -e "CRM_OPT_SYNC=$enabled" -e "CRM_OPT_RECEIPTS=$enabled" -e "CRM_OPT_RENDER=$enabled" -e "CRM_OPT_STATS=$enabled" -e "CRM_OPT_EXPORT=$enabled" -e "CRM_OPT_QUEUES=$enabled" web gunicorn optimization_wsgi:application --pythonpath /harness --bind 0.0.0.0:8000 --workers 3 --threads 4 --worker-class gthread --keep-alive 5
  if($LASTEXITCODE){throw "Không khởi động được $name"}
  # Worker chỉ đọc image snapshot tương ứng, broker phân DB, file ở runtime riêng.
  $worker="crm-opt-worker-$name"
  $exists=docker ps -aq --filter "name=^$worker$"
  if($exists){docker stop $worker | Out-Null}
  & docker compose -p knjsc -f deploy/docker-compose.yml run -d --rm --no-deps --name $worker -v "${app}:/app:ro" -v "${taskRoot}/app/tests/perf:/harness:ro" -v "${runtime}:/runtime" -e PYTHONPATH=/app:/harness -e DJANGO_SETTINGS_MODULE=optimization_settings -e RUN_MIGRATIONS=0 -e "POSTGRES_DB=test_knjsc_opt_$name" -e "CRM_OPT_EXPORT=$enabled" -e "CRM_OPT_QUEUES=$enabled" web celery -A knjsc worker -l info --concurrency 1 --prefetch-multiplier 1 -Q celery,crm_heavy
  if($LASTEXITCODE){throw "Không khởi động worker $name"}
}
