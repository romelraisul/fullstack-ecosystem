<#!
.SYNOPSIS
  Build a lean (no heavy ML/LLM) onefile PyInstaller executable.

.DESCRIPTION
  Creates venv_lean (if absent), installs only core/light dependencies, and builds a
  single-file executable excluding large frameworks (torch, tensorflow, sklearn,
  langchain, openai, anthropic, transformers, tiktoken).

.PARAMETER Clean
  Remove previous lean artifacts before building.

.PARAMETER Name
  Executable name (default: advanced_backend_lean)

.PARAMETER Python
  Python interpreter path (defaults to existing venv_lean or current python).

.EXAMPLE
  ./scripts/package_lean.ps1 -Clean
#>
[CmdletBinding()] param(
    [switch] $Clean,
    [string] $Name = 'advanced_backend_lean',
    [string] $Python
)

$ErrorActionPreference = 'Stop'
function Info($m) { Write-Host "[LEAN] $m" -ForegroundColor Cyan }
function Warn($m) { Write-Host "[LEAN] WARN: $m" -ForegroundColor Yellow }
function Err($m) { Write-Host "[LEAN] ERR: $m" -ForegroundColor Red }

$repoRoot = Split-Path -Parent $PSCommandPath | Split-Path -Parent
Set-Location $repoRoot

if (-not $Python) {
    if (Test-Path "$repoRoot/venv_lean/Scripts/python.exe") { $Python = "$repoRoot/venv_lean/Scripts/python.exe" }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $Python = (Get-Command python).Source }
    else { throw 'Python interpreter not found.' }
}

if (-not (Test-Path "$repoRoot/venv_lean")) {
    Info 'Creating venv_lean virtual environment'
    & $Python -m venv venv_lean
    $Python = "$repoRoot/venv_lean/Scripts/python.exe"
}

Info 'Upgrading pip'
& $Python -m pip install --upgrade pip > $null

$core = @('fastapi', 'uvicorn', 'pydantic', 'python-multipart', 'tdigest', 'prometheus_client', 'passlib', 'bcrypt', 'python-magic-bin')
Info 'Installing lean dependencies'
& $Python -m pip install --quiet --upgrade @core pyinstaller | Out-Null

if ($Clean) {
    Info 'Cleaning dist/build/spec artifacts'
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue dist, build, "$Name.spec"
}

$exclude = @('torch', 'tensorflow', 'sklearn', 'langchain', 'openai', 'anthropic', 'transformers', 'tiktoken')
$excludeArgs = $exclude | ForEach-Object { "--exclude-module $_" }

$hidden = @('tdigest', 'accumulation_tree', 'prometheus_client', 'passlib', 'bcrypt', 'magic')
$hiddenArgs = $hidden | ForEach-Object { "--hidden-import $_" }

Info 'Building lean onefile executable'
$cmd = @('pyinstaller', '--onefile', 'bootstrap_entry.py', '--name', $Name, '--add-data', 'executive_dashboard.html;.') + $hiddenArgs + $excludeArgs
Write-Host "[CMD] $($cmd -join ' ')" -ForegroundColor DarkGray
& $Python $cmd

if ($LASTEXITCODE -ne 0) { Err "PyInstaller failed: $LASTEXITCODE"; exit $LASTEXITCODE }

$exe = Join-Path "$repoRoot/dist" ("$Name.exe")
if (-not (Test-Path $exe)) { $exe = "$repoRoot/dist/$Name.exe" }
if (Test-Path $exe) {
    $sizeMB = [Math]::Round((Get-Item $exe).Length / 1MB, 2)
    Info "Lean build complete: $exe (${sizeMB}MB)"
    Info 'Run example:'
    Write-Host "  $env:MINIMAL_MODE=1; $exe" -ForegroundColor Green
    Write-Host 'Health:' -ForegroundColor Green
    Write-Host '  curl http://localhost:8000/health' -ForegroundColor Green
}
else {
    Warn 'Executable not found.'
}
