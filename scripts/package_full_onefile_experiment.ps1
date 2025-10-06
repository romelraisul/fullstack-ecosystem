<#!
.SYNOPSIS
  Experimental attempt to bundle full ML stack into a single-file executable.
.DESCRIPTION
  This script tries a PyInstaller --onefile build including heavy ML / LLM related libraries.
  Because of size, startup extraction latency, and potential missing dynamic libraries, the
  resulting executable may be unstable. Use for research only.
.OUTPUTS
  Produces dist/advanced_backend_full_onefile_experiment.exe (if successful) and a log file.
#>

param(
  [switch]$IncludeTensorflow,
  [string]$Name = 'advanced_backend_full_onefile_experiment'
)

$ErrorActionPreference = 'Stop'
$log = "experiment_onefile_full_ml.log"

Write-Host '[onefile-experiment] Starting full ML onefile build...' -ForegroundColor Cyan

# Base install (assumes venv active or global managed carefully)
$packages = @('fastapi','uvicorn','pyinstaller','tdigest','prometheus-client','passlib','bcrypt','python-magic-bin','torch','scikit-learn','langchain','openai','anthropic')
if ($IncludeTensorflow) { $packages += 'tensorflow' }

pip install --upgrade pip | Out-Null
pip install $packages | Tee-Object -FilePath $log

# Build command
$cmd = @(
  'pyinstaller',
  '--name', $Name,
  '--onefile', 'autogen/advanced_backend.py',
  '--hidden-import','tdigest',
  '--hidden-import','accumulation_tree',
  '--hidden-import','prometheus_client',
  '--hidden-import','passlib',
  '--hidden-import','bcrypt'
)

if ($IncludeTensorflow) { $env:INCLUDE_TENSORFLOW='1' }

Write-Host "[onefile-experiment] Running: $($cmd -join ' ')" -ForegroundColor Yellow
& $cmd 2>&1 | Tee-Object -FilePath $log -Append

if (Test-Path "dist/$Name.exe") {
  $sizeMB = [math]::Round((Get-Item "dist/$Name.exe").Length / 1MB,2)
  Write-Host "[onefile-experiment] Success: dist/$Name.exe ($sizeMB MB)" -ForegroundColor Green
  Write-Host '[onefile-experiment] Probing runtime health...' -ForegroundColor Cyan
  Start-Process -FilePath "dist/$Name.exe" -PassThru | ForEach-Object { $procId=$_.Id; Start-Sleep 5; }
  try {
    $h = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 5 -UseBasicParsing
    Write-Host "Health status: $($h.status)" -ForegroundColor Green
  try { Invoke-RestMethod -Uri 'http://127.0.0.1:8000/ml-capabilities' -TimeoutSec 5 -UseBasicParsing | Out-Null; Write-Host 'Capabilities loaded.' }
    catch { Write-Warning 'Capabilities endpoint failed (expected in some failure modes).' }
  } catch { Write-Warning "Health probe failed: $($_.Exception.Message)" }
  Get-Process | Where-Object { $_.Path -like "*${Name}.exe" } | Stop-Process -Force -ErrorAction SilentlyContinue
} else {
  Write-Warning '[onefile-experiment] Build failed or executable missing.'
}

Write-Host "[onefile-experiment] Log written to $log" -ForegroundColor Cyan
