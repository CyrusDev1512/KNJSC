param([ValidateSet(100000,300000)][int]$Rows=300000,[switch]$Browser,[switch]$Background,
    [ValidateSet('before','after')][string]$Stage='after')
$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path "$PSScriptRoot/../..").Path.Replace('\','/')
$outputPath="$taskRoot/storage/crm-update/"+$(if($Rows -eq 100000){'load100'}else{'load300'})
$application=if($Browser){'browser_wsgi:application'}else{'knjsc.wsgi:application'}
$applicationPath=if($Stage -eq 'before'){"$taskRoot/storage/crm-update/baseline/app"}else{"$taskRoot/app"}
docker rm -f knjsc-crm-update-before 2>$null | Out-Null
$argsApp=@('run','-d','--name','knjsc-crm-update-before','--network','knjsc-crm-update-test','-p','127.0.0.1:8853:8000',
    '-e','RUN_MIGRATIONS=0','-e','CRM_REQUEST_METRICS=1','-e','POSTGRES_HOST=knjsc-crm-update-db',
    '-e',"POSTGRES_DB=test_crm_update_load_$Rows",'-e','POSTGRES_USER=knjsc','-e','POSTGRES_PASSWORD=test',
    '-e','DJANGO_SETTINGS_MODULE=load_settings','-e','PYTHONPATH=/harness:/app',
    '-v',"${applicationPath}:/app:ro",'-v',"${taskRoot}/scripts/crm-update-perf:/harness:ro",'-v',"${outputPath}:/runtime")
if($Background){$argsApp+=@('-e','REDIS_URL=redis://knjsc-crm-update-redis:6379/0')}
$argsApp+=@('knjsc-web','gunicorn',$application,'--bind','0.0.0.0:8000','--workers','3','--threads','4','--timeout','60','--keep-alive','5')
docker @argsApp | Out-Null
if($LASTEXITCODE -ne 0){throw 'Cannot start isolated application'}
$ready=$false
for($attempt=0;$attempt -lt 15;$attempt++) {
    try{$response=Invoke-WebRequest 'http://127.0.0.1:8853/dang-nhap/' -TimeoutSec 2;if($response.StatusCode -eq 200){$ready=$true;break}}catch{}
    Start-Sleep -Seconds 1
}
if(!$ready){throw 'Isolated application did not become ready'}
