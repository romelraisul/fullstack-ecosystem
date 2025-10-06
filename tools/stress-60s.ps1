$ErrorActionPreference = 'Stop'

function Invoke-JsonPost($url, $body) {
    $json = ($body | ConvertTo-Json -Depth 6)
    $headers = @{ 'X-Orchestrator-Bypass' = '1' }
    return Invoke-RestMethod -Uri $url -Method Post -ContentType 'application/json' -Headers $headers -Body $json
}

$end = (Get-Date).AddSeconds(60)
$ok = 0
$err = 0
$iters = 0

while ((Get-Date) -lt $end) {
    try {
        $res = Invoke-JsonPost 'http://localhost:8010/orchestrate/full-experiment' @{}
        if ($res.errors -eq 0 -and $res.ok -eq $res.total) { $ok++ } else { $err++ }
    }
    catch { $err++ }
    $iters++
}

$tp = Invoke-RestMethod -Uri 'http://localhost:8010/orchestrator/throughput?window_seconds=60' -Method Get -Headers @{ 'X-Orchestrator-Bypass' = '1' }

[pscustomobject]@{
    duration_s       = 60
    iterations       = $iters
    iterations_ok    = $ok
    iterations_error = $err
    tasks_per_minute = $tp.tasks_per_minute
} | Format-List
