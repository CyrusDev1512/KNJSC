param([int]$Minutes=80)
# Chỉ đọc chỉ số container của phép đo và PostgreSQL dùng chung; không đổi cấu hình.
$metricsPath=Join-Path $PSScriptRoot '../.agents/design-state/review/master-nine-capacity/resources-final.jsonl'
$monitorEnd=(Get-Date).AddMinutes($Minutes)
while((Get-Date) -lt $monitorEnd){
    $sample=docker stats --no-stream --format '{{json .}}' knjsc-nine-capacity knjsc-db-1 2>$null
    [pscustomobject]@{at=(Get-Date).ToString('o');containers=@($sample | ForEach-Object {$_ | ConvertFrom-Json})} |
        ConvertTo-Json -Compress -Depth 5 | Add-Content -LiteralPath $metricsPath -Encoding utf8
    Start-Sleep -Seconds 30
}
