$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path "$PSScriptRoot/../..").Path.Replace('\','/')
$outputPath="$taskRoot/storage/crm-update/load300"
$stem='final-endurance-after-300000-20'
if(Test-Path "$outputPath/stop-endurance"){throw 'Inspect existing stop-endurance evidence before running again'}
if(!(Test-Path "$outputPath/time-normalization.json")){throw 'Normalize synthetic timestamps only after comparisons first'}
if(!(Get-Content -Raw "$taskRoot/storage/crm-update/matrix-gate.json" | ConvertFrom-Json).passed){throw 'Short matrix has not passed'}
$env:LOAD_DIR=$outputPath
$env:LOAD_BROWSER_SECONDS='1865'
$env:NODE_PATH='C:/Users/PC/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules'
$nodePath='C:/Users/PC/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
$processes=@()
$completed=$false
try {
    $browser=Start-Process -FilePath $nodePath -ArgumentList @("$taskRoot/scripts/crm-update-perf/endurance-browser.cjs") -WindowStyle Hidden -PassThru -RedirectStandardOutput "$outputPath/endurance-browser.log" -RedirectStandardError "$outputPath/endurance-browser.stderr.log"
    $processes+=$browser
    $loadArgs=@('run','--rm','--name','knjsc-crm-update-load','--network','knjsc-crm-update-test','--entrypoint','locust',
        '-e','LOAD_STAGE=after','-e','LOAD_EXTENDED=1','-e','LOAD_WARMUP=60','-e','LOAD_SECONDS=1800',
        '-e',"LOAD_RESULT=/runtime/$stem.json",'-v',"${taskRoot}/scripts/crm-update-perf:/harness:ro",'-v',"${outputPath}:/runtime",
        'knjsc-web','-f','/harness/locustfile.py','--headless','-H','http://knjsc-crm-update-before:8000','-u','19','-r','19','-t','1865s','--stop-timeout','15','--only-summary')
    $load=Start-Process -FilePath docker -ArgumentList $loadArgs -WindowStyle Hidden -PassThru -RedirectStandardOutput "$outputPath/$stem.stdout.log" -RedirectStandardError "$outputPath/$stem.log"
    $processes+=$load
    $background=Start-Process -FilePath docker -ArgumentList @('exec','-e','BACKGROUND_ROUNDS=31','knjsc-crm-update-before','python','/harness/background.py') -WindowStyle Hidden -PassThru -RedirectStandardOutput "$outputPath/endurance-background.log" -RedirectStandardError "$outputPath/endurance-background.stderr.log"
    $processes+=$background
    $start=[DateTime]::UtcNow
    while(@($processes | Where-Object {!$_.HasExited}).Count) {
        if(Test-Path "$outputPath/stop-endurance"){throw 'Chrome detected an endurance failure'}
        foreach($process in $processes){if($process.HasExited -and $process.ExitCode -ne 0){throw "Endurance child failed: $($process.Id), exit $($process.ExitCode)"}}
        if(([DateTime]::UtcNow-$start).TotalSeconds -gt 2000){throw 'Endurance exceeded bounded deadline'}
        Start-Sleep -Seconds 5
    }
    foreach($process in $processes){if($process.ExitCode -ne 0){throw "Endurance child failed: $($process.ExitCode)"}}
    $result=Get-Content -Raw "$outputPath/$stem.json" | ConvertFrom-Json
    $chrome=Get-Content -Raw "$outputPath/endurance-browser.json" | ConvertFrom-Json
    if($result.measured -lt 1800 -or $chrome.elapsed -lt 1860 -or $chrome.errors.Count){throw 'Incomplete endurance measurement'}
    docker exec -e "LOAD_RESULT=/runtime/$stem.json" knjsc-crm-update-before python /harness/oracle.py *> "$outputPath/$stem-oracle.log"
    if($LASTEXITCODE -ne 0){throw 'Endurance oracle failed'}
    $completed=$true
} finally {
    if(!$completed) {
        docker kill knjsc-crm-update-load 2>$null | Out-Null
        # Dừng cả chương trình background bên trong docker exec, không chỉ client host.
        docker stop knjsc-crm-update-before knjsc-crm-update-worker 2>$null | Out-Null
        foreach($process in $processes){if(!$process.HasExited){Stop-Process -Id $process.Id}}
    }
    docker logs knjsc-crm-update-before *> "$outputPath/$stem-server.log"
    docker logs knjsc-crm-update-worker *> "$outputPath/endurance-worker.log"
}
