$ErrorActionPreference = 'Stop'

function Test-Url($url) {
    try {
        $r = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 5
        if ($r.StatusCode -ne 200) { throw "Non-200: $($r.StatusCode)" }
        return 0
    }
    catch {
        Write-Host "FAIL: $url - $_" -ForegroundColor Red
        return 1
    }
}

$fail = 0
$fail += Test-Url "http://localhost:8010/health"
$fail += Test-Url "http://localhost:8010/metrics"
$fail += Test-Url "http://localhost:5173"
$fail += Test-Url "http://localhost:3030"

if ($fail -eq 0) { Write-Host "Smoke: PASS" -ForegroundColor Green; exit 0 } else { Write-Host "Smoke: FAIL ($fail)" -ForegroundColor Red; exit 1 }
