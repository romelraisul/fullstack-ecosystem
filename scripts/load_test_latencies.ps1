<#!
.SYNOPSIS
  Lightweight latency load test for /health and /ml-capabilities endpoints.
.DESCRIPTION
  Runs burst + steady phases, measuring latency and basic statistics.
.PARAMETER DurationSeconds
  Total duration of steady phase (default 15).
.PARAMETER Concurrency
  Parallel workers during steady phase (default 8).
#>
param(
    [int]$DurationSeconds = 15,
    [int]$Concurrency = 8,
    [string]$BaseUrl = 'http://127.0.0.1:8000'
)

$ErrorActionPreference = 'Stop'

function Invoke-TimedRequest {
    param([string]$Url)
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try { Invoke-RestMethod -Uri $Url -TimeoutSec 10 -UseBasicParsing | Out-Null; $ok = $true }
    catch { $ok = $false }
    $sw.Stop()
    return [PSCustomObject]@{ url = $Url; ms = $sw.Elapsed.TotalMilliseconds; ok = $ok }
}

$results = New-Object System.Collections.Concurrent.ConcurrentBag[object]

Write-Host '[load-test] Burst warmup (20 sequential requests)' -ForegroundColor Cyan
for ($i = 0; $i -lt 20; $i++) {
    $r = Invoke-TimedRequest -Url ("$BaseUrl/health")
    $results.Add($r)
}

Write-Host "[load-test] Steady phase $Concurrency workers for $DurationSeconds s" -ForegroundColor Cyan
$end = [DateTime]::UtcNow.AddSeconds($DurationSeconds)
$jobs = @()
for ($w = 0; $w -lt $Concurrency; $w++) {
    $jobs += Start-Job -ScriptBlock {
        param($BaseUrl, $End, $Shared)
        while ([DateTime]::UtcNow -lt $End) {
            foreach ($path in @('/health', '/ml-capabilities')) {
                $sw = [System.Diagnostics.Stopwatch]::StartNew(); $ok = $true
                try { Invoke-RestMethod -Uri ($BaseUrl + $path) -TimeoutSec 5 -UseBasicParsing | Out-Null } catch { $ok = $false }
                $sw.Stop()
                $Shared.Add([PSCustomObject]@{ url = ($BaseUrl + $path); ms = $sw.Elapsed.TotalMilliseconds; ok = $ok })
            }
        }
    } -ArgumentList $BaseUrl, $end, $results
}

Wait-Job -Job $jobs | Out-Null
Receive-Job -Job $jobs | Out-Null
Remove-Job -Job $jobs

$groups = $results | Group-Object url
$summary = @()
foreach ($g in $groups) {
    $lat = $g.Group.ms
    $okCount = ($g.Group | Where-Object { $_.ok }).Count
    $p = [math]::Round(($okCount / $g.Count) * 100, 2)
    $sorted = $lat | Sort-Object
    function quant { param($arr, $q) if ($arr.Count -eq 0) { return 0 } $pos = ($q * ($arr.Count - 1)); $lo = [int][math]::Floor($pos); $hi = [int][math]::Ceiling($pos); if ($lo -eq $hi) { return [math]::Round($arr[$lo], 2) } $frac = $pos - $lo; return [math]::Round($arr[$lo] + ($arr[$hi] - $arr[$lo]) * $frac, 2) }
    $summary += [PSCustomObject]@{
        url         = $g.Name
        count       = $g.Count
        success_pct = $p
        p50_ms      = quant $sorted 0.50
        p90_ms      = quant $sorted 0.90
        p95_ms      = quant $sorted 0.95
        p99_ms      = quant $sorted 0.99
        max_ms      = [math]::Round(($sorted[-1]), 2)
    }
}

Write-Host "[load-test] Summary:" -ForegroundColor Green
$summary | Sort-Object url | Format-Table -AutoSize

# Emit machine-readable JSON
($summary | ConvertTo-Json -Depth 4) | Out-File 'load_test_summary.json' -Encoding utf8
Write-Host '[load-test] JSON summary written to load_test_summary.json'
