$ErrorActionPreference = 'Stop'

# 60-minute paced soak test
# - Calls /orchestrate/full-experiment every 5 seconds
# - Tracks totals, errors, p95 duration estimate, and tasks/min snapshots
# - Writes a concise summary at the end

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
    catch { return $null }
}

$durations = New-Object System.Collections.Generic.List[Double]
$errors = 0
$totalCalls = 0
$okCalls = 0
$startWall = Get-Date

while ((Get-Date) - $startWall -lt [TimeSpan]::FromMinutes(60)) {
    $callStart = Get-Date
    try {
        $r = Invoke-JsonPost 'http://localhost:8010/orchestrate/full-experiment' @{}
        $ok = ($r.ok -eq $r.total -and $r.errors -eq 0)
        if ($ok) { $okCalls++ } else { $errors++ }
        $totalCalls++
        $durations.Add([double]$r.duration_ms)
        $t = Get-Throughput
        if ($null -ne $t) {
            $tpm = [Math]::Round($t.tasks_per_minute, 2)
        }
        else {
            $tpm = 'n/a'
        }
        Write-Host ("[{0}] ok={1}/{2} dur={3}ms tpm={4}" -f (Get-Date).ToString('HH:mm:ss'), $r.ok, $r.total, $r.duration_ms, $tpm)
    }
    catch {
        $errors++
        $totalCalls++
        Write-Host ("[{0}] ERROR invoking full-experiment: {1}" -f (Get-Date).ToString('HH:mm:ss'), $_.Exception.Message)
    }
    $elapsed = ((Get-Date) - $callStart).TotalMilliseconds
    $sleepMs = [Math]::Max(0, 5000 - [int]$elapsed)
    Start-Sleep -Milliseconds $sleepMs
}

# Compute p95 of durations
$sorted = $durations | Sort-Object
if ($sorted.Count -gt 0) {
    $idx = [int][Math]::Ceiling($sorted.Count * 0.95) - 1
    if ($idx -lt 0) { $idx = 0 }
    $p95 = [Math]::Round($sorted[$idx], 2)
}
else {
    $p95 = $null
}

$wall = ((Get-Date) - $startWall).TotalMinutes
$summary = [pscustomobject]@{
    minutes         = [Math]::Round($wall, 1)
    calls           = $totalCalls
    ok_calls        = $okCalls
    errors          = $errors
    error_rate_pct  = if ($totalCalls -gt 0) { [Math]::Round(($errors / $totalCalls) * 100, 2) } else { 0 }
    p95_duration_ms = $p95
}

"`nSOAK SUMMARY"
$summary | Format-List
