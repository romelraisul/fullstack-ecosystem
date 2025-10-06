$ErrorActionPreference = 'Stop'

function Invoke-JsonPost($url, $body) {
    $json = ($body | ConvertTo-Json -Depth 6)
    $headers = @{ 'X-Orchestrator-Bypass' = '1' }
    return Invoke-RestMethod -Uri $url -Method Post -ContentType 'application/json' -Headers $headers -Body $json
}

function Get-Throughput() {
    try {
        $u = 'http://localhost:8010/orchestrator/throughput?window_seconds=60'
        $headers = @{ 'X-Orchestrator-Bypass' = '1' }
        return Invoke-RestMethod -Uri $u -Method Get -Headers $headers
    }
    catch {
        return $null
    }
}

$results = @()
for ($i = 1; $i -le 10; $i++) {
    $start = Get-Date
    $r = Invoke-JsonPost 'http://localhost:8010/orchestrate/full-experiment' @{}
    $duration = ((Get-Date) - $start).TotalMilliseconds
    $ok = ($r.ok -eq $r.total -and $r.errors -eq 0)
    $tp = Get-Throughput
    if ($null -ne $tp) {
        $tpm = [Math]::Round($tp.tasks_per_minute, 2)
    }
    else {
        $tpm = $null
    }
    $results += [pscustomobject]@{
        iter = $i; ok = $ok; total = $r.total; errors = $r.errors; duration_ms = [Math]::Round($duration, 2); tasks_per_min = $tpm
    }
    Start-Sleep -Milliseconds 300
}

$results | Format-Table -AutoSize

$allOk = -not ($results | Where-Object { -not $_.ok })
$avgTpm = [Math]::Round((($results | Where-Object { $_.tasks_per_min -ne $null } | Measure-Object -Property tasks_per_min -Average).Average), 2)
$avgMs = [Math]::Round((($results | Measure-Object -Property duration_ms -Average).Average), 2)

Write-Host "\nSummary: all_ok=$allOk  avg_duration_ms=$avgMs  avg_tasks_per_min=$avgTpm"
