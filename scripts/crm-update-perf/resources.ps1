param([int]$Minutes=120)
$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path "$PSScriptRoot/../..").Path
$deadline=[DateTime]::UtcNow.AddMinutes($Minutes)
$outputPath=Join-Path $taskRoot 'storage/crm-update/resources-continued.jsonl'
# Bộ lấy mẫu đầu kết thúc lúc 10:20 UTC; tránh trùng mẫu trong khoảng chuyển tiếp.
while([DateTime]::UtcNow -lt [DateTime]'2026-09-12T10:21:00Z'){Start-Sleep -Seconds 5}
while([DateTime]::UtcNow -lt $deadline -and !(Test-Path "$taskRoot/storage/crm-update/stop-resources")) {
    $names=@(docker ps --filter name=knjsc-crm-update --format '{{.Names}}' | Where-Object {$_ -in @('knjsc-crm-update-before','knjsc-crm-update-db','knjsc-crm-update-worker','knjsc-crm-update-redis')})
    if($names.Count) {
        $samples=@(docker stats --no-stream --format '{{json .}}' @names | ForEach-Object {$_ | ConvertFrom-Json})
        @{time=[DateTime]::UtcNow.ToString('o');stats=$samples} | ConvertTo-Json -Depth 4 -Compress | Add-Content -LiteralPath $outputPath -Encoding utf8
    }
    Start-Sleep -Seconds 5
}
