<#!
.SYNOPSIS
  Basic smoke test & failure replay harness.
.DESCRIPTION
  Sends a curated list of representative requests to core endpoints and records any non-2xx
  responses. Produces smoke_failures.json and human-readable summary.
#>
param(
  [string]$BaseUrl = 'http://127.0.0.1:8000'
)

$ErrorActionPreference = 'Stop'

$targets = @(
  @{ method = 'GET'; path = '/health' },
  @{ method = 'GET'; path = '/ml-capabilities' },
  @{ method = 'GET'; path = '/__phase' },
  @{ method = 'GET'; path = '/startup/heartbeat' },
  @{ method = 'POST'; path = '/admin/adaptive/reset' },
  @{ method = 'GET'; path = '/api/v2/latency/quantiles' },
  @{ method = 'GET'; path = '/api/v2/latency/distribution' }
)

$failures = @()

function Invoke-Target {
  param($t)
  $uri = $BaseUrl + $t.path
  try {
    if ($t.method -eq 'GET') {
      $resp = Invoke-WebRequest -Uri $uri -Method GET -TimeoutSec 10 -UseBasicParsing
    } elseif ($t.method -eq 'POST') {
      $resp = Invoke-WebRequest -Uri $uri -Method POST -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
    }
    if ($resp.StatusCode -ge 400) {
      $failures += [PSCustomObject]@{ path=$t.path; method=$t.method; status=$resp.StatusCode; body=$resp.Content }
    }
  } catch {
    $errStatus = if ($_.Exception.Response) { $_.Exception.Response.StatusCode.value__ } else { -1 }
    $failures += [PSCustomObject]@{ path=$t.path; method=$t.method; status=$errStatus; body=$_.Exception.Message }
  }
}

Write-Host '[smoke] Executing requests...' -ForegroundColor Cyan
foreach ($t in $targets) { Invoke-Target $t }

if ($failures.Count -eq 0) {
  Write-Host '[smoke] All requests succeeded.' -ForegroundColor Green
} else {
  Write-Warning "[smoke] Failures detected: $($failures.Count)"
  $failures | Format-Table -AutoSize
}

($failures | ConvertTo-Json -Depth 6) | Out-File 'smoke_failures.json' -Encoding utf8
Write-Host '[smoke] Report written to smoke_failures.json'
