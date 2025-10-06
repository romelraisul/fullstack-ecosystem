$ErrorActionPreference = 'Stop'

function Invoke-JsonPost($url, $body) {
    $json = ($body | ConvertTo-Json -Depth 6)
    $headers = @{ 'X-Orchestrator-Bypass' = '1' }
    return Invoke-RestMethod -Uri $url -Method Post -ContentType 'application/json' -Headers $headers -Body $json
}

$r = Invoke-JsonPost 'http://localhost:8010/orchestrate/full-experiment' @{}
$ok = ($r.ok -eq $r.total -and $r.errors -eq 0)
Write-Host ("ok={0} total={1} errors={2} duration_ms={3}" -f $ok, $r.total, $r.errors, $r.duration_ms)
