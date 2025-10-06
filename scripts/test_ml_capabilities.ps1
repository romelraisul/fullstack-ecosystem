<#!
.SYNOPSIS
  Launch backend (exe or module) and verify /health and /ml-capabilities endpoints.

.DESCRIPTION
  1. Chooses an execution target:
     - If -ExePath provided, uses that executable.
     - Else if dist/advanced_backend_full_onedir/advanced_backend_full_onedir.exe exists, uses it.
     - Else if dist/advanced_backend_lean.exe exists, uses that with MINIMAL_MODE=1.
     - Else falls back to `python -m uvicorn autogen.advanced_backend:app`.
  2. Waits for /health.
  3. Fetches /ml-capabilities (if present) and pretty prints JSON.
  4. Optionally writes raw JSON to an output file.

.PARAMETER Port
  Port to bind (default 8070).

.PARAMETER ExePath
  Explicit path to packaged executable.

.PARAMETER OutputJson
  Path to write the ml-capabilities JSON (optional).

.PARAMETER TimeoutSeconds
  Max seconds to wait for health (default 25).

.EXAMPLE
  ./scripts/test_ml_capabilities.ps1

.EXAMPLE
  ./scripts/test_ml_capabilities.ps1 -ExePath dist/advanced_backend_full_onedir/advanced_backend_full_onedir.exe -Port 9000

.EXAMPLE
  ./scripts/test_ml_capabilities.ps1 -OutputJson capabilities.json
#>
[CmdletBinding()] param(
    [int] $Port = 8070,
    [string] $ExePath,
    [string] $OutputJson,
    [int] $TimeoutSeconds = 25
)

$ErrorActionPreference = 'Stop'
function Info($m) { Write-Host "[TEST] $m" -ForegroundColor Cyan }
function Warn($m) { Write-Host "[TEST] WARN: $m" -ForegroundColor Yellow }
function Err($m) { Write-Host "[TEST] ERR: $m" -ForegroundColor Red }

$repoRoot = Split-Path -Parent $PSCommandPath | Split-Path -Parent
Set-Location $repoRoot

if (-not $ExePath) {
    $fullCandidate = Join-Path $repoRoot 'dist/advanced_backend_full_onedir/advanced_backend_full_onedir.exe'
    $leanCandidate = Join-Path $repoRoot 'dist/advanced_backend_lean.exe'
    if (Test-Path $fullCandidate) { $ExePath = $fullCandidate; Info "Auto-selected full onedir exe" }
    elseif (Test-Path $leanCandidate) { $ExePath = $leanCandidate; $env:MINIMAL_MODE = '1'; Info "Auto-selected lean exe (MINIMAL_MODE=1)" }
}

$usingExe = $true
if (-not $ExePath -or -not (Test-Path $ExePath)) {
    Warn 'No executable available; falling back to uvicorn module run'
    $usingExe = $false
}

$env:PORT = $Port.ToString()
$env:SAFE_MODE = $env:SAFE_MODE # preserve if user set
if ($usingExe) {
    Info "Starting executable: $ExePath on port $Port"
    Start-Process -FilePath $ExePath -WindowStyle Hidden
}
else {
    Info "Starting uvicorn (python module) on port $Port"
    Start-Process -FilePath python -ArgumentList '-m', 'uvicorn', 'autogen.advanced_backend:app', '--host', '127.0.0.1', '--port', "$Port", '--log-level', 'warning' -WindowStyle Hidden
}

$healthUrl = "http://127.0.0.1:$Port/health"
$capUrl = "http://127.0.0.1:$Port/ml-capabilities"
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$healthy = $false

while ((Get-Date) -lt $deadline) {
    try {
        $r = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2 -UseBasicParsing
        if ($r.status -eq 'ok') { $healthy = $true; break }
    }
    catch { }
    Start-Sleep -Milliseconds 400
}

if (-not $healthy) { Err "Health endpoint did not become ready within $TimeoutSeconds s"; exit 2 }
Info 'Health OK'

try {
    $cap = Invoke-RestMethod -Uri $capUrl -TimeoutSec 3 -UseBasicParsing
    Info '/ml-capabilities response:'
    $json = $cap | ConvertTo-Json -Depth 10
    Write-Host $json
    if ($OutputJson) {
        $json | Out-File -FilePath $OutputJson -Encoding utf8
        Info "Wrote JSON to $OutputJson"
    }
}
catch {
    Warn "Failed to retrieve /ml-capabilities (endpoint may not exist in lean build). $_"
}

Info 'Done.'
