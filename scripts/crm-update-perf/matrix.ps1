param([ValidateSet('before','after')][string]$Stage='before')
$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path "$PSScriptRoot/../..").Path.Replace('\','/')
if(Test-Path "$taskRoot/storage/crm-update/pause-matrix"){throw 'Matrix paused for regression review'}
$applicationPath=if($Stage -eq 'before'){"$taskRoot/storage/crm-update/baseline/app"}else{"$taskRoot/app"}
foreach($rowCount in @(100000,300000)) {
    $outputPath="$taskRoot/storage/crm-update/"+$(if($rowCount -eq 100000){'load100'}else{'load300'})
    $dbName="test_crm_update_load_$rowCount"
    docker rm -f knjsc-crm-update-before 2>$null | Out-Null
    docker run -d --name knjsc-crm-update-before --network knjsc-crm-update-test -p 127.0.0.1:8853:8000 -e RUN_MIGRATIONS=0 -e CRM_REQUEST_METRICS=1 -e POSTGRES_HOST=knjsc-crm-update-db -e "POSTGRES_DB=$dbName" -e POSTGRES_USER=knjsc -e POSTGRES_PASSWORD=test -e DJANGO_SETTINGS_MODULE=load_settings -e PYTHONPATH=/harness:/app -v "${applicationPath}:/app:ro" -v "${taskRoot}/scripts/crm-update-perf:/harness:ro" -v "${outputPath}:/runtime" knjsc-web gunicorn knjsc.wsgi:application --bind 0.0.0.0:8000 --workers 3 --threads 4 --timeout 60 --keep-alive 5 | Out-Null
    if($LASTEXITCODE -ne 0){throw 'Cannot start isolated app'}
    foreach($loadUsers in @(10,20)) {
        $stem="final-$Stage-$rowCount-$loadUsers"
        @{stage=$Stage;rows=$rowCount;users=$loadUsers;started=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content "$taskRoot/storage/crm-update/phase.json" -Encoding utf8
        Get-Content -Raw "$taskRoot/storage/crm-update/phase.json" | ConvertFrom-Json | ConvertTo-Json -Compress | Add-Content "$taskRoot/storage/crm-update/phases.jsonl" -Encoding utf8
        docker run --rm --name knjsc-crm-update-load --network knjsc-crm-update-test --entrypoint locust -e "LOAD_STAGE=$Stage" -e LOAD_WARMUP=60 -e LOAD_SECONDS=300 -e "LOAD_RESULT=/runtime/$stem.json" -v "${taskRoot}/scripts/crm-update-perf:/harness:ro" -v "${outputPath}:/runtime" knjsc-web -f /harness/locustfile.py --headless -H http://knjsc-crm-update-before:8000 -u $loadUsers -r $loadUsers -t 365s --stop-timeout 15 --only-summary *> "$outputPath/$stem.log"
        $testExit=$LASTEXITCODE
        docker logs knjsc-crm-update-before *> "$outputPath/$stem-server.log"
        if($testExit -ne 0){throw "Load failed: $stem"}
        if($Stage -eq 'after') {
            docker exec -e "LOAD_RESULT=/runtime/$stem.json" knjsc-crm-update-before python /harness/oracle.py *> "$outputPath/$stem-oracle.log"
            if($LASTEXITCODE -ne 0){throw "Oracle failed: $stem"}
        }
    }
}
