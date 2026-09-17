param(
  [ValidateSet('before','after')][string]$Stage='before',
  [ValidateSet(100000,300000)][int]$Rows=100000,
  [ValidateSet(10,20)][int]$Users=10,
  [ValidateRange(10,1860)][int]$Duration=360,
  [ValidateRange(0,60)][int]$Warmup=60,
  [ValidateSet(1,2)][int]$Protocol=1,
  [string]$Server='crm-opt-diagnostic',
  [int]$Port=8000,
  [switch]$Mixed,
  [switch]$Endurance,
  [ValidateRange(10,120)][int]$BulkInterval=120,
  [string]$Label=''
)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $taskRoot
$runtime=Join-Path $taskRoot ('.test-runtime/'+$Stage+($Rows/1000))
$evidence=Join-Path $taskRoot '.agents/design-state/review/optimization'
if(-not $Label){$Label="$Stage-$Rows-$Users-p$Protocol"}
if($Label -notmatch '^[a-zA-Z0-9_-]+$' -or $Server -notmatch '^crm-opt-[a-zA-Z0-9-]+$'){throw 'Sai tên evidence/server test'}
$manifest=Get-Content -Raw -LiteralPath (Join-Path $runtime 'ready.json') | ConvertFrom-Json
if($manifest.database -notlike 'test_knjsc_opt_*' -or $manifest.rows -ne $Rows){throw 'Không đúng fixture test'}
$application="crm-opt-$Stage$($Rows/1000)"
$sample=Start-Job -ArgumentList $evidence,$Label,$Server,$application -ScriptBlock {
  param($evidence,$label,$server,$application)
  while($true){
    $stamp=[DateTime]::UtcNow.ToString('o')
    $resources=docker stats --no-stream --format '{{json .}}' $server $application knjsc-db-1 crm-opt-broker crm-opt-cache crm-opt-load ($application.Replace('crm-opt-','crm-opt-worker-'))
    [ordered]@{time=$stamp;containers=@($resources | ForEach-Object {$_ | ConvertFrom-Json})} | ConvertTo-Json -Depth 5 -Compress | Add-Content -LiteralPath (Join-Path $evidence "$label-resources.jsonl")
    Start-Sleep -Seconds 5
  }
}
try{
  $scenario=if($Endurance){'tests/perf/locust_optimization_endurance.py'}else{'tests/perf/locust_optimization.py'}
  & docker compose -p knjsc -f deploy/docker-compose.yml run --rm --no-deps --name crm-opt-load -v "${runtime}:/runtime:ro" -v "${evidence}:/evidence" -e RUN_MIGRATIONS=0 -e OPT_MANIFEST=/runtime/ready.json -e "OPT_RESULT=/evidence/$Label.json" -e "OPT_WARMUP=$Warmup" -e "OPT_PROTOCOL=$Protocol" -e "OPT_BULK_INTERVAL=$BulkInterval" -e "OPT_MIXED=$([int]$Mixed.IsPresent)" web locust -f $scenario --headless --host "http://${Server}:$Port" --users $Users --spawn-rate 20 --run-time "${Duration}s" --only-summary *> (Join-Path $evidence "$Label.log")
  $result=$LASTEXITCODE
}finally{
  Stop-Job $sample
  Receive-Job $sample -ErrorAction Continue
  Remove-Job $sample
  docker logs $application *> (Join-Path $evidence "$Label-server.log")
  if($Server -eq 'crm-opt-proxy'){docker exec crm-opt-proxy cat /var/log/nginx/optimization.log *> (Join-Path $evidence "$Label-proxy.log")}
}
Write-Output "$Label kết thúc, exit=$result"
exit $result
