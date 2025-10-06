# Simple smoke tests for key API endpoints
$ErrorActionPreference = 'Stop'
$base = 'http://localhost:5125'

Write-Host "GET /api/systems" -ForegroundColor Cyan
$systems = Invoke-RestMethod -Uri "$base/api/systems" -UseBasicParsing
if (-not ($systems -is [System.Collections.IEnumerable])) { throw "systems is not a list" }

Write-Host "GET /api/systems/integration-summary" -ForegroundColor Cyan
$sum = Invoke-RestMethod -Uri "$base/api/systems/integration-summary" -UseBasicParsing
if ([int]$sum.total -ne $systems.Count) { throw "summary total mismatch" }
if ([int]$sum.with_api_base -ne [int]$sum.total) { throw "not at 100% readiness" }

# Quantum health checks
Write-Host "GET /qcae/health" -ForegroundColor Cyan
$qcae = Invoke-RestMethod -Uri "$base/qcae/health" -UseBasicParsing
if ($qcae.status -ne 'ok') { throw "qcae not ok" }

Write-Host "GET /qdc/health" -ForegroundColor Cyan
$qdc = Invoke-RestMethod -Uri "$base/qdc/health" -UseBasicParsing

Write-Host "GET /qcms/health" -ForegroundColor Cyan
$qcms = Invoke-RestMethod -Uri "$base/qcms/health" -UseBasicParsing

Write-Host "GET /qcc/health" -ForegroundColor Cyan
$qcc = Invoke-RestMethod -Uri "$base/qcc/health" -UseBasicParsing

# Orchestrate quantum (small shots)
Write-Host "POST /api/orchestrate/quantum" -ForegroundColor Cyan
$resp = Invoke-RestMethod -Method Post -Uri "$base/api/orchestrate/quantum" -Body (@{shots = 128 } | ConvertTo-Json) -ContentType 'application/json' -UseBasicParsing
if ($resp.status -ne 'ok') { throw "orchestrate/quantum failed" }
if (-not $resp.result.top_counts) { throw "no top_counts in result" }

Write-Host "OK" -ForegroundColor Green
