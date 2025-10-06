# Fails if strict readiness is not at 100% (with_api_base == total)
param(
    [string]$Url = 'http://localhost:5125/api/systems/integration-summary',
    [int]$TimeoutSeconds = 15
)

$ErrorActionPreference = 'Stop'
$end = (Get-Date).AddSeconds($TimeoutSeconds)

while ((Get-Date) -lt $end) {
    try {
        $res = Invoke-RestMethod -Uri $Url -UseBasicParsing
        $total = [int]$res.total
        $withApi = [int]$res.with_api_base
        if ($total -gt 0 -and $total -eq $withApi) {
            Write-Host "Readiness OK: $withApi / $total"
            exit 0
        }
        else {
            Write-Host "Waiting: with_api_base=$withApi total=$total"; Start-Sleep -Seconds 2
        }
    }
    catch {
        Start-Sleep -Seconds 2
    }
}
Write-Error "Readiness not at 100% within $TimeoutSeconds seconds"
exit 2
