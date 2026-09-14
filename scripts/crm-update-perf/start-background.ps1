$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path "$PSScriptRoot/../..").Path.Replace('\','/')
docker run -d --name knjsc-crm-update-redis --network knjsc-crm-update-test redis:7-alpine redis-server --save '' --appendonly no | Out-Null
if($LASTEXITCODE -ne 0){throw 'Cannot start isolated Redis; inspect existing container instead of replacing it'}
docker run -d --name knjsc-crm-update-worker --network knjsc-crm-update-test -e RUN_MIGRATIONS=0 -e POSTGRES_HOST=knjsc-crm-update-db -e POSTGRES_DB=test_crm_update_load_300000 -e POSTGRES_USER=knjsc -e POSTGRES_PASSWORD=test -e DJANGO_SETTINGS_MODULE=load_settings -e PYTHONPATH=/harness:/app -e REDIS_URL=redis://knjsc-crm-update-redis:6379/0 -v "${taskRoot}/app:/app:ro" -v "${taskRoot}/scripts/crm-update-perf:/harness:ro" -v "${taskRoot}/storage/crm-update/load300:/runtime" knjsc-web celery -A knjsc worker --concurrency=1 -Q celery --loglevel=WARNING | Out-Null
if($LASTEXITCODE -ne 0){throw 'Cannot start isolated worker'}
