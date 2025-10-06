# Quick benchmark for orchestrate/quantum at different shot counts
$ErrorActionPreference = 'Stop'
$base = 'http://localhost:5125'
$shotsList = @(64, 128, 512, 2048)

$results = @()
foreach ($shots in $shotsList) {
    Write-Host "POST /api/orchestrate/quantum shots=$shots" -ForegroundColor Cyan
    $t0 = Get-Date
    $resp = Invoke-RestMethod -Method Post -Uri "$base/api/orchestrate/quantum" -Body (@{shots = $shots } | ConvertTo-Json) -ContentType 'application/json' -UseBasicParsing
    $t1 = Get-Date
    $ms = [math]::Round(($t1 - $t0).TotalMilliseconds, 2)
    $topStr = ''
    if ($resp.result.top_counts) {
        $pairs = @()
        foreach ($p in $resp.result.top_counts) { if ($p.Length -ge 2) { $pairs += ("{0} {1}" -f $p[0], $p[1]) } }
        $topStr = ($pairs -join ', ')
    }
    $results += [PSCustomObject]@{ shots = $shots; duration_ms = $resp.duration_ms; wall_ms = $ms; top = $topStr }
}

$results | Format-Table -AutoSize

# Optional: write CSV
$csv = Join-Path $PSScriptRoot "quantum_bench_$(Get-Date -Format 'yyyyMMdd_HHmmss').csv"
$results | Export-Csv -NoTypeInformation -Path $csv
Write-Host "Saved: $csv" -ForegroundColor Green
